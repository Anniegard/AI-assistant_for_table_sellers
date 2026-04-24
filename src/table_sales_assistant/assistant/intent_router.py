from table_sales_assistant.assistant.models import DialogueIntent


class IntentRouter:
    def route(self, text: str) -> DialogueIntent:
        lowered = (text or "").strip().lower()
        if not lowered:
            return DialogueIntent.UNKNOWN
        has_question_signal = "?" in lowered or any(
            token in lowered
            for token in (
                "что",
                "зачем",
                "какой",
                "какая",
                "какие",
                "чем",
                "почему",
                "как",
                "отлича",
            )
        )
        if any(token in lowered for token in ("начать заново", "/start", "сброс", "заново")):
            return DialogueIntent.RESTART
        if any(
            token in lowered
            for token in (
                "оставить заявку",
                "оставь заявку",
                "хочу заявку",
                "передай менеджеру",
                "свяжите с менеджером",
                "связались",
                "заявк",
            )
        ):
            return DialogueIntent.LEAVE_LEAD
        if "менеджер" in lowered:
            return DialogueIntent.HANDOFF_MANAGER
        if any(
            token in lowered
            for token in (
                "сравни",
                "сравнить",
                "сравни варианты",
                "какой лучше",
                "что выбрать",
                "чем отличаются",
            )
        ):
            return DialogueIntent.COMPARE
        if any(token in lowered for token in ("дорого", "дешевле", "бюджетн")):
            return DialogueIntent.OBJECTION_PRICE
        if any(
            token in lowered
            for token in (
                "аксессуар",
                "аксессуары",
                "лоток",
                "кабель-канал",
                "кабель канал",
                "что добавить к столу",
                "нужен лоток",
            )
        ):
            return DialogueIntent.ACCESSORY_REQUEST
        if any(token in lowered for token in ("привет", "как дела", "спасибо")):
            return DialogueIntent.SMALL_TALK
        if any(
            token in lowered
            for token in (
                "два мотора",
                "2 мотора",
                "один мотор",
                "1 мотор",
                "мотор лучше",
                "разница моторов",
                "грузоподъем",
                "размер столешницы",
                "какой размер",
            )
        ) or (
            has_question_signal
            and any(token in lowered for token in ("мотор", "грузоподъем", "столешниц"))
        ):
            return DialogueIntent.FAQ
        if any(token in lowered for token in ("достав", "гарант", "сборк", "материал")):
            return DialogueIntent.DELIVERY_WARRANTY_MATERIALS
        if has_question_signal:
            return DialogueIntent.FAQ
        if any(
            token in lowered
            for token in ("подбери", "подобрать", "подбор", "нужен стол", "стол для")
        ):
            return DialogueIntent.RECOMMEND
        return DialogueIntent.UNKNOWN
