import sqlglot
from sqlglot import exp

from langchain.tools import tool
from langgraph.prebuilt import ToolRuntime
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.ai.agent.context import ALLOWED_TABLES, ExpenseAgentContext

MAX_ROWS = 10

# sqlglot has no first-class notion of postgres/SQLAlchemy-style ":name"
# bind params — it can silently rewrite them when reserializing the AST
# back to SQL (we've seen it turn ":user_id" into both "@user_id" and
# "%(user_id)s" depending on surrounding tokens). We protect it before
# parsing with a plain identifier that survives untouched, then restore
# it after, so we never depend on sqlglot's round-trip behavior for the
# one token that matters most for row-level security.
_USER_ID_PLACEHOLDER = "__user_id_param__"


def validate_and_prepare_sql(query: str) -> str:
    protected_query = query.replace(":user_id", _USER_ID_PLACEHOLDER)

    try:
        statements = sqlglot.parse(protected_query, read="postgres")
    except Exception as exc:
        raise ValueError("Invalid SQL query.") from exc

    if len(statements) != 1 or statements[0] is None:
        raise ValueError("Only one SQL statement is allowed.")

    statement = statements[0]

    if statement.key.lower() != "select":
        raise ValueError("Only SELECT queries are allowed.")

    # Exclude CTE aliases from the table check — they aren't real tables.
    cte_names = {cte.alias_or_name for cte in statement.find_all(exp.CTE)}
    tables = {t.name for t in statement.find_all(exp.Table) if t.name not in cte_names}

    unauthorized = tables - ALLOWED_TABLES
    if unauthorized:
        raise ValueError(
            f"Query references unauthorized tables: {', '.join(unauthorized)}"
        )

    # Enforce that any allowed table actually referenced is scoped by user_id.
    # Cheap heuristic: the protected user_id placeholder must appear somewhere
    # in a WHERE/ON/HAVING predicate. This is not airtight (see note below),
    # but it stops the common failure mode of the model just forgetting it.
    where_clauses = [
        w.sql(dialect="postgres")
        for w in statement.find_all((exp.Where, exp.Join, exp.Having))
    ]
    if tables & ALLOWED_TABLES and not any(
        "user_id" in clause and _USER_ID_PLACEHOLDER in clause
        for clause in where_clauses
    ):
        raise ValueError(
            "Query must filter user-owned tables using "
            "WHERE user_id = :user_id "
            "(or an equivalent JOIN/HAVING predicate)."
        )

    # Enforce a row cap at the SQL level, not just client-side.
    if not statement.args.get("limit"):
        statement = statement.limit(MAX_ROWS)
    else:
        existing_limit = statement.args["limit"].expression
        if int(existing_limit.name) > MAX_ROWS:
            statement.set("limit", exp.Limit(expression=exp.Literal.number(MAX_ROWS)))

    safe_query = statement.sql(dialect="postgres")
    safe_query = safe_query.replace(_USER_ID_PLACEHOLDER, ":user_id")
    return safe_query


@tool
def execute_sql(query: str, runtime: ToolRuntime[ExpenseAgentContext]) -> dict:
    """
    Execute a read-only PostgreSQL SELECT query against the
    CURRENT AUTHENTICATED USER'S expense data.

    IMPORTANT:
    The SQL query MUST contain the literal parameter
    ':user_id' and use it to restrict user-owned data.

    ALWAYS include:

        WHERE user_id = :user_id

    when querying receipts or budgets.

    For receipt_items, scope through the receipt:

        WHERE r.user_id = :user_id

    Example:

        SELECT COALESCE(SUM(total), 0) AS total_spent
        FROM receipts
        WHERE user_id = :user_id
        AND purchase_datetime >= date_trunc('month', CURRENT_DATE);

    The application automatically supplies the actual user_id
    parameter. NEVER put an actual UUID into the SQL.

    Allowed tables:
    - receipts
    - receipt_items
    - budgets

    Only SELECT queries are allowed.
    """
    try:
        safe_query = validate_and_prepare_sql(query)

        result = runtime.context.db.execute(
            text(safe_query),
            {"user_id": runtime.context.user_id},
        )
        rows = result.mappings().fetchmany(MAX_ROWS)

        return {
            "success": True,
            "columns": list(result.keys()),
            "rows": [dict(row) for row in rows],
            "row_count": len(rows),
        }

    except ValueError as exc:
        return {
            "success": False,
            "error": str(exc),
            "instruction": "Fix the query per the error above and retry.",
        }

    except SQLAlchemyError as exc:
        runtime.context.db.rollback()
        return {
            "success": False,
            "error": str(exc),
            "instruction": "The query failed. Review the schema and generate a corrected query.",
        }
