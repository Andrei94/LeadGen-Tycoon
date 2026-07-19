"""SQLite persistence for local-first play."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from .state import normalize_state

APP_DIR = Path(__file__).resolve().parents[1]
SAVE_DIR = APP_DIR / "saves"
DB_PATH = SAVE_DIR / "leadgen_tycoon.sqlite"
JSON_FALLBACK_PATH = SAVE_DIR / "leadgen_tycoon_fallback.json"


def init_db():
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS saves (
                slot TEXT PRIMARY KEY,
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _load_json_fallback():
    if not JSON_FALLBACK_PATH.exists():
        return {}
    return json.loads(JSON_FALLBACK_PATH.read_text(encoding="utf-8"))


def _save_json_fallback(payload):
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    JSON_FALLBACK_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def save_game(state, slot="default"):
    state["updated_at"] = datetime.utcnow().isoformat(timespec="seconds")
    payload = json.dumps(state, indent=2, sort_keys=True)
    try:
        init_db()
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO saves(slot, state_json, updated_at) VALUES(?, ?, ?) "
                "ON CONFLICT(slot) DO UPDATE SET state_json=excluded.state_json, updated_at=excluded.updated_at",
                (slot, payload, state["updated_at"]),
            )
            conn.commit()
    except (OSError, sqlite3.Error):
        fallback = _load_json_fallback()
        fallback[slot] = {"state_json": payload, "updated_at": state["updated_at"]}
        _save_json_fallback(fallback)


def load_game(slot="default"):
    try:
        init_db()
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute("SELECT state_json FROM saves WHERE slot = ?", (slot,)).fetchone()
        if not row:
            return None
        return normalize_state(json.loads(row[0]))
    except (OSError, sqlite3.Error):
        fallback = _load_json_fallback()
        if slot not in fallback:
            return None
        return normalize_state(json.loads(fallback[slot]["state_json"]))


def delete_save(slot="default"):
    try:
        init_db()
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM saves WHERE slot = ?", (slot,))
            conn.commit()
    except (OSError, sqlite3.Error):
        fallback = _load_json_fallback()
        fallback.pop(slot, None)
        _save_json_fallback(fallback)


def list_saves():
    try:
        init_db()
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute("SELECT slot, updated_at FROM saves ORDER BY updated_at DESC").fetchall()
        return [{"slot": row[0], "updated_at": row[1]} for row in rows]
    except (OSError, sqlite3.Error):
        fallback = _load_json_fallback()
        return [
            {"slot": slot, "updated_at": value.get("updated_at", "")}
            for slot, value in sorted(fallback.items(), key=lambda item: item[1].get("updated_at", ""), reverse=True)
        ]
