import os
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from src.config.config import settings

# Determine DB connection details - fallback to sqlite for local dev/testing
DATABASE_URL = settings.DATABASE_URL or "sqlite:///ecosaur_sqlite.db"

# Create database engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
    
    # Enable WAL mode and enforce foreign keys on SQLite connection
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()
else:
    # Postgres configuration (e.g. Supabase DB connection)
    # Fix postgresql:// prefix issues
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    FastAPI Dependency yielding SQLAlchemy sessions.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
