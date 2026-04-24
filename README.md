# AI-assistant for table sellers

Демо Telegram-бот AI sales assistant для продавцов регулируемых по высоте столов.

## Business value

- Помогает клиенту выбрать модель по параметрам без долгой переписки.
- Закрывает повторяющиеся FAQ-вопросы в первом касании.
- Сохраняет структурированный лид и передает его менеджеру.
- Показывает бизнесу proof of value без интеграции в сайт и CRM.

## Что показывает демо

1. Подбор стола по бюджету, росту, мониторам, сценарию и моторам.
2. FAQ-ответы на базе markdown knowledge.
3. AI-объяснение уже выбранных deterministic рекомендаций.
4. Сбор заявки и локальное сохранение в JSON.
5. Отправку заявки менеджеру в Telegram при заданном chat id.

## Ограничения демо

- Все товары и лиды в репозитории: sample data.
- Нет обещаний по реальным срокам, остаткам и финальной цене.
- Без `OPENAI_API_KEY` проект работает в offline/demo режиме.

## Архитектура

- `bot`: Telegram handlers и FSM-состояния.
- `catalog`: структура товаров и deterministic filtering.
- `knowledge`: загрузка markdown и keyword search.
- `ai`: клиент OpenAI и промпты объяснений.
- `services`: orchestration рекомендаций, FAQ, лидов.
- `leads`: модель и JSON repository.
- `notifications`: форматирование лида и отправка менеджеру.

## Быстрый запуск

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest
ruff check .
python -m table_sales_assistant.main
```

## Настройка `.env`

1. Скопируйте `.env.example` в `.env`.
2. Заполните `TELEGRAM_BOT_TOKEN`.
3. Опционально заполните `OPENAI_API_KEY` и `MANAGER_TELEGRAM_CHAT_ID`.

Ключевые переменные:

- `TELEGRAM_BOT_TOKEN`
- `OPENAI_API_KEY` (optional)
- `MANAGER_TELEGRAM_CHAT_ID` (optional)
- `PRODUCTS_PATH`
- `KNOWLEDGE_DIR`
- `LEADS_PATH`
- `LOG_LEVEL`

## Demo journey

- Запустить бота.
- Пройти `/start`.
- Выбрать подбор стола и получить 2-3 рекомендации.
- Задать FAQ-вопрос.
- Оставить заявку и проверить JSON файл лидов.
- Проверить отправку менеджеру при заданном `MANAGER_TELEGRAM_CHAT_ID`.

## Документация

- `docs/demo_script.md`
- `docs/demo_checklist.md`
- `docs/stage_5_packaging.md`
- `docs/commercial_positioning.md`
- `docs/client_pitch.md`

## Roadmap

- Stage 1: Project setup
- Stage 2: Telegram MVP
- Stage 3: AI recommendation flow
- Stage 4: Lead collection and manager notification
- Stage 5: Demo packaging

## License

This project is source-available. Commercial use is prohibited without prior
written permission from the author. See `LICENSE` for full terms.

