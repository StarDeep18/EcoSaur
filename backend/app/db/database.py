import os
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Database path - default to a local sqlite file ecosaur_sqlite.db
DB_PATH = "ecosaur_sqlite.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# Enable WAL mode and enforce foreign keys on connection
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    FastAPI Dependency that yields a new SQLAlchemy database session and
    ensures it gets closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
