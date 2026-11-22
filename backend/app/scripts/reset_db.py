from pathlib import Path
from app.core.config import settings
from app.scripts.seed import seed
path=Path("data/app.db")
if path.exists(): path.unlink()
seed(True)

