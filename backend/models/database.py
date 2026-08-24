import logging

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import settings

logger = logging.getLogger(__name__)


def build_engine(database_url: str):
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            pool_pre_ping=True,
            echo=False,
            connect_args={"check_same_thread": False},
        )

    try:
        engine = create_engine(database_url, pool_pre_ping=True, echo=False)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Connected to configured database.")
        return engine
    except Exception as exc:
        fallback_url = "sqlite:///./smt_local.db"
        logger.warning(
            "Database connection failed for %s: %s. Falling back to SQLite at %s.",
            database_url,
            exc,
            fallback_url,
        )
        settings.DATABASE_URL = fallback_url
        return create_engine(
            fallback_url,
            pool_pre_ping=True,
            echo=False,
            connect_args={"check_same_thread": False},
        )


engine = build_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
