import json
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "db.json"


class StorageError(Exception):
    pass


def _load_db() -> Dict[str, Any]:
    if not DB_PATH.exists():
        raise StorageError(f"db.json not found at {DB_PATH}")
    with DB_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_db(db: Dict[str, Any]) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DB_PATH.open("w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def get_courses() -> List[Dict[str, Any]]:
    return _load_db().get("courses", [])


def get_slots() -> List[Dict[str, Any]]:
    return _load_db().get("slots", [])


def get_requests() -> List[Dict[str, Any]]:
    return _load_db().get("requests", [])


def find_course_by_key(course_key: str) -> Optional[Dict[str, Any]]:
    for c in get_courses():
        if c.get("course_key") == course_key:
            return c
    return None


def find_slot_by_id(slot_id: str) -> Optional[Dict[str, Any]]:
    for s in get_slots():
        if s.get("slot_id") == slot_id:
            return s
    return None


def append_request(record: Dict[str, Any]) -> None:
    db = _load_db()
    requests: List[Dict[str, Any]] = db.setdefault("requests", [])
    requests.append(record)
    _save_db(db)


