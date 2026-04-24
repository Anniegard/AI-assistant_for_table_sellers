from pathlib import Path

from table_sales_assistant.catalog.models import Product
from table_sales_assistant.storage.sqlite import connect_sqlite


class SQLiteCatalogRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def load_products(self) -> list[Product]:
        if not self.db_path.exists():
            raise FileNotFoundError(f"SQLite catalog DB not found: {self.db_path}")

        with connect_sqlite(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    name,
                    category,
                    price_rub,
                    min_height_cm,
                    max_height_cm,
                    width_cm,
                    depth_cm,
                    motors_count,
                    lifting_capacity_kg,
                    tabletop_material,
                    source_url,
                    availability,
                    description_short
                FROM products
                """
            ).fetchall()

        products: list[Product] = []
        for row in rows:
            products.append(
                Product(
                    id=row["id"],
                    name=row["name"] or "Unknown product",
                    category=row["category"] or "unknown",
                    segment="imported_demo",
                    price=row["price_rub"] or 0,
                    min_height_cm=row["min_height_cm"] or 0,
                    max_height_cm=row["max_height_cm"] or 0,
                    tabletop_width_cm=row["width_cm"] or 0,
                    tabletop_depth_cm=row["depth_cm"] or 0,
                    motors_count=row["motors_count"] or 1,
                    lifting_capacity_kg=row["lifting_capacity_kg"] or 0,
                    material=row["tabletop_material"] or "unknown",
                    colors=[],
                    use_cases=[],
                    recommended_user_height_min_cm=(row["min_height_cm"] or 0),
                    recommended_user_height_max_cm=(row["max_height_cm"] or 999),
                    product_url=row["source_url"] or "",
                    in_stock=(row["availability"] or "").lower() != "out_of_stock",
                    short_description=row["description_short"] or "",
                )
            )
        return products
