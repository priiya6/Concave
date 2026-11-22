import sys
from pathlib import Path
from alembic import context
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db import Base, engine
from app import models

target_metadata=Base.metadata

def run_migrations_online():
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    context.configure(url=str(engine.url), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction(): context.run_migrations()
else:
    run_migrations_online()
