from sqlalchemy import text

from src.db.session import SessionLocal


def main() -> None:
    with SessionLocal() as session:
        result = session.execute(
            text(
                """
                SELECT
                    current_user,
                    current_database()
                """
            )
        )

        row = result.one()

        print("Database session successful.")
        print(f"User: {row[0]}")
        print(f"Database: {row[1]}")


if __name__ == "__main__":
    main()