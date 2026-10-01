from pathlib import Path
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine


PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not configured. "
        "Create a .env file based on .env.example."
    )


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)