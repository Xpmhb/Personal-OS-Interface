"""
Database config — PostgreSQL for production, SQLite for local testing
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Check for Render's DATABASE_URL or local PostgreSQL
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")

if DATABASE_URL:
    # Production: Use PostgreSQL from environment
    engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
else:
    # Local testing: Use SQLite
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test.db")
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
