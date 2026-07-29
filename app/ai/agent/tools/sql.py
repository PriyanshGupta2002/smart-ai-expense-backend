import sqlglot

from langchain.tools import tool
from langgraph.prebuilt import ToolRuntime
from sqlalchemy import text

from sqlalchemy.exc import SQLAlchemyError
from app.ai.agent.context import ALLOWED_TABLES, ExpenseAgentContext


def validate_sql(query: str) -> None:

    try:
        statements = sqlglot.parse(
            query,
            read="postgres",
        )
    except Exception as exc:
        raise ValueError("Invalid SQL query.") from exc

    if len(statements) != 1:
        raise ValueError("Only one SQL statement is allowed.")

    statement = statements[0]

    if statement.key.lower() not in {
        "select",
    }:
        raise ValueError("Only SELECT queries are allowed.")

    tables = {table.name for table in statement.find_all(sqlglot.exp.Table)}

    unauthorized = tables - ALLOWED_TABLES

    if unauthorized:
        raise ValueError(
            "Query references tables that are " "not available to the expense agent."
        )


@tool
def execute_sql(
    query: str,
    runtime: ToolRuntime[ExpenseAgentContext],
) -> dict:
    """
    Execute a read-only PostgreSQL query against the
    authenticated user's expense data.
    """

    try:
        validate_sql(query)

        result = runtime.context.db.execute(text(query))

        rows = result.mappings().fetchmany(100)

        return {
            "columns": list(result.keys()),
            "rows": [dict(row) for row in rows],
            "row_count": len(rows),
        }

    except SQLAlchemyError as exc:

        # Roll back failed transaction
        runtime.context.db.rollback()

        return {
            "success": False,
            "error": str(exc),
            "instruction": (
                "The query failed. Review the schema " "and generate a corrected query."
            ),
        }
