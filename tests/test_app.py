import sqlite3
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


def test_homepage_returns_ok(tmp_path):
    client = TestClient(create_app(settings(tmp_path)))
    res = client.get("/")
    assert res.status_code == 200


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


def test_context_hides_audit_claim_ids_without_modifying_memory_files(tmp_path: Path):
    persona = tmp_path / "persona.md"
    stable = tmp_path / "stable.md"
    persona_text = (
        "# Persona\n"
        "- [P-001] Persona content remains available.\n"
        "- Ordinary [bracketed conversational text] remains intact.\n"
        "A non-leading [P-999] reference remains intact."
    )
    stable_text = (
        "# Stable Memory\n"
        "- [S-024] Stable-memory content remains available.\n"
        "- [C-030] Future continuity claims use the same presentation rule.\n"
        "- [X-001] Unapproved bracket tokens remain intact."
    )
    persona.write_text(persona_text, encoding="utf-8")
    stable.write_text(stable_text, encoding="utf-8")
    cfg = Settings(
        OPENAI_API_KEY=None,
        DATABASE_PATH=tmp_path / "test.db",
        persona_path=persona,
        stable_memory_path=stable,
    )

    context = ContextBuilder(MemoryLoader(cfg.persona_path, cfg.stable_memory_path)).build([], "hello")
    system_content = context[0]["content"]

    assert "Persona content remains available." in system_content
    assert "Stable-memory content remains available." in system_content
    assert "[P-001]" not in system_content
    assert "[S-024]" not in system_content
    assert "[C-030]" not in system_content
    assert "[bracketed conversational text]" in system_content
    assert "A non-leading [P-999] reference remains intact." in system_content
    assert "[X-001] Unapproved bracket tokens remain intact." in system_content
    assert persona.read_text(encoding="utf-8") == persona_text
    assert stable.read_text(encoding="utf-8") == stable_text


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


class FailingModelClient:
    def generate(self, messages):
        raise RuntimeError("model failure")


def test_failed_model_call_does_not_persist_either_message(tmp_path):
    app = create_app(settings(tmp_path))
    app.state.chat_service.model_client = FailingModelClient()
    conversation = app.state.repository.create_conversation()

    try:
        app.state.chat_service.add_user_message_and_generate(conversation.conversation_id, "do not save")
    except RuntimeError as exc:
        assert str(exc) == "model failure"
    else:
        raise AssertionError("Expected model failure")

    assert app.state.repository.list_messages(conversation.conversation_id) == []


def test_successful_user_assistant_turn_is_stored_together(tmp_path):
    app = create_app(settings(tmp_path))
    app.state.chat_service.model_client = FakeModelClient("saved assistant")
    conversation = app.state.repository.create_conversation()

    user_message, assistant_message = app.state.chat_service.add_user_message_and_generate(conversation.conversation_id, "save user")

    messages = app.state.repository.list_messages(conversation.conversation_id)
    assert messages == [user_message, assistant_message]
    assert [message.role for message in messages] == ["user", "assistant"]
    assert [message.text for message in messages] == ["save user", "saved assistant"]


def test_limited_message_retrieval_returns_newest_messages_chronologically(tmp_path):
    app = create_app(settings(tmp_path))
    repo = app.state.repository
    conversation = repo.create_conversation()
    for index in range(5):
        repo.add_message(conversation.conversation_id, "user", f"message-{index}")

    messages = repo.list_messages(conversation.conversation_id, limit=3)

    assert [message.text for message in messages] == ["message-2", "message-3", "message-4"]


def test_orphan_messages_are_rejected(tmp_path):
    app = create_app(settings(tmp_path))
    repo = app.state.repository

    try:
        repo.add_message("missing-conversation", "user", "orphan")
    except sqlite3.IntegrityError as exc:
        assert "FOREIGN KEY constraint failed" in str(exc)
    else:
        raise AssertionError("Expected orphan message insert to fail")
