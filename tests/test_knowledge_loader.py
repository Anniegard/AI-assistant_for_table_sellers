from pathlib import Path

from table_sales_assistant.knowledge.loader import load_markdown_knowledge
from table_sales_assistant.knowledge.search import search_knowledge


def test_knowledge_loader_loads_markdown_files() -> None:
    articles = load_markdown_knowledge(Path('data/knowledge'))
    assert len(articles) >= 5


def test_knowledge_search_finds_keywords() -> None:
    articles = load_markdown_knowledge(Path('data/knowledge'))
    motor_hits = search_knowledge(articles, 'мотор')
    monitor_hits = search_knowledge(articles, 'монитор')

    assert motor_hits
    assert monitor_hits
