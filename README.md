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

## AI dialogue audit logs

Добавлен backend audit logging для обменов `пользователь -> ассистент`.

- Формат хранения: append-only JSONL.
- По умолчанию путь: `data/private/ai_dialogue_events.jsonl`.
- События включают: `conversation_id`, `channel`, `mode`, `intent`, `status`, `latency_ms`, `lead_id`, `recommended_products`.
- Текст сообщений проходит sanitization (`phone -> [phone]`, `email -> [email]`).
- При ошибке записи бот/API не падают: пишется только warning в обычный logger.

Пример env:

```env
AI_DIALOGUE_LOG_ENABLED=true
AI_DIALOGUE_LOG_PATH=data/private/ai_dialogue_events.jsonl
```

## Архитектура

- `bot`: Telegram transport слой и FSM-состояния.
- `assistant`: persona, intent routing, dialogue service, response builder.
- `audit`: модели и JSONL репозиторий для audit-событий диалога.
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

- `ENABLE_TELEGRAM` (default: `true`)
- `ENABLE_WEB_API` (default: `false`)
- `WEB_ALLOWED_ORIGINS` (comma-separated origins or `*`)
- `WEB_HOST` (default: `0.0.0.0`)
- `WEB_PORT` (default: `8000`)
- `TELEGRAM_BOT_TOKEN`
- `OPENAI_ENABLED` (default: `true`; set `false` for fully local demo mode)
- `OPENAI_API_KEY` (optional)
- `OPENAI_MODEL` (default: `gpt-4.1-mini`)
- `MANAGER_TELEGRAM_CHAT_ID` (optional)
- `PRODUCTS_PATH`
- `KNOWLEDGE_DIR`
- `LEADS_PATH`
- `LOG_LEVEL`

## Запуск транспортов

Telegram transport (как раньше):

```bash
python -m table_sales_assistant.main
```

Web API transport (FastAPI demo):

```bash
python -m table_sales_assistant.main_api
```

Рекомендуемые флаги в `.env`:

```env
ENABLE_TELEGRAM=false
ENABLE_WEB_API=true
WEB_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
WEB_HOST=0.0.0.0
WEB_PORT=8000
```

Production CORS example:

```env
WEB_ALLOWED_ORIGINS=https://anniland.ru,https://www.anniland.ru
```

## Web API demo endpoints

- `GET /api/demo/health`
- `POST /api/demo/sessions`
- `POST /api/demo/messages`
- `POST /api/demo/leads`

Пример сессии:

```bash
curl -X POST http://localhost:8000/api/demo/sessions
```

```bash
curl -X POST http://localhost:8000/api/demo/messages ^
  -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"web-...\",\"text\":\"рост 190 бюджет 50000 для дома\"}"
```

```bash
curl -X POST http://localhost:8000/api/demo/leads ^
  -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"web-...\",\"name\":\"Иван\",\"phone\":\"+79991234567\",\"city\":\"Москва\"}"
```

Важно: OpenAI ключ остается только на backend стороне (env/config) и не передается во frontend.

## Demo without OpenAI

Проект поддерживает стабильный локальный режим для VM/окружений без доступа к OpenAI API.

- Установите `OPENAI_ENABLED=false` в `.env`.
- В этом режиме OpenAI полностью пропускается, даже если `OPENAI_API_KEY` заполнен.
- `POST /api/demo/messages` продолжает работать через локальную логику:
  - catalog-backed рекомендации;
  - шаблоны `ResponseBuilder`;
  - FAQ/keyword fallback.
- Backend логирует тип исключения и traceback при ошибках внешнего AI, но API не отдает сырые provider errors во frontend.

Пример `.env` для офлайн-демо:

```env
ENABLE_TELEGRAM=false
ENABLE_WEB_API=true
OPENAI_ENABLED=false
WEB_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
WEB_HOST=0.0.0.0
WEB_PORT=8000
```

## Deploy behind nginx

Минимальная схема деплоя для `anniland-web`:

1. FastAPI demo API запускается отдельно (`python -m table_sales_assistant.main_api`) на внутреннем адресе, например `127.0.0.1:8000`.
2. В `.env` укажите production CORS:
   - `WEB_ALLOWED_ORIGINS=https://anniland.ru,https://www.anniland.ru`
3. Nginx проксирует API на backend:

```nginx
location /api/demo/ {
    proxy_pass http://127.0.0.1:8000/api/demo/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

4. Frontend `anniland-web` ходит только в `https://anniland.ru/api/demo/*`, без прямого доступа к внутреннему порту FastAPI.

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

## Demo data import

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

Быстрая проверка качества локальной demo DB:

```bash
python scripts/inspect_demo_db.py --db-path data/private/stolstoya_demo.sqlite
```

Команда показывает:
- количество товаров по категориям;
- количество knowledge docs по типам;
- примеры `adjustable_desk` и `accessory`;
- товары без цены, unknown, подозрительные записи;
- дубликаты `source_url`.

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