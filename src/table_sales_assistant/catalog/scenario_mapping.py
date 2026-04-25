"""Map internal selection scenarios to catalog product.use_cases tags for scoring."""

from __future__ import annotations

# Catalog tags seen in sample data / importers
_INTERNAL_TO_CATALOG_TAGS: dict[str, frozenset[str]] = {
    "home_office": frozenset({"home_office", "study", "it_work", "family_workspace"}),
    "office": frozenset({"family_workspace", "home_office", "it_work", "executive_office"}),
    "gaming": frozenset({"it_work", "engineering", "home_office"}),
    "study": frozenset({"study", "home_office"}),
    "unknown": frozenset(),
}


def catalog_tags_for_scenario(scenario: str | None) -> frozenset[str]:
    if not scenario:
        return frozenset()
    mapped = _INTERNAL_TO_CATALOG_TAGS.get(scenario)
    if mapped is not None:
        return mapped
    return frozenset({scenario})
