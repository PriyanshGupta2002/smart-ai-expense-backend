import json

from langchain.tools import tool
from langgraph.prebuilt import ToolRuntime
from sqlalchemy import inspect

from app.ai.agent.context import (
    ExpenseAgentContext,
    ALLOWED_TABLES,
)
from app.core.redis import redis_client

SCHEMA_CACHE_PREFIX = "expense-agent:schema"
SCHEMA_CACHE_TTL = 60 * 60 * 24 * 7


def _schema_cache_key(table_name: str) -> str:
    return f"{SCHEMA_CACHE_PREFIX}:{table_name}"


@tool
def get_table_schema(
    table_name: str,
    runtime: ToolRuntime[ExpenseAgentContext],
) -> dict:
    """
    Get the schema of an allowed expense-related database table.

    Returns column names, data types, nullable information,
    primary keys, and foreign keys.

    Call this before writing SQL when you are unsure about
    the structure of a table.
    """

    # --------------------------------
    # 1. Validate table
    # --------------------------------

    if table_name not in ALLOWED_TABLES:
        return {"error": f"Table '{table_name}' is not available."}

    cache_key = _schema_cache_key(table_name)

    # --------------------------------
    # 2. Check Redis
    # --------------------------------

    cached_schema = redis_client.get(cache_key)

    if cached_schema:
        return json.loads(cached_schema)

    # --------------------------------
    # 3. Inspect DB
    # --------------------------------

    inspector = inspect(runtime.context.db.get_bind())

    columns = inspector.get_columns(table_name)

    primary_key = inspector.get_pk_constraint(table_name)

    foreign_keys = inspector.get_foreign_keys(table_name)

    # --------------------------------
    # 4. Build schema
    # --------------------------------

    schema = {
        "table": table_name,
        "columns": [
            {
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column["nullable"],
            }
            for column in columns
        ],
        "primary_key": primary_key.get(
            "constrained_columns",
            [],
        ),
        "foreign_keys": [
            {
                "columns": fk["constrained_columns"],
                "referenced_table": fk["referred_table"],
                "referenced_columns": fk["referred_columns"],
            }
            for fk in foreign_keys
        ],
    }

    # --------------------------------
    # 5. Cache
    # --------------------------------

    redis_client.setex(
        cache_key,
        SCHEMA_CACHE_TTL,
        json.dumps(schema),
    )

    return schema
