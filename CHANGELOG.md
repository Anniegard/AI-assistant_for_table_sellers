# Changelog

## [0.3.9] - 2026-04-25

- Improved consultative dialogue quality with reusable response templates for recommendations, contextual FAQ answers, comparison replies, and no-exact-match fallback scenarios with clear CTAs.
- Added richer manager handoff summary content in notifications (known client parameters, recommended option, unresolved question/objection, and suggested manager next step) and expanded regression tests for these flows.
- Updated demo script/checklist examples to reflect the new response format and refreshed sample catalog/test coverage for the current demo scenarios.

## [0.3.8] - 2026-04-25

- Ran the StolStoya ingestion scenario into local demo SQLite (`data/private/stolstoya_demo.sqlite`) and verified imported catalog/knowledge records with the DB inspection script.
- Added an explicit `.gitignore` rule for `data/private/stolstoya_demo.sqlite` so local demo data stays untracked without altering already tracked files on GitHub.

## [0.3.7] - 2026-04-25

- Improved sales tone in no-result/FAQ fallbacks: responses now stay consultative, suggest nearby options, and gently guide users to manager handoff when needed.
- Simplified guided recommendation flow by removing mandatory `use_case` input from the FSM path: if scenario is unknown, selection continues without this filter.
- Updated demo docs formatting and checklist wording to match the refreshed conversation flow and presentation narrative.

## [0.3.6] - 2026-04-24

- Stabilized demo-MVP recommendation flow: fixed SQLite user-height mapping (technical range is no longer treated as user height), enforced desk-only selection boundaries, improved strict-budget/cheaper handling, and added context-based compare responses.
- Improved FAQ/import tooling for demo safety: added stronger FAQ fallback answers, extended StolStoya import report warnings, introduced `scripts/inspect_demo_db.py`, and refreshed demo docs for SQLite import/inspection workflow and disclaimers.
- Expanded regression coverage for height filtering, strict budget behavior, compare/intent/accessory flows, importer category/report checks, and inspect CLI output.
- Improved StolStoya crawl routing for real imports: broadened catalog-like URL discovery, filtered irrelevant/system links, and reduced false knowledge classification on catalog paths.

## [0.3.5] - 2026-04-24

- Added optional SQLite backends for catalog and knowledge with env-driven runtime switching (`CATALOG_BACKEND`, `KNOWLEDGE_BACKEND`) and explicit fail-fast behavior when DB files are missing.
- Added local StolStoya demo importer CLI with normalization/parsing utilities, SQLite schema/storage layer, import run reporting, and strict `.gitignore` rules to keep scraped data out of GitHub.
- Updated recommendation/FAQ behavior and expanded test coverage with synthetic fixtures for importer parsing, SQLite repositories, category guards, and normalization helpers.
- Fixed `scripts/ingest_stolstoya.py` startup so it resolves `src` automatically and runs without manual `PYTHONPATH` setup.
- Improved importer dry-run stability: removed brittle seed paths, added safer link discovery/routing (`listing` vs `product`), reduced false `chair` categorization, and added routing regression tests.

## [0.3.4] - 2026-04-24

- Fixed desk recommendation boundaries: main подбор now excludes accessories by default, enforces strict budget matching, and only uses above-budget fallback when no in-budget desk exists.
- Added dedicated cheaper-flow recalculation in free-text dialogue to avoid repeating previous products and return only truly cheaper desk options (or an explicit no-cheaper message).
- Split accessory vs desk behavior in wording/explanations, added accessory intent handling, and expanded regression tests for category filtering, strict budget, cheaper requests, and accessory explanation safety.

## [0.3.3] - 2026-04-24

- Fixed free-text budget parsing for compact and conversational formats (`50к`, `50 тыс`, `до 50 000`, `50000 рублей`) including combined parameter messages.
- Reworked intent priority to route FAQ questions (especially motor-related) before repeated missing-parameter prompts, while keeping FSM button flows intact.
- Improved dialogue recommendation/lead behavior: smart missing-param prompts, monitor fallback as non-blocking with explicit preliminary note, and context-aware motor FAQ + lead handoff context reuse.

## [0.3.2] - 2026-04-24

- Added session memory for free-text dialogue: recent message history, context summary, and parameter accumulation across Telegram messages.
- Improved dialogue behavior for incomplete inputs by making budget/height required, using a monitor-count fallback, and preserving natural FAQ/recommendation transitions.
- Extended lead handoff with known client parameters and dialogue summary for manager context, and updated tests/docs for the new conversational flow.

## [0.3.1] - 2026-04-24

- Added structured observability for dialogue flow: function-level phases, user/bot identifiers, and response trace points in Telegram handlers.
- Added JSONL event sink `data/dialogue_events.jsonl` with fields `question`, `answer`, `user_id`, `lead_id`, `phase`, and extra metadata.
- Added OpenAI request/response logging (including latency and fallback-disabled mode) for easier runtime diagnostics.
- Updated `.gitignore` to exclude local dialogue event logs from repository history.

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