from pathlib import Path

from table_sales_assistant.knowledge.loader import load_markdown_knowledge
from table_sales_assistant.knowledge.search import search_knowledge
from table_sales_assistant.knowledge.sqlite_repository import SQLiteKnowledgeRepository


class FAQService:
    _FALLBACK_ANSWERS = {
        "motors": (
            "Для большинства рабочих сетапов два мотора стабильнее и тише под нагрузкой. "
            "Один мотор чаще подходит для более легких и бюджетных конфигураций."
        ),
        "load": (
            "Если у вас два монитора, кронштейны и системный блок, обычно стоит ориентироваться "
            "на запас грузоподъемности от 100 кг."
        ),
        "tabletop_size": (
            "Для одного монитора обычно хватает ширины 100-120 см, "
            "для двух мониторов чаще выбирают "
            "120-140 см и глубину от 70 см."
        ),
        "warranty": (
            "Гарантия зависит от конкретной модели и поставки. Для демо считаем это параметром, "
            "который менеджер подтверждает перед оформлением."
        ),
        "delivery": (
            "Доставка и сроки зависят от города и наличия. В демо показываем общий процесс, "
            "а точные условия менеджер подтверждает отдельно."
        ),
        "assembly": (
            "Сборка обычно доступна как отдельная услуга. В демо можно зафиксировать этот запрос "
            "в заявке для менеджера."
        ),
        "accessories": (
            "Чаще всего к столу добавляют кабель-менеджмент, кронштейн монитора и держатель "
            "системного блока под тяжелый сетап."
        ),
        "materials": (
            "ЛДСП обычно доступнее по цене и практичен в уходе, "
            "массив чаще выбирают за внешний вид "
            "и премиальный тактильный опыт."
        ),
        "height_190": (
            "При росте 190 см обычно важен широкий диапазон регулировки и устойчивость на верхних "
            "положениях, поэтому чаще смотрят модели с двумя моторами."
        ),
    }

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
                fallback = self._fallback_answer(question)
                return fallback
            doc = docs[0]
            summary = doc["summary"] or ""
            if not summary:
                preview = doc["content"].strip().splitlines()
                summary = " ".join(line.strip() for line in preview[:3] if line.strip())
            return f'{doc["title"]}: {summary}'

        hits = search_knowledge(self.articles, question)
        if not hits:
            return self._fallback_answer(question)

        title, content = hits[0]
        preview = content.strip().splitlines()
        short_answer = " ".join(line.strip() for line in preview[:3] if line.strip())
        return f"{title}: {short_answer}"

    def _fallback_answer(self, question: str) -> str | None:
        lowered = (question or "").lower()
        if any(token in lowered for token in ("мотор", "мотора", "моторов")):
            return self._FALLBACK_ANSWERS["motors"]
        if any(token in lowered for token in ("грузопод", "нагруз")):
            return self._FALLBACK_ANSWERS["load"]
        if any(token in lowered for token in ("столешниц", "размер")):
            return self._FALLBACK_ANSWERS["tabletop_size"]
        if "гарант" in lowered:
            return self._FALLBACK_ANSWERS["warranty"]
        if "достав" in lowered:
            return self._FALLBACK_ANSWERS["delivery"]
        if "сборк" in lowered:
            return self._FALLBACK_ANSWERS["assembly"]
        if any(token in lowered for token in ("аксессуар", "кабель", "кронштейн")):
            return self._FALLBACK_ANSWERS["accessories"]
        if any(token in lowered for token in ("лдсп", "массив", "материал")):
            return self._FALLBACK_ANSWERS["materials"]
        if "190" in lowered and "рост" in lowered:
            return self._FALLBACK_ANSWERS["height_190"]
        return None
