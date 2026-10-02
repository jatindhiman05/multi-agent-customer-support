from langgraph.checkpoint.postgres import PostgresSaver

from src.core.config import DATABASE_URL


# SQLAlchemy accepts:
# postgresql+psycopg://...
#
# PostgresSaver uses psycopg directly, so remove
# SQLAlchemy's driver suffix.
CHECKPOINT_DATABASE_URL = DATABASE_URL.replace(
    "postgresql+psycopg://",
    "postgresql://",
)


checkpointer_context = (
    PostgresSaver.from_conn_string(
        CHECKPOINT_DATABASE_URL
    )
)

checkpointer = (
    checkpointer_context.__enter__()
)