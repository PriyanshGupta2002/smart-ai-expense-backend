from langgraph.checkpoint.postgres import PostgresSaver
from app.core.config import settings

CHECKPOINT_DATABASE_URL = settings.CHECKPOINTER_DATABASE_URL


def get_checkpointer():
    if not CHECKPOINT_DATABASE_URL:
        raise RuntimeError("CHECKPOINT_DATABASE_URL is not configured")

    return PostgresSaver.from_conn_string(CHECKPOINT_DATABASE_URL)
