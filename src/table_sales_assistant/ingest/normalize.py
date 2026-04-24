import re


def parse_price_rub(text: str | None) -> int | None:
    if not text:
        return None
    cleaned = re.sub(r"[^\d]", "", text)
    if not cleaned:
        return None
    return int(cleaned)


def parse_height_range_cm(text: str | None) -> tuple[int | None, int | None]:
    if not text:
        return (None, None)
    normalized = text.lower().replace(",", ".")
    match = re.search(r"(\d{2,3})\s*(?:-|до)\s*(\d{2,3})\s*см?", normalized)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    return (None, None)


def parse_dimensions_cm(text: str | None) -> tuple[int | None, int | None]:
    if not text:
        return (None, None)
    normalized = text.lower().replace("х", "x")
    match = re.search(r"(\d{2,3})\s*[x*]\s*(\d{2,3})\s*см?", normalized)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    return (None, None)


def parse_motors_count(text: str | None) -> int | None:
    if not text:
        return None
    normalized = text.lower()
    if "одномотор" in normalized:
        return 1
    if "двухмотор" in normalized:
        return 2
    match = re.search(r"(\d)\s*мотор", normalized)
    if match:
        return int(match.group(1))
    return None


def parse_lifting_capacity_kg(text: str | None) -> int | None:
    if not text:
        return None
    normalized = text.lower().replace(",", ".")
    match = re.search(r"(?:до\s*)?(\d{2,3})\s*кг", normalized)
    if not match:
        return None
    return int(match.group(1))


def detect_tabletop_material(text: str | None) -> str | None:
    if not text:
        return None
    normalized = text.lower()
    if "лдсп" in normalized:
        return "ЛДСП"
    if "мдф" in normalized:
        return "МДФ"
    if "массив" in normalized:
        return "массив"
    if "шпон" in normalized:
        return "шпон"
    return None


def classify_category(url: str, title: str, breadcrumbs: str, text: str) -> str:
    haystack = f"{url} {title} {breadcrumbs} {text}".lower()
    if any(token in haystack for token in ("кресл", "/chairs")):
        return "chair"
    if any(token in haystack for token in ("аксессуар", "/accessories", "кабель", "кронштейн")):
        return "accessory"
    if any(token in haystack for token in ("столешниц", "/tabletop")):
        return "tabletop"
    if any(token in haystack for token in ("подстоль", "рама", "/frame")):
        return "frame"
    if any(
        token in haystack
        for token in (
            "регулировк",
            "стол с регулировкой",
            "регулируем",
            "desk",
            "/catalog",
        )
    ):
        return "adjustable_desk"
    return "unknown"
