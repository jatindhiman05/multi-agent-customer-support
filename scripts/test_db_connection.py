from sqlalchemy import text

from src.db.connection import engine


def main() -> None:
    with engine.connect() as connection:
        result = connection.execute(
            text(
                """
                SELECT
                    current_user,
                    current_database(),
                    version()
                """
            )
        )

        row = result.one()

        print("Database connection successful.")
        print(f"User: {row[0]}")
        print(f"Database: {row[1]}")
        print(f"PostgreSQL: {row[2]}")


if __name__ == "__main__":
    main()