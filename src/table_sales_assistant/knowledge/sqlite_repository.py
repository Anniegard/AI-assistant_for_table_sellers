import json
import math
import re
from pathlib import Path

from table_sales_assistant.storage.sqlite import connect_sqlite


def _tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-zA-Zа-яА-Я0-9]+", text.lower()) if len(token) >= 2]


class SQLiteKnowledgeRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def search(self, query: str, limit: int = 3) -> list[dict[str, str]]:
        if not query.strip():
            return []
        if not self.db_path.exists():
            raise FileNotFoundError(f"SQLite knowledge DB not found: {self.db_path}")

        with connect_sqlite(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT title, source_url, doc_type, content, summary, tags_json
                FROM knowledge_documents
                """
            ).fetchall()

        doc_freq: dict[str, int] = {}
        tokenized_docs: list[tuple[dict[str, str], list[str]]] = []
        for row in rows:
            tags = ""
            if row["tags_json"]:
                try:
                    parsed = json.loads(row["tags_json"])
                    if isinstance(parsed, list):
                        tags = " ".join(str(item) for item in parsed)
                except json.JSONDecodeError:
                    tags = ""
            doc = {
                "title": row["title"],
                "source_url": row["source_url"],
                "doc_type": row["doc_type"],
                "content": row["content"],
                "summary": row["summary"] or "",
                "tags": tags,
            }
            tokens = _tokenize(f'{doc["title"]}\n{doc["content"]}\n{doc["tags"]}')
            tokenized_docs.append((doc, tokens))
            for token in set(tokens):
                doc_freq[token] = doc_freq.get(token, 0) + 1

        total_docs = max(1, len(tokenized_docs))
        query_tokens = _tokenize(query)
        scored: list[tuple[float, dict[str, str]]] = []
        for doc, tokens in tokenized_docs:
            score = 0.0
            body = f'{doc["title"]}\n{doc["content"]}\n{doc["tags"]}'.lower()
            query_lower = query.lower()
            if query_lower in doc["title"].lower():
                score += 3.0
            if query_lower in body:
                score += 2.0
            for token in query_tokens:
                tf = tokens.count(token)
                if tf == 0:
                    continue
                df = doc_freq.get(token, 1)
                idf = math.log((1 + total_docs) / (1 + df)) + 1
                score += tf * idf
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [doc for _, doc in scored[:limit]]
