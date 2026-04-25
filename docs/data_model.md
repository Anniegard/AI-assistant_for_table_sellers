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
  - `collection_step`: текущий шаг пошагового сбора.
  - `collection_answered`: какие шаги уже подтверждены пользователем.
  - `recommended_products` и `last_assistant_message`: база для пост-рекомендационных интентов.

- `KnownClientParams` (ключевые поля)
  - `use_case`, `height_cm`, `monitors_count`, `has_pc_case`.
  - `budget_min`, `budget_max`, `budget_unspecified`.
  - `max_width_cm`, `max_depth_cm`, `preferred_width_cm`, `preferred_depth_cm`, `no_size_limit`.
  - `stability_priority`, `heavy_setup`.

Эти поля сериализуются в `known_params` и используются и в Telegram, и в Web API сессиях.

## Примечание

Все данные в текущем репозитории являются демонстрационными sample-данными.