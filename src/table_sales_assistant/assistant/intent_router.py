from table_sales_assistant.assistant.models import DialogueIntent


class IntentRouter:
    def route(self, text: str) -> DialogueIntent:
        lowered = (text or "").strip().lower()
        if not lowered:
            return DialogueIntent.UNKNOWN
        if any(token in lowered for token in ("начать заново", "/start", "сброс", "заново")):
            return DialogueIntent.RESTART
        if any(token in lowered for token in ("оставить заявку", "связались", "заявк")):
            return DialogueIntent.LEAVE_LEAD
        if "менеджер" in lowered:
            return DialogueIntent.HANDOFF_MANAGER
        if any(token in lowered for token in ("сравни", "сравнить")):
            return DialogueIntent.COMPARE
        if any(token in lowered for token in ("почему", "чем", "мотор")):
            return DialogueIntent.CLARIFY_RECOMMENDATION
        if any(token in lowered for token in ("достав", "гарант", "сборк", "материал", "размер")):
            return DialogueIntent.DELIVERY_WARRANTY_MATERIALS
        if any(token in lowered for token in ("дорого", "дешевле", "бюджетн")):
            return DialogueIntent.OBJECTION_PRICE
        if any(token in lowered for token in ("привет", "как дела", "спасибо")):
            return DialogueIntent.SMALL_TALK
        if any(token in lowered for token in ("нужен стол", "подобрать", "подбор", "стол для")):
            return DialogueIntent.RECOMMEND
        if "?" in lowered:
            return DialogueIntent.FAQ
        return DialogueIntent.UNKNOWN
