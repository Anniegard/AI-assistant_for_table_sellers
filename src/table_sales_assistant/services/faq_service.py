from table_sales_assistant.knowledge.loader import load_markdown_knowledge
from table_sales_assistant.knowledge.search import search_knowledge


class FAQService:
    def __init__(self, knowledge_dir) -> None:
        self.articles = load_markdown_knowledge(knowledge_dir)

    def answer(self, question: str) -> str | None:
        hits = search_knowledge(self.articles, question)
        if not hits:
            return None

        title, content = hits[0]
        preview = content.strip().splitlines()
        short_answer = " ".join(line.strip() for line in preview[:3] if line.strip())
        return f"{title}: {short_answer}"
