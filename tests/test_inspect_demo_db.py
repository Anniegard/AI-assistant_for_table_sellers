import subprocess
import sys
from pathlib import Path

from table_sales_assistant.storage.sqlite import connect_sqlite, ensure_sqlite_schema


def _schema_path() -> Path:
    return Path("src/table_sales_assistant/storage/sqlite_schema.sql")


def test_inspect_demo_db(tmp_path: Path) -> None:
    db_path = tmp_path / "inspect.sqlite"
    with connect_sqlite(db_path) as connection:
        ensure_sqlite_schema(connection, _schema_path())
        connection.execute(
            """
            INSERT INTO products (
                id, source, source_url, source_product_id, name, category, subtype, price_rub,
                min_height_cm, max_height_cm, width_cm, depth_cm, motors_count, lifting_capacity_kg,
                tabletop_material, description_short, availability, raw_payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "desk-1",
                "demo",
                "https://example.local/desk-1",
                None,
                "Desk 1",
                "adjustable_desk",
                None,
                49900,
                62,
                127,
                140,
                70,
                2,
                120,
                "ЛДСП",
                "demo",
                "in_stock",
                "{}",
            ),
        )
        connection.execute(
            """
            INSERT INTO products (
                id, source, source_url, source_product_id, name, category, subtype, price_rub,
                min_height_cm, max_height_cm, width_cm, depth_cm, motors_count, lifting_capacity_kg,
                tabletop_material, description_short, availability, raw_payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "acc-1",
                "demo",
                "https://example.local/acc-1",
                None,
                "Acc 1",
                "accessory",
                None,
                3900,
                None,
                None,
                None,
                None,
                1,
                None,
                None,
                "demo",
                "in_stock",
                "{}",
            ),
        )
        connection.execute(
            """
            INSERT INTO knowledge_documents (
                id, source, source_url, title, doc_type, content, summary, tags_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "k1",
                "demo",
                "https://example.local/faq",
                "FAQ",
                "faq",
                "content",
                "summary",
                "[]",
            ),
        )
        connection.commit()

    result = subprocess.run(
        [sys.executable, "scripts/inspect_demo_db.py", "--db-path", str(db_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    output = result.stdout.lower()
    assert "products by category" in output
    assert "adjustable_desk" in output
    assert "accessory" in output
    assert "knowledge docs by type" in output
