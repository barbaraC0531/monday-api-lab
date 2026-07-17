from datetime import datetime
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    model_configured: bool


class ConversationCreateResponse(BaseModel):
    conversation_id: str
    created_at: datetime


class MessageResponse(BaseModel):
    message_id: str
    role: str
    text: str
    created_at: datetime
    model_response_id: str | None = None


class ConversationResponse(BaseModel):
    conversation_id: str
    created_at: datetime
    messages: list[MessageResponse]


class MessageCreateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)


class MessageCreateResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse


class MemoryStatusResponse(BaseModel):
    persona_path: str
    persona_loaded: bool
    stable_memory_path: str
    stable_memory_loaded: bool
