import os
import sqlite3
import threading

DB_FILE = os.getenv("SMARTFARM_DB", "smarfa.db")

_local = threading.local()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS crop_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    height_cm REAL NOT NULL,
    soil_moisture REAL NOT NULL,
    temperature_c REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS intrusion_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    motion_detected INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_id TEXT NOT NULL,
    type TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS water_pump_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    trigger_type TEXT NOT NULL,
    reason TEXT NOT NULL,
    moisture_before REAL,
    duration_seconds INTEGER NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scan_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    crop_detected TEXT NOT NULL,
    severity TEXT NOT NULL,
    ai_confidence REAL NOT NULL,
    health_assessment TEXT NOT NULL,
    model_used TEXT
);
"""


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_FILE)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
    return _local.conn


def init_db():
    conn = _get_conn()
    conn.executescript(_SCHEMA)
    conn.commit()


def get_db() -> sqlite3.Connection:
    return _get_conn()
