import re


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Zа-яА-Я0-9]+", text.lower())
    return {token for token in tokens if len(token) >= 2}


def search_knowledge(articles: dict[str, str], keyword: str) -> list[tuple[str, str]]:
    needle = keyword.lower().strip()
    if not needle:
        return []

    query_tokens = _tokenize(needle)
    scored_matches: list[tuple[int, tuple[str, str]]] = []
    for title, content in articles.items():
        title_lower = title.lower()
        content_lower = content.lower()
        score = 0
        if needle in title_lower:
            score += 4
        if needle in content_lower:
            score += 3

        if query_tokens:
            article_tokens = _tokenize(f"{title}\n{content}")
            score += sum(1 for token in query_tokens if token in article_tokens)

        if score > 0:
            scored_matches.append((score, (title, content)))

    scored_matches.sort(key=lambda item: item[0], reverse=True)
    return [match for _, match in scored_matches]
