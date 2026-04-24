from table_sales_assistant.leads.models import Lead


def format_lead_for_manager(lead: Lead) -> str:
    recommended = ", ".join(lead.recommended_products) if lead.recommended_products else "-"
    return (
        "Новая заявка из демо-бота\n"
        f"Имя: {lead.name}\n"
        f"Телефон: {lead.phone}\n"
        f"Город: {lead.city}\n"
        f"Рост: {lead.height_cm}\n"
        f"Бюджет: {lead.budget}\n"
        f"Сценарий: {lead.use_case}\n"
        f"Мониторы: {lead.monitors_count}\n"
        f"Системный блок: {lead.has_pc_case}\n"
        f"Размер: {lead.preferred_size}\n"
        f"Доставка: {lead.needs_delivery}\n"
        f"Сборка: {lead.needs_assembly}\n"
        f"Рекомендации: {recommended}\n"
        f"Комментарий: {lead.comment or '-'}\n"
        f"Источник: {lead.source}"
    )
