"""农药库查询工具"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def load_pesticide_db() -> list[dict]:
    with open(DATA_DIR / "pesticide_db.json", encoding="utf-8") as f:
        return json.load(f)["pesticides"]


def load_banned_list() -> list[str]:
    with open(DATA_DIR / "banned_pesticides.json", encoding="utf-8") as f:
        return json.load(f)["banned_for_tea"]


def load_mrl_database() -> dict:
    with open(DATA_DIR / "mrl_database.json", encoding="utf-8") as f:
        return json.load(f)


def query_candidates(disease: str, organic_only: bool = False) -> list[dict]:
    """根据病害查询候选农药"""
    db = load_pesticide_db()
    results = [p for p in db if disease in p.get("target_diseases", [])]
    if organic_only:
        results = [p for p in results if p.get("organic_certified", False)]
    return results
