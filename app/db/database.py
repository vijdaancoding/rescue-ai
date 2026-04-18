"""
SQLAlchemy engine + session factory.

Supabase's pooler aggressively closes idle connections. `pool_pre_ping` checks
liveness before reuse (avoiding StaleConnection errors on the first query of
an otherwise-idle app) and `pool_recycle` proactively drops connections older
than 30 min before Postgres does. Pool sizes are tuned for a small Railway
worker — a larger deployment should raise them.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine = create_engine(
    settings.DATABASE_URL,
    **({} if _is_sqlite else {
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }),
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
