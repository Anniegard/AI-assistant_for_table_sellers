import sqlite3
from pathlib import Path


def connect_sqlite(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_sqlite_schema(connection: sqlite3.Connection, schema_path: Path) -> None:
    with schema_path.open("r", encoding="utf-8") as schema_file:
        connection.executescript(schema_file.read())
    connection.commit()
