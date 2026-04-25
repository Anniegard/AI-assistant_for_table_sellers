from table_sales_assistant.assistant.models import AssistantGoal, AssistantResponse, DialogueIntent


class ResponseBuilder:
    @staticmethod
    def _format_confidence(score: float | None) -> str:
        if score is None:
            return "medium"
        if score >= 72:
            return "high"
        if score >= 60:
            return "medium"
        return "low"

    @staticmethod
    def with_cta(
        text: str,
        *,
        goal: AssistantGoal,
        intent: DialogueIntent,
        cta: str,
    ) -> AssistantResponse:
        return AssistantResponse(text=text, goal=goal, intent=intent, cta=cta)

    @staticmethod
    def plain(text: str, *, goal: AssistantGoal, intent: DialogueIntent) -> AssistantResponse:
        return AssistantResponse(text=text, goal=goal, intent=intent)

    @classmethod
    def recommendation(
        cls,
        *,
        intro_lines: list[str],
        items: list[dict[str, str]],
        cta: str,
        intent: DialogueIntent,
    ) -> AssistantResponse:
        lines = [*intro_lines, "", "Рекомендую:"]
        for idx, item in enumerate(items[:3], start=1):
            lines.append(f"{idx}. {item['name']} — {item['price']}")
            lines.append(item["reason"])
            if item["tradeoff"]:
                lines.append(f"Важно учесть: {item['tradeoff']}")
        return cls.with_cta(
            "\n".join(lines).strip(),
            goal=AssistantGoal.RECOMMEND,
            intent=intent,
            cta=cta,
        )

    @classmethod
    def faq(
        cls,
        *,
        answer: str,
        known_params: list[str],
        cta: str,
        intent: DialogueIntent,
    ) -> AssistantResponse:
        context_line = ""
        if known_params:
            context_line = f"С учетом ваших параметров ({', '.join(known_params)}). "
        text = f"{context_line}{answer}"
        return cls.with_cta(text, goal=AssistantGoal.ANSWER_QUESTION, intent=intent, cta=cta)

    @classmethod
    def comparison(
        cls, *, bullets: list[str], conclusion: str, cta: str, intent: DialogueIntent
    ) -> AssistantResponse:
        lines = ["Сравнение по последним вариантам:"]
        lines.extend(f"- {line}" for line in bullets)
        lines.extend(["", conclusion])
        return cls.with_cta(
            "\n".join(lines),
            goal=AssistantGoal.COMPARE,
            intent=intent,
            cta=cta,
        )

    @classmethod
    def no_exact_match(
        cls,
        *,
        blocking_constraint: str,
        alternatives: list[str],
        cta: str,
        intent: DialogueIntent,
    ) -> AssistantResponse:
        lines = [
            "Точного совпадения сейчас нет.",
            f"Что ограничивает подбор: {blocking_constraint}.",
        ]
        if alternatives:
            lines.append("Ближайшие альтернативы:")
            lines.extend(f"- {item}" for item in alternatives[:3])
        return cls.with_cta(
            "\n".join(lines),
            goal=AssistantGoal.HANDOFF_READY,
            intent=intent,
            cta=cta,
        )
