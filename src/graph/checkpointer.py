import os

from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured.")


# SQLAlchemy commonly accepts:
# postgresql+psycopg://...
#
# PostgresSaver uses psycopg directly, so remove the SQLAlchemy driver suffix.
CHECKPOINT_DATABASE_URL = DATABASE_URL.replace(
    "postgresql+psycopg://",
    "postgresql://",
)


checkpointer_context = PostgresSaver.from_conn_string(
    CHECKPOINT_DATABASE_URL
)

checkpointer = checkpointer_context.__enter__()