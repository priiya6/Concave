import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db import Base, engine
from app import models
target_metadata=Base.metadata
def run_migrations_online(): Base.metadata.create_all(engine)
run_migrations_online()
