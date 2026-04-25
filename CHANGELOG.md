# Changelog

## [0.4.8] - 2026-04-26

- Fixed guided flow predictability: free-text parsing no longer auto-skips monitors/PC/size, so recommendation starts only after explicit answers or explicit skip phrases on those steps.
- Updated cheaper intent UX: "дешевле" without a budget now asks for a new budget and sets waiting state, while inline/follow-up budget replies recalculate recommendations without restarting the scenario.
- Expanded regression coverage for guided step order, cheaper follow-up budget flow, parser edge phrases (size/PC/scenario/budget), synced `docs/data_model.md` with actual context model fields, and added manual UX checklist scenarios.

## [0.4.7] - 2026-04-26

- Reworked recommendation UX to a unified guided flow for Telegram and Web API (`scenario -> height -> budget -> monitors -> pc_on_desk -> size`) with smarter step-aware free-text parsing.
- Upgraded recommendation logic with scenario-tag mapping, stronger monitor/PC/size/height scoring, budget range handling, and +15% stretch fallback marked as tradeoff instead of silent hard filtering.
- Added post-recommendation intent handling (cheaper/premium/clarify/switch scenario-size-budget), Russian scenario labels in user-facing texts, refreshed quick replies/copy, and expanded regression coverage including dedicated parser tests.

## [0.4.6] - 2026-04-26

- Restored compatibility fields in OpenAI technical logs by writing `question` and `answer` for `openai_request`/`openai_response` events while keeping structured internals in `extra`.

## [0.4.5] - 2026-04-26

- Aligned dialogue audit format with admin analytics contract by introducing explicit `event_type` values (`user_message_received`, `assistant_response_sent`) and writing separate user/assistant events in Telegram and Web API flows.
- Prevented technical OpenAI prompt context from polluting dialogue fields in JSONL by moving request/response internals to structured `extra` payload fields.

## [0.4.4] - 2026-04-25

- Fixed audit mode detection to reflect the real response generation path: `openai` only when a concrete reply actually used LLM output, `offline` for rule-based/fallback responses, and `unknown` when usage cannot be determined.
- Removed hardcoded OpenAI model values from runtime audit integration by introducing `OPENAI_MODEL` config and wiring model selection through `Settings`/`OpenAIClient`.
- Hardened audit JSONL readers: `read_recent()` and `export_events_as_json()` now skip empty/corrupted lines with warning logs instead of raising, with new regression tests for corrupted JSONL records.

## [0.4.3] - 2026-04-25

- Added dedicated dialogue audit backend module (`audit`) with structured event model, append-only JSONL repository, and fail-safe service API for `read_recent()` / `export_events_as_json()`.
- Added privacy-first sanitization for dialogue text in audit logs (phone/email masking), plus `AI_DIALOGUE_LOG_ENABLED` and `AI_DIALOGUE_LOG_PATH` config/env wiring with default path `data/private/ai_dialogue_events.jsonl`.
- Integrated success/error audit events with `latency_ms` into Telegram free-text flow and Web API `/api/demo/messages`, including mode detection (`openai` / `offline` / `yandex_ai` / `unknown`), intent, recommended products, and lead-aware logging.
- Added regression tests for JSONL persistence, valid JSON lines, `read_recent(limit)`, sanitize behavior, fail-safe write errors, and mode detection.

## [0.4.2] - 2026-04-25

- Hardened `/api/demo/messages` against OpenAI/network failures: added stable route-level exception fallback with sanitized user-facing text while preserving backend traceback logging.
- Added explicit `OPENAI_ENABLED` config flag and wired service construction so demo can run fully local mode even when API key exists.
- Improved OpenAI resilience and test coverage: AI client now catches provider exceptions with structured error logging, explanation flow always degrades to deterministic text, and API tests verify no-500/no-leak behavior.

## [0.4.1] - 2026-04-25

- Reduced repetitive phrasing in recommendation responses by moving monitor caveats to a single intro note and removing duplicated template labels (`Ограничения`, `Уверенность`) from every suggested item.
- Made dialogue responses more natural by dropping hardcoded `Следующий шаг`/filler tails from recommendation, comparison, FAQ, and no-exact-match templates while keeping CTAs in quick replies.
- Cleaned FAQ output formatting to avoid leaking knowledge article slugs/headings into user-visible answers and updated dialogue tests to match the new response style.
- Added `.gitignore` rule for local VM log exports (`vm-logs-*/`) to keep temporary diagnostic dumps out of commits.

## [0.4.0] - 2026-04-25

- Added optional FastAPI demo transport (`/api/demo/*`) with in-memory web sessions, Pydantic API schemas, and endpoint coverage for health, sessions, messages, and lead creation while reusing existing assistant services.
- Extracted shared service composition into `app_factory` so Telegram and Web API use the same dialogue/recommendation/lead pipeline without duplicating assistant logic.
- Added transport flags and runtime split (`ENABLE_TELEGRAM`, `ENABLE_WEB_API`, `WEB_ALLOWED_ORIGINS`, `main_api.py`), updated README with Web API usage examples, and kept Telegram transport behavior intact.
- Polished FastAPI demo transport before web integration: added optional manager notification in `/api/demo/leads`, introduced `WEB_HOST`/`WEB_PORT`, documented local/production CORS examples, added TTL cleanup for in-memory web sessions, and expanded API regression tests for invalid sessions and manager summary.

## [0.3.9] - 2026-04-25

- Improved consultative dialogue quality with reusable response templates for recommendations, contextual FAQ answers, comparison replies, and no-exact-match fallback scenarios with clear CTAs.
- Added richer manager handoff summary content in notifications (known client parameters, recommended option, unresolved question/objection, and suggested manager next step) and expanded regression tests for these flows.
- Updated demo script/checklist examples to reflect the new response format and refreshed sample catalog/test coverage for the current demo scenarios.
- Fixed Ruff/CI formatting issue in comparison response text assembly in `dialogue_service` without changing recommendation behavior.
- Added explicit GitHub Actions workflow permissions (`contents: read`) in CI to satisfy least-privilege checks and remove CodeQL warning.

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