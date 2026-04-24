import argparse
import sqlite3
from pathlib import Path


def _print_rows(title: str, rows: list[sqlite3.Row]) -> None:
    print(f"\n{title}:")
    if not rows:
        print("- none")
        return
    for row in rows:
        print("- " + " | ".join(str(value) for value in row))


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect local SQLite demo DB")
    parser.add_argument("--db-path", type=Path, required=True)
    args = parser.parse_args()
    if not args.db_path.exists():
        raise FileNotFoundError(f"SQLite DB not found: {args.db_path}")

    connection = sqlite3.connect(args.db_path)
    connection.row_factory = sqlite3.Row
    try:
        category_counts = connection.execute(
            """
            SELECT COALESCE(category, 'unknown') AS category, COUNT(*) AS cnt
            FROM products
            GROUP BY COALESCE(category, 'unknown')
            ORDER BY cnt DESC, category ASC
            """
        ).fetchall()
        knowledge_counts = connection.execute(
            """
            SELECT COALESCE(doc_type, 'other') AS doc_type, COUNT(*) AS cnt
            FROM knowledge_documents
            GROUP BY COALESCE(doc_type, 'other')
            ORDER BY cnt DESC, doc_type ASC
            """
        ).fetchall()
        adjustable_samples = connection.execute(
            """
            SELECT id, name, price_rub, min_height_cm, max_height_cm
            FROM products
            WHERE category = 'adjustable_desk'
            ORDER BY COALESCE(price_rub, 999999999), id
            LIMIT 10
            """
        ).fetchall()
        accessory_samples = connection.execute(
            """
            SELECT id, name, price_rub
            FROM products
            WHERE category = 'accessory'
            ORDER BY COALESCE(price_rub, 999999999), id
            LIMIT 10
            """
        ).fetchall()
        without_price = connection.execute(
            """
            SELECT id, name, category
            FROM products
            WHERE price_rub IS NULL OR price_rub <= 0
            ORDER BY id
            """
        ).fetchall()
        unknown_products = connection.execute(
            """
            SELECT id, name, source_url
            FROM products
            WHERE COALESCE(category, 'unknown') = 'unknown'
            ORDER BY id
            """
        ).fetchall()
        suspicious = connection.execute(
            """
            SELECT id, name, category, price_rub, min_height_cm, max_height_cm, source_url
            FROM products
            WHERE (
                category = 'adjustable_desk'
                AND (min_height_cm IS NULL OR max_height_cm IS NULL)
            )
               OR source_url IS NULL OR TRIM(source_url) = ''
            ORDER BY id
            """
        ).fetchall()
        duplicates = connection.execute(
            """
            SELECT source_url, COUNT(*) AS cnt
            FROM products
            WHERE source_url IS NOT NULL AND TRIM(source_url) != ''
            GROUP BY source_url
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC, source_url
            """
        ).fetchall()
    finally:
        connection.close()

    print("Products by category:")
    for row in category_counts:
        print(f"- {row['category']}: {row['cnt']}")

    print("\nKnowledge docs by type:")
    for row in knowledge_counts:
        print(f"- {row['doc_type']}: {row['cnt']}")

    _print_rows("Top 10 adjustable_desk", adjustable_samples)
    _print_rows("Top 10 accessory", accessory_samples)
    _print_rows("Products without price", without_price)
    _print_rows("Unknown products", unknown_products)
    _print_rows("Suspicious product rows", suspicious)
    _print_rows("Duplicate source_url", duplicates)


if __name__ == "__main__":
    main()
