from sqlalchemy import select

from src.db.models import User
from src.db.session import SessionLocal


def main() -> None:
    with SessionLocal() as session:
        statement = select(User)

        users = session.scalars(statement).all()

        print(f"Users found: {len(users)}")

        for user in users:
            print(
                f"{user.id} | "
                f"{user.email} | "
                f"{user.role} | "
                f"{user.status}"
            )


if __name__ == "__main__":
    main()