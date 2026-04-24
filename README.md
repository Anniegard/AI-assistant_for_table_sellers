# AI-assistant for table sellers

Демо Telegram-бот с сущностью `ЭргоАссистент`: разговорный AI sales assistant для продавцов регулируемых по высоте столов.

## Business value

- Помогает клиенту выбрать модель по параметрам без долгой переписки.
- Закрывает повторяющиеся FAQ-вопросы в первом касании.
- Сохраняет структурированный лид и передает его менеджеру.
- Показывает бизнесу proof of value без интеграции в сайт и CRM.

## Что показывает демо

1. Разговорный подбор по свободному тексту и кнопкам.
2. Intent routing: подбор, вопросы, сравнение, возражения по цене, заявка.
3. Scoring-рекомендации 2-3 вариантов (fit score, reasons, tradeoffs).
4. FAQ-ответы на базе markdown knowledge.
5. AI-объяснение только catalog-backed рекомендаций.
6. Сбор заявки и расширенное резюме для менеджера.

## Ограничения демо

- Все товары и лиды в репозитории: sample data.
- Нет обещаний по реальным срокам, остаткам и финальной цене.
- Без `OPENAI_API_KEY` проект работает в offline/demo режиме.
- Это MVP: без CRM, web-widget и production RAG.

## Архитектура

- `bot`: Telegram transport слой и FSM-состояния.
- `assistant`: persona, intent routing, dialogue service, response builder.
- `catalog`: структура товаров и scoring recommender.
- `knowledge`: загрузка markdown и keyword search.
- `ai`: клиент OpenAI.
- `services`: рекомендации, объяснения, FAQ, лиды.
- `leads`: модель и JSON repository.
- `notifications`: форматирование лида и отправка менеджеру.

Поток запроса:
`Telegram -> DialogueService -> Catalog/Recommender/Knowledge -> AI Explanation -> LeadService -> Manager Notification`.

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
- Написать: `Мне нужен стол для дома, рост 185, два монитора, бюджет 60-80 тысяч`.
- Получить 2-3 рекомендации и объяснение.
- Спросить: `Почему два мотора лучше?` или `Есть дешевле?`.
- Написать: `Оставь заявку`.
- Проверить JSON файл лидов и уведомление менеджеру.
- Проверить отправку менеджеру при заданном `MANAGER_TELEGRAM_CHAT_ID`.

## Пример диалога

- Пользователь: `Мне нужен стол для дома, рост 185, два монитора, бюджет до 70к`
- ЭргоАссистент: `Подобрал 3 варианта из каталога ... Хотите, сравню по устойчивости и нагрузке?`
- Пользователь: `Почему не один мотор?`
- ЭргоАссистент: `Для двух мониторов и системного блока два мотора дают лучший запас стабильности...`
- Пользователь: `Оставь заявку`
- ЭргоАссистент: `Отлично, как вас зовут?`

## Session memory и свободный текст (MVP)

- Бот хранит в памяти текущей Telegram-сессии известные параметры клиента и последние сообщения диалога (до 10 реплик).
- Свободный текст поддерживает извлечение `рост`, `бюджет`, `сценарий`, `мониторы` и накопление параметров между сообщениями.
- Для подбора обязательны `рост` и `budget_max`; если `monitors_count` не указан, используется предварительный универсальный сценарий для 1-2 мониторов.
- При передаче лида менеджеру бот сохраняет `known_params`, последние вопросы, рекомендованные товары и краткую сводку диалога.
- Ограничения MVP: без Redis/PostgreSQL памяти, без CRM, рекомендации только из структурного каталога (LLM не источник характеристик товаров).

## Local demo data import

Локальный importer может расширить демо-базу из публичных страниц `https://stolstoya.ru/`.

Пример запуска:

```bash
python scripts/ingest_stolstoya.py --db-path data/private/stolstoya_demo.sqlite --max-pages 50 --delay 1.0
```

Полезные опции:
- `--dry-run` (только анализ, без записи в БД)
- `--refresh-cache` (перезаписать локальный cache)
- `--no-cache` (не использовать/не сохранять cache)
- `--source-base-url` (по умолчанию `https://stolstoya.ru/`)

Где создается БД:
- локально в `data/private/stolstoya_demo.sqlite` (или путь из `--db-path`).
- SQLite/raw/cache данные не должны коммититься в GitHub и исключены через `.gitignore`.

Подключение SQLite как источника каталога/знаний:
- `CATALOG_BACKEND=sqlite`
- `CATALOG_DB_PATH=data/private/stolstoya_demo.sqlite`
- `KNOWLEDGE_BACKEND=sqlite`
- `KNOWLEDGE_DB_PATH=data/private/stolstoya_demo.sqlite`

Важно:
- это локальный демо-импорт из публичных страниц, не официальный бот StolStoya;
- для коммерческого пилота нужно получить разрешение клиента или использовать предоставленный клиентом каталог;
- не коммитите спаршенные БД, raw HTML, картинки и полные выгрузки.

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