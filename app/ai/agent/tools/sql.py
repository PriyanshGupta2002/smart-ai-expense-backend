import sqlglot
from sqlglot import exp

from langchain.tools import tool
from langgraph.prebuilt import ToolRuntime
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.ai.agent.context import ALLOWED_TABLES, ExpenseAgentContext

MAX_ROWS = 10


def validate_and_prepare_sql(query: str) -> str:
    try:
        statements = sqlglot.parse(query, read="postgres")
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
    # Cheap heuristic: the literal parameter ':user_id' must appear somewhere
    # in a WHERE/ON/HAVING predicate. This is not airtight (see note below),
    # but it stops the common failure mode of the model just forgetting it.
    where_clauses = [
        w.sql(dialect="postgres")
        for w in statement.find_all((exp.Where, exp.Join, exp.Having))
    ]
    if tables & ALLOWED_TABLES and not any(
        "user_id" in clause and ":user_id" in clause for clause in where_clauses
    ):
        raise ValueError(
            "Query must filter user-owned tables using WHERE user_id = :user_id "
            "(or an equivalent JOIN/HAVING predicate)."
        )

    # Enforce a row cap at the SQL level, not just client-side.
    if not statement.args.get("limit"):
        statement = statement.limit(MAX_ROWS)
    else:
        existing_limit = statement.args["limit"].expression
        if int(existing_limit.name) > MAX_ROWS:
            statement.set("limit", exp.Limit(expression=exp.Literal.number(MAX_ROWS)))

    return statement.sql(dialect="postgres")


@tool
def execute_sql(query: str, runtime: ToolRuntime[ExpenseAgentContext]) -> dict:
    """
    Execute a read-only PostgreSQL query against the
    authenticated user's expense data.

    The SQL generated MUST filter every user-owned table
    (receipts, budgets, receipt_items) using ':user_id',
    e.g. WHERE user_id = :user_id.
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
