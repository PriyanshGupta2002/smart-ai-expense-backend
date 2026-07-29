from langchain.tools import tool
from app.ai.agent.context import ALLOWED_TABLES


@tool
def list_tables() -> list[str]:
    """
    List the database tables available for expense analysis.

    Use this when you need to discover which tables are
    available before querying the database.
    """

    return sorted(ALLOWED_TABLES)
