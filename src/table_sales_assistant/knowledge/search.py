def search_knowledge(articles: dict[str, str], keyword: str) -> list[tuple[str, str]]:
    needle = keyword.lower().strip()
    if not needle:
        return []

    matches: list[tuple[str, str]] = []
    for title, content in articles.items():
        if needle in content.lower() or needle in title.lower():
            matches.append((title, content))
    return matches
