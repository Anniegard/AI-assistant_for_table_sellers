import json
from pathlib import Path

from table_sales_assistant.catalog.models import Product


class ProductRepository:
    def __init__(self, products_path: Path) -> None:
        self.products_path = products_path

    def load_products(self) -> list[Product]:
        with self.products_path.open("r", encoding="utf-8-sig") as fp:
            raw_products = json.load(fp)
        return [Product.model_validate(item) for item in raw_products]
