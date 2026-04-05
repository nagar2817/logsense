from pathlib import Path
import sqlite3

from app.core.config import Settings


def get_connection(*, settings: Settings) -> sqlite3.Connection:
    Path(settings.sqlite_database_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.sqlite_database_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(*, settings: Settings) -> None:
    with get_connection(settings=settings) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id TEXT PRIMARY KEY,
                service TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                fingerprint TEXT NOT NULL,
                title TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                root_cause TEXT NOT NULL,
                suggested_action TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                resolved_at TEXT
            );

            CREATE TABLE IF NOT EXISTS actions (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (incident_id) REFERENCES incidents (id)
            );

            CREATE INDEX IF NOT EXISTS idx_logs_fingerprint_timestamp
            ON logs (fingerprint, timestamp);

            CREATE INDEX IF NOT EXISTS idx_incidents_fingerprint_status
            ON incidents (fingerprint, status);

            CREATE INDEX IF NOT EXISTS idx_actions_incident_id
            ON actions (incident_id);
            """
        )
