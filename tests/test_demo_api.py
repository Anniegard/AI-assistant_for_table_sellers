import json
from pathlib import Path

from fastapi.testclient import TestClient

from table_sales_assistant.api.app import create_app
from table_sales_assistant.api.session_store import InMemoryWebSessionStore
from table_sales_assistant.app_factory import build_app_services
from table_sales_assistant.config import Settings


def _build_client(
    tmp_path: Path,
    *,
    openai_enabled: bool = True,
    openai_api_key: str = "",
) -> tuple[TestClient, Path]:
    leads_path = tmp_path / "leads.test.json"
    settings = Settings(
        ENABLE_WEB_API=True,
        ENABLE_TELEGRAM=False,
        OPENAI_ENABLED=openai_enabled,
        OPENAI_API_KEY=openai_api_key,
        PRODUCTS_PATH="data/products.sample.json",
        KNOWLEDGE_DIR="data/knowledge",
        LEADS_PATH=str(leads_path),
        WEB_ALLOWED_ORIGINS="*",
    )
    services = build_app_services(settings)
    app = create_app(settings=settings, services=services, session_store=InMemoryWebSessionStore())
    return TestClient(app), leads_path


def test_demo_health(tmp_path: Path) -> None:
    with _build_client(tmp_path)[0] as client:
        response = client.get("/api/demo/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["mode"] == "demo"


def test_demo_create_session(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    with client:
        response = client.post("/api/demo/sessions")
    assert response.status_code == 201
    payload = response.json()
    assert isinstance(payload["session_id"], str)
    assert payload["session_id"].startswith("web-")


def test_demo_message_flow_returns_required_fields(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    with client:
        session_response = client.post("/api/demo/sessions")
        session_id = session_response.json()["session_id"]
        response = client.post(
            "/api/demo/messages",
            json={"session_id": session_id, "text": "рост 190 бюджет 50000 для дома"},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["assistant_text"]
    assert payload["intent"]
    assert isinstance(payload["quick_replies"], list)
    assert isinstance(payload["recommended_products"], list)
    assert "lead_state" in payload
    assert isinstance(payload["lead_state"]["known_params"], dict)


def test_demo_messages_openai_disabled_returns_recommendation(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path, openai_enabled=False)
    with client:
        session_id = client.post("/api/demo/sessions").json()["session_id"]
        response = client.post(
            "/api/demo/messages",
            json={
                "session_id": session_id,
                "text": "Мне нужен стол до 70000, рост 185, два монитора, только ноутбук, 140x70",
            },
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["assistant_text"]
    assert payload["intent"]
    assert isinstance(payload["recommended_products"], list)
    assert payload["recommended_products"]


def test_demo_messages_openai_failure_returns_stable_fallback(tmp_path: Path, monkeypatch) -> None:
    client, _ = _build_client(tmp_path, openai_enabled=True, openai_api_key="test-key")
    with client:
        session_id = client.post("/api/demo/sessions").json()["session_id"]
        openai_client = client.app.state.services.explanation_service.ai_client

        def _raise_provider_error(*args, **kwargs):
            raise RuntimeError("OpenAI upstream timeout: 504 gateway")

        monkeypatch.setattr(openai_client, "simple_chat", _raise_provider_error)
        response = client.post(
            "/api/demo/messages",
            json={
                "session_id": session_id,
                "text": "рост 185 бюджет 70000 два монитора только ноутбук 140x70",
            },
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["assistant_text"]
    assert "OpenAI" not in payload["assistant_text"]
    assert "timeout" not in payload["assistant_text"].lower()
    assert isinstance(payload["recommended_products"], list)
    assert payload["recommended_products"]


def test_demo_messages_unhandled_error_is_sanitized(tmp_path: Path, monkeypatch) -> None:
    client, _ = _build_client(tmp_path)
    with client:
        session_id = client.post("/api/demo/sessions").json()["session_id"]

        def _raise_unhandled(*args, **kwargs):
            raise RuntimeError("OpenAI AuthError: invalid_api_key")

        monkeypatch.setattr(client.app.state.services.dialogue_service, "handle", _raise_unhandled)
        response = client.post(
            "/api/demo/messages",
            json={"session_id": session_id, "text": "помоги выбрать стол"},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "fallback"
    assert "OpenAI" not in payload["assistant_text"]
    assert "invalid_api_key" not in payload["assistant_text"]


def test_demo_messages_invalid_session_returns_404(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    with client:
        response = client.post(
            "/api/demo/messages",
            json={"session_id": "web-missing", "text": "привет"},
        )
    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


def test_demo_lead_creation_persists_lead(tmp_path: Path) -> None:
    client, leads_path = _build_client(tmp_path)
    with client:
        session_id = client.post("/api/demo/sessions").json()["session_id"]
        client.post(
            "/api/demo/messages",
            json={"session_id": session_id, "text": "рост 185 бюджет 80000 для дома"},
        )
        response = client.post(
            "/api/demo/leads",
            json={
                "session_id": session_id,
                "name": "Иван",
                "phone": "+79991234567",
                "city": "Москва",
                "comment": "Свяжитесь после 18:00",
            },
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["lead_id"]
    assert payload["source"] == "web_demo"
    assert isinstance(payload["manager_summary"], str)
    assert payload["manager_summary"].strip()

    saved = json.loads(leads_path.read_text(encoding="utf-8"))
    assert len(saved) == 1
    assert saved[0]["source"] == "web_demo"


def test_demo_leads_invalid_session_returns_404(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)
    with client:
        response = client.post(
            "/api/demo/leads",
            json={
                "session_id": "web-missing",
                "name": "Иван",
                "phone": "+79991234567",
                "city": "Москва",
            },
        )
    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


def _post_message(client: TestClient, session_id: str, text: str) -> dict:
    response = client.post(
        "/api/demo/messages",
        json={"session_id": session_id, "text": text},
    )
    assert response.status_code == 200
    return response.json()


def test_demo_guided_happy_path_buttons_no_loop(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path, openai_enabled=False)
    with client:
        session_id = client.post("/api/demo/sessions").json()["session_id"]
        r1 = _post_message(client, session_id, "Для работы дома")
        assert r1["lead_state"]["current_step"] == "height"
        r2 = _post_message(client, session_id, "176-185 см")
        assert r2["lead_state"]["current_step"] == "budget"
        r3 = _post_message(client, session_id, "50 000-80 000 ₽")
        assert r3["lead_state"]["current_step"] == "monitors"
        r4 = _post_message(client, session_id, "2 монитора")
        assert r4["lead_state"]["current_step"] == "pc_desk"
        r5 = _post_message(client, session_id, "Нет")
        assert r5["lead_state"]["current_step"] == "size"
        r6 = _post_message(client, session_id, "120x60")
        assert r6["lead_state"]["current_step"] in {"city", "assembly", None}
        known = r6["lead_state"]["known_params"]
        assert known["use_case"] == "home_office"
        assert known["height_cm"] is not None
        assert known["budget_max"] is not None
        assert known["monitors_count"] == 2
        assert known["has_pc_case"] is False
        assert known["preferred_width_cm"] == 120


def test_demo_guided_happy_path_free_text_no_loop(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path, openai_enabled=False)
    with client:
        session_id = client.post("/api/demo/sessions").json()["session_id"]
        _post_message(client, session_id, "Для работы дома")
        _post_message(client, session_id, "178")
        _post_message(client, session_id, "50000")
        _post_message(client, session_id, "2")
        _post_message(client, session_id, "нет")
        r = _post_message(client, session_id, "120 см")
        assert r["lead_state"]["current_step"] in {"city", "assembly", None}
        known = r["lead_state"]["known_params"]
        assert known["height_cm"] == 178
        assert known["budget_max"] == 50000
        assert known["monitors_count"] == 2
        assert known["has_pc_case"] is False
        assert known["preferred_width_cm"] == 120


def test_demo_lead_flow_requires_required_fields(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path, openai_enabled=False)
    with client:
        session_id = client.post("/api/demo/sessions").json()["session_id"]
        r1 = _post_message(client, session_id, "Позвать менеджера")
        assert r1["lead_state"]["lead_step"] == "name"
        assert r1["manager_summary"] is None
        r2 = _post_message(client, session_id, "Иван")
        assert r2["lead_state"]["lead_step"] == "phone"
        assert r2["manager_summary"] is None
        r3 = _post_message(client, session_id, "+7 999 123 45")
        assert r3["lead_state"]["lead_step"] == "phone"
        assert r3["manager_summary"] is None
        r4 = _post_message(client, session_id, "+7 999 123 45 67")
        assert r4["lead_state"]["lead_step"] == "city"
        r5 = _post_message(client, session_id, "Москва")
        assert r5["lead_state"]["lead_step"] == "comment"
        r6 = _post_message(client, session_id, "нет")
        assert r6["lead_state"]["lead_ready"] is True
        assert r6["manager_summary"]
        assert "Заявка принята" in r6["assistant_text"]


def test_demo_restart_resets_full_context(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path, openai_enabled=False)
    with client:
        session_id = client.post("/api/demo/sessions").json()["session_id"]
        _post_message(client, session_id, "Для работы дома")
        _post_message(client, session_id, "178")
        _post_message(client, session_id, "50000")
        _post_message(client, session_id, "Позвать менеджера")
        _post_message(client, session_id, "Иван")
        restart = _post_message(client, session_id, "заново")
        known = restart["lead_state"]["known_params"]
        assert known["height_cm"] is None
        assert known["budget_max"] is None
        assert known["use_case"] is None
        assert restart["lead_state"]["current_step"] == "scenario"
        assert restart["lead_state"]["lead_step"] is None
        assert restart["manager_summary"] is None


def test_web_session_store_cleanup_keeps_active_sessions() -> None:
    now = [100.0]

    def fake_now() -> float:
        return now[0]

    store = InMemoryWebSessionStore(ttl_seconds=10, now_fn=fake_now)
    active = store.create()
    expired = store.create()

    now[0] = 105.0
    assert store.get(active.session_id) is not None

    now[0] = 111.0
    assert store.get(expired.session_id) is None
    assert store.get(active.session_id) is not None
