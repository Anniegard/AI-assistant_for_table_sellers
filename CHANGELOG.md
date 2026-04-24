# Changelog

## [0.3.0] - 2026-04-24

- Introduced `ЭргоАссистент` business layer (`assistant`) with intent routing, free-text parameter extraction, and dialogue orchestration decoupled from Telegram handlers.
- Upgraded catalog recommendation to hard-filter + soft-scoring output (`fit_score`, reasons, tradeoffs, best-for) and wired ranked recommendations into dialogue responses.
- Expanded Telegram UX with conversational quick actions (`Задать вопрос`, `Сравнить варианты`, `Почему этот стол?`, `Есть дешевле?`, `Позвать менеджера`, reset/cancel flows).
- Enhanced lead handoff payload for manager with recent user questions, selected recommendation, and assistant comment.
- Updated README/architecture docs and added focused tests for intents, dialogue free-text handling, scoring, fallback without OpenAI, no-hallucination guard, and handoff summary.

## [0.2.1] - 2026-04-24

- QA hardening before client demo: improved Telegram flow stability and clearer startup error when `TELEGRAM_BOT_TOKEN` is missing.
- Polished recommendation UX with human-readable scenario prompts and mapping to internal `use_case` values.
- Added reliable recommendation-to-lead handoff with shortcut action `Оставить заявку по этим вариантам` and reduced post-recommendation lead form.
- Improved manager notification readability and safe skip logging when `MANAGER_TELEGRAM_CHAT_ID` is not configured.
- Hardened FAQ keyword search for Russian phrasing and expanded tests for menu, FAQ, lead recommendation carry-over, and notification output.
- Added source-available licensing terms in `LICENSE` and clarified non-commercial usage in `README.md`.

## [0.2.0] - 2026-04-24

- Implemented Telegram MVP flow: `/start`, main menu, recommendation dialogue, FAQ, lead collection, and demo mode.
- Added AI explanation layer with offline-safe deterministic fallback.
- Added lead services, manager notification via Telegram, and manager-friendly lead formatting.
- Added tests for bot menu, FAQ service, AI fallback, lead repository/service, and manager notification.
- Packaged demo docs: checklist, client pitch, stage 5 packaging, screenshots plan, and screencast script.

## [0.1.0] - 2026-04-24

- Initial foundation for AI-assistant for table sellers MVP.
- Added repository structure, documentation skeleton, Python package scaffold, sample data, tests, and CI.