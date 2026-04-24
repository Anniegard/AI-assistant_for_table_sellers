from pathlib import Path


def load_markdown_knowledge(knowledge_dir: Path) -> dict[str, str]:
    articles: dict[str, str] = {}
    for path in sorted(knowledge_dir.glob('*.md')):
        articles[path.stem] = path.read_text(encoding='utf-8')
    return articles
