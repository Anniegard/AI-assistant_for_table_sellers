from pathlib import Path

from table_sales_assistant.knowledge.loader import load_markdown_knowledge
from table_sales_assistant.knowledge.search import search_knowledge
from table_sales_assistant.knowledge.sqlite_repository import SQLiteKnowledgeRepository


class FAQService:
    def __init__(
        self,
        knowledge_dir: Path | None = None,
        sqlite_db_path: Path | None = None,
    ) -> None:
        self.articles = load_markdown_knowledge(knowledge_dir) if knowledge_dir else {}
        self.sqlite_repository = (
            SQLiteKnowledgeRepository(sqlite_db_path) if sqlite_db_path else None
        )

    def answer(self, question: str) -> str | None:
        if self.sqlite_repository is not None:
            docs = self.sqlite_repository.search(question, limit=1)
            if not docs:
                return None
            doc = docs[0]
            summary = doc["summary"] or ""
            if not summary:
                preview = doc["content"].strip().splitlines()
                summary = " ".join(line.strip() for line in preview[:3] if line.strip())
            return f'{doc["title"]}: {summary}'

        hits = search_knowledge(self.articles, question)
        if not hits:
            return None

        title, content = hits[0]
        preview = content.strip().splitlines()
        short_answer = " ".join(line.strip() for line in preview[:3] if line.strip())
        return f"{title}: {short_answer}"
