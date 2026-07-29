from sqlalchemy import text
from langchain.tools import tool, ToolRuntime
from app.ai.agent.context import ExpenseAgentContext, ALLOWED_TABLES


@tool
def get_sample_data(
    table_name: str,
    runtime: ToolRuntime[ExpenseAgentContext],
    limit: int = 3,
) -> list[dict]:
    """
    Return a few sample rows from an allowed expense table.

    Use this only when you need to understand how values
    are represented in the database.

    Do not call this tool if the schema already provides
    enough information.
    """

    if table_name not in ALLOWED_TABLES:
        return [{"error": f"Table '{table_name}' is not available."}]

    limit = max(
        1,
        min(limit, 5),
    )

    db = runtime.context.db
    user_id = runtime.context.user_id

    if table_name == "receipts":

        query = text("""
            SELECT *
            FROM receipts
            WHERE user_id = :user_id
            LIMIT :limit
        """)

        rows = (
            db.execute(
                query,
                {
                    "user_id": user_id,
                    "limit": limit,
                },
            )
            .mappings()
            .all()
        )

    elif table_name == "receipt_items":

        query = text("""
            SELECT ri.*
            FROM receipt_items ri
            JOIN receipts r
                ON r.id = ri.receipt_id
            WHERE r.user_id = :user_id
            LIMIT :limit
        """)

        rows = (
            db.execute(
                query,
                {
                    "user_id": user_id,
                    "limit": limit,
                },
            )
            .mappings()
            .all()
        )

    else:
        return []

    return [dict(row) for row in rows]
