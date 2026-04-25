# Модель данных

## Структура товара

- id
- name
- category
- segment
- price
- min_height_cm
- max_height_cm
- tabletop_width_cm
- tabletop_depth_cm
- motors_count
- lifting_capacity_kg
- material
- colors
- use_cases
- recommended_user_height_min_cm
- recommended_user_height_max_cm
- product_url
- in_stock
- short_description

## Структура лида

- id
- created_at
- name
- phone
- city
- height_cm
- budget
- use_case
- monitors_count
- has_pc_case
- preferred_size
- needs_delivery
- needs_assembly
- recommended_products
- comment
- source

## Session context (диалог)

- `DialogueContext`
  - `known_params`: накопленные параметры клиента.
  - `collection_answered`: какие шаги уже подтверждены пользователем.
  - `recommended_products`: база для post-recommendation интентов (`compare`, `cheaper`, `change_*`).
  - `guide_active`: признак активного пошагового guided flow.
  - `awaiting_budget_after_cheaper`: ожидание нового бюджета после запроса "дешевле".
  - `low_budget_warned`: флаг, что уже показывали уточнение по слишком низкому бюджету.
  - `recent_questions`, `recent_messages`: краткая история для контекста и handoff.
  - `dialogue_goal`, `lead_readiness`, `manager_summary`: служебные поля состояния диалога.

- `KnownClientParams` (ключевые поля)
  - `use_case`, `height_cm`, `monitors_count`, `has_pc_case`.
  - `budget_min`, `budget_max`, `budget_exact_rub`, `budget_unspecified`.
  - `max_width_cm`, `max_depth_cm`, `preferred_width_cm`, `preferred_depth_cm`, `no_size_limit`.
  - `heavy_setup`, `preferred_size`, `city`, `needs_assembly`.
  - Флаги explicit skip: `height_unspecified`, `monitors_unspecified`, `pc_unspecified`, `size_unspecified`.

Эти поля сериализуются в `known_params` и используются и в Telegram, и в Web API сессиях.

## Примечание

Все данные в текущем репозитории являются демонстрационными sample-данными.