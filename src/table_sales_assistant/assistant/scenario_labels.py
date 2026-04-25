"""Human-readable labels for internal scenario keys (user-facing text only)."""

_SCENARIO_LABEL_RU: dict[str, str] = {
    "home_office": "для работы дома",
    "office": "для офиса",
    "gaming": "для игр или тяжёлого сетапа",
    "study": "для учёбы",
    "unknown": "не указан",
}

# Legacy / catalog-style tags still stored in some sessions
_CATALOG_STYLE_LABEL_RU: dict[str, str] = {
    "it_work": "для IT и длительной работы за компьютером",
    "engineering": "для инженерных задач и тяжёлого сетапа",
    "executive_office": "для руководительского кабинета",
    "family_workspace": "для семейного или офисного пространства",
}


def scenario_label_ru(internal: str | None) -> str:
    if not internal:
        return "не указан"
    if internal in _SCENARIO_LABEL_RU:
        return _SCENARIO_LABEL_RU[internal]
    return _CATALOG_STYLE_LABEL_RU.get(internal, "не указан")


def is_internal_scenario_token(value: str) -> bool:
    v = value.strip()
    return v in _SCENARIO_LABEL_RU or v in _CATALOG_STYLE_LABEL_RU
