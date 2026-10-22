from supportiq.db.session import engine
from supportiq.models.base import Base
from supportiq.models.ticket import Ticket  # noqa: F401


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully.")