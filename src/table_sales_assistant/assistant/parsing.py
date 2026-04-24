import re

USE_CASE_KEYWORDS: dict[str, str] = {
    "дом": "home_office",
    "офис": "family_workspace",
    "разработ": "it_work",
    "it": "it_work",
    "учеб": "study",
    "руковод": "executive_office",
    "инженер": "engineering",
}


def extract_height_cm(text: str) -> int | None:
    match = re.search(r"(?:рост|height)\D{0,8}(\d{3})", text.lower())
    if match:
        return int(match.group(1))
    simple = re.search(r"\b(1[5-9]\d|20\d)\b", text)
    return int(simple.group(1)) if simple else None


def extract_monitors_count(text: str) -> int | None:
    lowered = text.lower()
    if "два монит" in lowered:
        return 2
    if "три монит" in lowered:
        return 3
    if "один монит" in lowered:
        return 1
    match = re.search(r"(\d+)\s*монитор", lowered)
    return int(match.group(1)) if match else None


def extract_budget_range(text: str) -> tuple[int | None, int | None]:
    normalized = text.lower().replace(" ", "")
    budget_keyword_match = re.search(r"(?:бюджет|budget)\D{0,8}(\d{4,6})", text.lower())
    if budget_keyword_match:
        return None, int(budget_keyword_match.group(1))
    range_match = re.search(r"(\d{2,3})[-–](\d{2,3})к", normalized)
    if range_match:
        return int(range_match.group(1)) * 1000, int(range_match.group(2)) * 1000

    up_to_match = re.search(r"(?:до|<=)(\d{2,3})к", normalized)
    if up_to_match:
        return None, int(up_to_match.group(1)) * 1000

    plain_k_match = re.search(r"\b(\d{2,3})к\b", normalized)
    if plain_k_match:
        value = int(plain_k_match.group(1)) * 1000
        return None, value

    rub_match = re.search(r"\b(\d{5,6})\b", normalized)
    if rub_match:
        value = int(rub_match.group(1))
        return None, value
    return None, None


def extract_use_case(text: str) -> str | None:
    lowered = text.lower()
    for key, mapped in USE_CASE_KEYWORDS.items():
        if key in lowered:
            return mapped
    return None


def extract_has_pc_case(text: str) -> bool | None:
    lowered = text.lower()
    if "системный блок" not in lowered:
        return None
    if any(token in lowered for token in ("нет", "не нужен", "без")):
        return False
    return True
