from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Enterprise production connection pooling configuration
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Automatically checks and discards stale/dropped connections
    pool_size=20,        # Base connection pool size
    max_overflow=10,     # Max temporary bursting connections under load
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency injection provider yielding a transactional database 
    session context per-request, ensuring complete safe teardown cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()