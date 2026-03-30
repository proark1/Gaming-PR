from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

connect_args = {}
engine_kwargs = {}

if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    # Use NullPool to avoid thread-safety issues with SQLite
    from sqlalchemy.pool import StaticPool
    engine_kwargs = {"poolclass": StaticPool}
else:
    # PostgreSQL: enable connection pooling
    engine_kwargs = {
        "pool_size": 20,       # was 10 — supports SCRAPE_CONCURRENCY=10 × 3 inner workers
        "max_overflow": 30,    # was 20 — headroom for translation threads + API requests
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": {
            "connect_timeout": 10,              # fail fast if DB unreachable
            "options": "-c lock_timeout=5s",    # don't block forever waiting for table locks
        },
    }

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs,
)

# Enable WAL mode for SQLite to allow concurrent reads during writes
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
