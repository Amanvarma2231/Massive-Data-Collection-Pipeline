import json
from pathlib import Path
from typing import Dict, Any
from ..config import settings

def load_canonical_seed_db() -> Dict[str, Any]:
    seed_file = settings.SEED_DIR / "canonical_entities.json"
    if seed_file.exists():
        with open(seed_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}
