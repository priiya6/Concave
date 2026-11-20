from app.db import Base, engine
from app import models
target_metadata=Base.metadata
def run_migrations_online(): Base.metadata.create_all(engine)
run_migrations_online()

