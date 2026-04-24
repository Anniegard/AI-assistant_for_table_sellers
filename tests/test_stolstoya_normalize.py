from table_sales_assistant.ingest.normalize import (
    classify_category,
    parse_height_range_cm,
    parse_lifting_capacity_kg,
    parse_price_rub,
)


def test_parse_price_rub() -> None:
    assert parse_price_rub("74 900 руб.") == 74900


def test_parse_height_range_cm() -> None:
    assert parse_height_range_cm("Диапазон: 50-116 см") == (50, 116)
    assert parse_height_range_cm("Высота 60 до 125 см") == (60, 125)


def test_parse_lifting_capacity_kg() -> None:
    assert parse_lifting_capacity_kg("Нагрузка до 250 кг") == 250


def test_classify_category_accessory() -> None:
    category = classify_category(
        url="https://stolstoya.ru/catalog/aksessuary/cable-tray",
        title="Кабель-канал",
        breadcrumbs="Каталог / Аксессуары",
        text="Аксессуар для кабель-менеджмента",
    )
    assert category == "accessory"


def test_classify_category_adjustable_desk() -> None:
    category = classify_category(
        url="https://stolstoya.ru/catalog/reguliruemye-stoly/model-a",
        title="Стол с регулировкой высоты",
        breadcrumbs="Каталог / Столы с регулировкой",
        text="Эргономичный стол для офиса",
    )
    assert category == "adjustable_desk"


def test_classify_category_not_chair_without_chair_path() -> None:
    category = classify_category(
        url="https://stolstoya.ru/catalog/reguliruemye-stoly/model-1",
        title="Эргономичный стол",
        breadcrumbs="Каталог / Столы",
        text="Подходит для офиса, не кресло.",
    )
    assert category == "adjustable_desk"


def test_importer_category_detection() -> None:
    assert (
        classify_category(
            url="https://stolstoya.ru/catalog/reguliruemye-stoly/model-x",
            title="Стол с регулировкой",
            breadcrumbs="Каталог / Столы",
            text="Регулируемый стол для офиса",
        )
        == "adjustable_desk"
    )
    assert (
        classify_category(
            url="https://stolstoya.ru/catalog/ramy/frame-x",
            title="Рама frame",
            breadcrumbs="Каталог / Рамы",
            text="Подстолье",
        )
        == "frame"
    )
    assert (
        classify_category(
            url="https://stolstoya.ru/catalog/tabletop/oak",
            title="Столешница",
            breadcrumbs="Каталог / Столешницы",
            text="Столешница из ЛДСП",
        )
        == "tabletop"
    )
    assert (
        classify_category(
            url="https://stolstoya.ru/catalog/accessories/cable",
            title="Кабельный лоток",
            breadcrumbs="Каталог / Аксессуары",
            text="аксессуар",
        )
        == "accessory"
    )
    assert (
        classify_category(
            url="https://stolstoya.ru/unknown/page",
            title="Страница",
            breadcrumbs="Инфо",
            text="информация без каталога",
        )
        == "unknown"
    )
