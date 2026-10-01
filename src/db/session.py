from sqlalchemy.orm import Session, sessionmaker

from src.db.connection import engine


SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)