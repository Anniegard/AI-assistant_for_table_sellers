from table_sales_assistant.assistant.models import AssistantGoal, AssistantResponse, DialogueIntent


class ResponseBuilder:
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
