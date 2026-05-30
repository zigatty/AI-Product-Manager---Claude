import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ai_pm.db")
SYNC_URL = _url.replace("sqlite+aiosqlite", "sqlite").replace("postgresql+asyncpg://", "postgresql://")

engine = create_engine(SYNC_URL, connect_args={"check_same_thread": False} if "sqlite" in SYNC_URL else {})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
