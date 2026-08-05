from sqlalchemy import text
from langchain.tools import tool, ToolRuntime

from app.ai.agent.context import (
    ALLOWED_TABLES,
    ExpenseAgentContext,
)

TABLE_USER_FILTERS = {
    "receipts": "user_id = :user_id",
    "budgets": "user_id = :user_id",
    "receipt_items": """
        receipt_id IN (
            SELECT id
            FROM receipts
            WHERE user_id = :user_id
        )
    """,
}


@tool
def get_sample_data(
    table_name: str,
    runtime: ToolRuntime[ExpenseAgentContext],
    limit: int = 3,
) -> list[dict]:
    """
    Return a few sample rows from an allowed table.
    """

    if table_name not in ALLOWED_TABLES:
        return [{"error": f"Table '{table_name}' is not available."}]

    where_clause = TABLE_USER_FILTERS.get(table_name)

    if where_clause is None:
        return [{"error": f"No access rule configured for '{table_name}'."}]

    limit = max(1, min(limit, 5))

    query = text(f"""
        SELECT *
        FROM {table_name}
        WHERE {where_clause}
        LIMIT :limit
        """)

    rows = (
        runtime.context.db.execute(
            query,
            {
                "user_id": runtime.context.user_id,
                "limit": limit,
            },
        )
        .mappings()
        .all()
    )

    return [dict(row) for row in rows]
