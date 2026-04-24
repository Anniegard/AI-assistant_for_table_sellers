from pathlib import Path

from table_sales_assistant.catalog.repository import ProductRepository


def test_product_repository_loads_sample_products() -> None:
    products_path = Path('data/products.sample.json')
    repository = ProductRepository(products_path=products_path)

    products = repository.load_products()

    assert len(products) >= 10
    assert any(item.motors_count == 2 for item in products)
