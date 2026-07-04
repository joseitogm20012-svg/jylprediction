import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, scoped_session


class Base(DeclarativeBase):
    pass


SQLITE_PATH = Path(__file__).parent.parent / "scrapycoco.db"


def get_database_url() -> str:
    pg_url = os.environ.get("DATABASE_URL", "")
    if pg_url:
        return pg_url
    return f"sqlite:///{SQLITE_PATH}"


engine = create_engine(
    get_database_url(),
    echo=os.environ.get("SQL_ECHO", "0") == "1",
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if "sqlite" in get_database_url() else {},
)

if "sqlite" in get_database_url():

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)


def get_db():
    db = db_session()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
