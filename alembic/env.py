from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.db.base import Base
import src.db.models  # noqa: F401


# Alembic Config object.
config = context.config


# Configure Python logging from alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Tell Alembic about our SQLAlchemy metadata.
target_metadata = Base.metadata


# =============================================================================
# EXTERNAL TABLES
# =============================================================================

# These tables are owned and managed by LangGraph's PostgresSaver.
# Alembic must not create, modify, or delete them.
LANGGRAPH_TABLES = {
    "checkpoints",
    "checkpoint_blobs",
    "checkpoint_writes",
    "checkpoint_migrations",
}


def include_object(
    object,
    name,
    type_,
    reflected,
    compare_to,
):
    """
    Prevent Alembic autogenerate from managing LangGraph-owned tables.
    """

    if (
        type_ == "table"
        and reflected
        and name in LANGGRAPH_TABLES
    ):
        return False

    return True


def run_migrations_offline() -> None:
    """
    Run migrations without creating a live database connection.
    """

    from src.db.connection import DATABASE_URL

    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations using a live database connection.
    """

    from src.db.connection import DATABASE_URL

    configuration = config.get_section(
        config.config_ini_section
    ) or {}

    configuration["sqlalchemy.url"] = DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()