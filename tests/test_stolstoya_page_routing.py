from table_sales_assistant.ingest.stolstoya_importer import (
    _extract_links,
    _is_knowledge_page,
    _is_product_page,
)


def test_is_product_page_true_for_product_markers() -> None:
    assert _is_product_page(
        "https://stolstoya.ru/catalog/ramy/model-x",
        "Рама model-x",
        "Цена 49900 руб характеристики мотор 2 грузоподъемность 120 кг",
    )


def test_is_product_page_false_for_listing() -> None:
    assert not _is_product_page(
        "https://stolstoya.ru/catalog/ramy",
        "Каталог рам",
        "Категория товаров и фильтры",
    )


def test_is_knowledge_page_for_delivery() -> None:
    assert _is_knowledge_page(
        "https://stolstoya.ru/delivery-and-payment",
        "Доставка и оплата",
        "Условия доставки по регионам",
    )


def test_extract_links_filters_irrelevant_paths() -> None:
    html = """
    <html><body>
      <a href="/catalog">Catalog</a>
      <a href="/blog/post-1">Blog</a>
      <a href="/contacts">Contacts</a>
      <a href="/images/photo.jpg">Image</a>
    </body></html>
    """
    links = _extract_links("https://stolstoya.ru/", html)
    assert "https://stolstoya.ru/catalog" in links
    assert "https://stolstoya.ru/blog/post-1" in links
    assert "https://stolstoya.ru/contacts" not in links
