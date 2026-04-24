from table_sales_assistant.leads.models import Lead


def _fmt_bool(value: bool | None) -> str:
    if value is None:
        return "-"
    return "Да" if value else "Нет"


def _fmt_optional(value: object | None) -> str:
    if value in (None, ""):
        return "-"
    return str(value)


def format_lead_for_manager(lead: Lead) -> str:
    recommended = ", ".join(lead.recommended_products) if lead.recommended_products else "-"
    recent_questions = "; ".join(lead.recent_questions) if lead.recent_questions else "-"
    known_params = lead.known_params if lead.known_params else "-"
    return (
        "Новая заявка из демо-бота\n"
        f"Имя: {lead.name}\n"
        f"Телефон: {lead.phone}\n"
        f"Город: {lead.city}\n"
        f"Бюджет: {_fmt_optional(lead.budget)}\n"
        f"Рост: {_fmt_optional(lead.height_cm)}\n"
        f"Сценарий: {_fmt_optional(lead.use_case)}\n"
        f"Мониторы: {_fmt_optional(lead.monitors_count)}\n"
        f"Системный блок: {_fmt_bool(lead.has_pc_case)}\n"
        f"Размер: {_fmt_optional(lead.preferred_size)}\n"
        f"Доставка: {_fmt_bool(lead.needs_delivery)}\n"
        f"Сборка: {_fmt_bool(lead.needs_assembly)}\n"
        f"Известные параметры: {_fmt_optional(known_params)}\n"
        f"Рекомендации: {recommended}\n"
        f"Сводка диалога: {_fmt_optional(lead.recent_dialogue_summary)}\n"
        f"Вопросы клиента: {recent_questions}\n"
        f"Выбранный вариант: {_fmt_optional(lead.selected_product_id)}\n"
        f"Комментарий ассистента: {_fmt_optional(lead.assistant_comment)}\n"
        f"Комментарий: {_fmt_optional(lead.comment)}\n"
        f"Источник: {lead.source}"
    )
