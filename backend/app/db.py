from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .core.config import settings

if settings.database_url.startswith("sqlite"):
    Path("data").mkdir(exist_ok=True)
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {})
@event.listens_for(engine, "connect")
def sqlite_pragmas(dbapi_connection, _):
    cur = dbapi_connection.cursor(); cur.execute("PRAGMA foreign_keys=ON"); cur.execute("PRAGMA journal_mode=WAL"); cur.execute("PRAGMA busy_timeout=5000"); cur.close()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
class Base(DeclarativeBase): pass
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

