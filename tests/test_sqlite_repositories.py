from pathlib import Path

from table_sales_assistant.catalog.models import Product
from table_sales_assistant.catalog.recommender import ProductRecommender, RecommendationQuery
from table_sales_assistant.catalog.sqlite_repository import SQLiteCatalogRepository
from table_sales_assistant.knowledge.sqlite_repository import SQLiteKnowledgeRepository
from table_sales_assistant.services.faq_service import FAQService
from table_sales_assistant.storage.sqlite import connect_sqlite, ensure_sqlite_schema


def _schema_path() -> Path:
    return Path("src/table_sales_assistant/storage/sqlite_schema.sql")


def test_sqlite_catalog_repository_returns_product_model(tmp_path: Path) -> None:
    db_path = tmp_path / "demo.sqlite"
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
                "p1",
                "stolstoya",
                "https://stolstoya.ru/catalog/p1",
                None,
                "Desk P1",
                "adjustable_desk",
                None,
                79900,
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
        connection.commit()

    products = SQLiteCatalogRepository(db_path).load_products()
    assert products
    assert isinstance(products[0], Product)
    assert products[0].id == "p1"


def test_sqlite_height_range_not_used_as_user_height(tmp_path: Path) -> None:
    db_path = tmp_path / "demo.sqlite"
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
                "desk-height",
                "stolstoya",
                "https://stolstoya.ru/catalog/desk-height",
                None,
                "Desk Height",
                "adjustable_desk",
                None,
                50000,
                60,
                125,
                140,
                70,
                2,
                100,
                "ЛДСП",
                "demo",
                "in_stock",
                "{}",
            ),
        )
        connection.commit()

    products = SQLiteCatalogRepository(db_path).load_products()
    product = products[0]
    assert product.min_height_cm == 60
    assert product.max_height_cm == 125
    assert product.recommended_user_height_min_cm == 140
    assert product.recommended_user_height_max_cm == 210
    ranked = ProductRecommender().recommend(
        products,
        RecommendationQuery(budget=70000, user_height_cm=190, monitors_count=2),
    )
    assert ranked
    assert ranked[0].id == "desk-height"


def test_knowledge_repository_finds_two_motors_faq(tmp_path: Path) -> None:
    db_path = tmp_path / "demo.sqlite"
    with connect_sqlite(db_path) as connection:
        ensure_sqlite_schema(connection, _schema_path())
        connection.execute(
            """
            INSERT INTO knowledge_documents (
                id, source, source_url, title, doc_type, content, summary, tags_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "k1",
                "stolstoya",
                "https://stolstoya.ru/faq/motors",
                "Один мотор или два мотора",
                "faq",
                "Два мотора дают лучшую стабильность для двух мониторов.",
                "Два мотора стабильнее.",
                '["мотор","нагрузка"]',
            ),
        )
        connection.commit()

    repository = SQLiteKnowledgeRepository(db_path)
    results = repository.search("два мотора", limit=1)
    assert results
    assert "два мотора" in results[0]["title"].lower()

    answer = FAQService(sqlite_db_path=db_path).answer("Что лучше для двух мониторов?")
    assert answer


def test_knowledge_search_finds_motor_faq(tmp_path: Path) -> None:
    db_path = tmp_path / "demo.sqlite"
    with connect_sqlite(db_path) as connection:
        ensure_sqlite_schema(connection, _schema_path())
        connection.execute(
            """
            INSERT INTO knowledge_documents (
                id, source, source_url, title, doc_type, content, summary, tags_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "k-motor",
                "stolstoya",
                "https://stolstoya.ru/faq/two-motors",
                "Чем два мотора лучше",
                "faq",
                "Два мотора дают запас стабильности и лучше подходят для тяжелого сетапа.",
                "Два мотора стабильнее под нагрузкой.",
                '["мотор","стабильность"]',
            ),
        )
        connection.commit()

    answer = FAQService(sqlite_db_path=db_path).answer("чем два мотора лучше")
    assert answer
    assert "два мотора" in answer.lower()
