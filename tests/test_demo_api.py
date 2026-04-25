import json
from pathlib import Path

from fastapi.testclient import TestClient

from table_sales_assistant.api.app import create_app
from table_sales_assistant.api.session_store import InMemoryWebSessionStore
from table_sales_assistant.app_factory import build_app_services
from table_sales_assistant.config import Settings


def _build_client(tmp_path: Path) -> tuple[TestClient, Path]:
    leads_path = tmp_path / "leads.test.json"
    settings = Settings(
        ENABLE_WEB_API=True,
        ENABLE_TELEGRAM=False,
        OPENAI_API_KEY="",
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
