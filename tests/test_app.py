from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.memory.loaders import MemoryLoader
from app.services.context import ContextBuilder
from app.services.openai_client import FakeModelClient


def settings(tmp_path: Path) -> Settings:
    persona = tmp_path / "persona.md"
    stable = tmp_path / "stable.md"
    persona.write_text("Persona text", encoding="utf-8")
    stable.write_text("Stable memory", encoding="utf-8")
    return Settings(
        OPENAI_API_KEY=None,
        DATABASE_PATH=tmp_path / "test.db",
        persona_path=persona,
        stable_memory_path=stable,
    )


def client_with_fake(tmp_path: Path) -> TestClient:
    app = create_app(settings(tmp_path))
    app.state.chat_service.model_client = FakeModelClient("fake response")
    return TestClient(app)


def test_configuration_defaults(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CALL_MODEL_ON_TOUCH", raising=False)
    cfg = Settings(_env_file=None)
    assert cfg.openai_api_key is None
    assert cfg.call_model_on_touch is False


def test_startup_without_api_key(tmp_path):
    client = TestClient(create_app(settings(tmp_path)))
    assert client.get("/health").json() == {"status": "ok", "model_configured": False}


def test_memory_loading(tmp_path):
    cfg = settings(tmp_path)
    loader = MemoryLoader(cfg.persona_path, cfg.stable_memory_path)
    assert loader.load_persona() == "Persona text"
    assert loader.load_stable_memory() == "Stable memory"
    assert loader.status()["persona_loaded"] is True


def test_conversation_creation_and_message_persistence(tmp_path):
    client = client_with_fake(tmp_path)
    conversation_id = client.post("/api/conversations").json()["conversation_id"]
    res = client.post(f"/api/conversations/{conversation_id}/messages", json={"text": "hello"})
    assert res.status_code == 200
    data = client.get(f"/api/conversations/{conversation_id}").json()
    assert [m["role"] for m in data["messages"]] == ["user", "assistant"]
    assert data["messages"][1]["text"] == "fake response"


def test_context_construction(tmp_path):
    cfg = settings(tmp_path)
    app = create_app(cfg)
    repo = app.state.repository
    conv = repo.create_conversation()
    repo.add_message(conv.conversation_id, "user", "old")
    builder = ContextBuilder(MemoryLoader(cfg.persona_path, cfg.stable_memory_path), recent_message_limit=5)
    context = builder.build(repo.list_messages(conv.conversation_id), "new")
    assert context[0]["role"] == "system"
    assert "Persona text" in context[0]["content"]
    assert "Stable memory" in context[0]["content"]
    assert context[-1] == {"role": "user", "content": "new"}


def test_fake_model_responses():
    result = FakeModelClient("deterministic").generate([])
    assert result.text == "deterministic"
    assert result.response_id == "fake-response-id"


def test_api_error_handling_for_missing_conversation(tmp_path):
    client = client_with_fake(tmp_path)
    res = client.get("/api/conversations/not-real")
    assert res.status_code == 404
    assert res.json()["detail"] == "Conversation not found"


def test_api_error_handling_for_missing_key(tmp_path):
    client = TestClient(create_app(settings(tmp_path)))
    conversation_id = client.post("/api/conversations").json()["conversation_id"]
    res = client.post(f"/api/conversations/{conversation_id}/messages", json={"text": "hello"})
    assert res.status_code == 503
    assert "OPENAI_API_KEY" in res.json()["detail"]
