from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.models.schemas import (
    ConversationCreateResponse,
    ConversationResponse,
    HealthResponse,
    MemoryStatusResponse,
    MessageCreateRequest,
    MessageCreateResponse,
    MessageResponse,
)
from app.services.chat import ChatService
from app.services.openai_client import ModelConfigurationError

router = APIRouter()


def record_to_message(record) -> MessageResponse:
    return MessageResponse(**record.__dict__)


def get_chat_service(request: Request) -> ChatService:
    return request.app.state.chat_service


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    return HealthResponse(status="ok", model_configured=request.app.state.settings.has_openai_api_key)


@router.post("/api/conversations", response_model=ConversationCreateResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(chat: ChatService = Depends(get_chat_service)) -> ConversationCreateResponse:
    return ConversationCreateResponse(**chat.create_conversation().__dict__)


@router.get("/api/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: str, chat: ChatService = Depends(get_chat_service)) -> ConversationResponse:
    conversation, messages = chat.get_conversation_with_messages(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse(
        conversation_id=conversation.conversation_id,
        created_at=conversation.created_at,
        messages=[record_to_message(m) for m in messages],
    )


@router.post("/api/conversations/{conversation_id}/messages", response_model=MessageCreateResponse)
def add_message(conversation_id: str, payload: MessageCreateRequest, chat: ChatService = Depends(get_chat_service)) -> MessageCreateResponse:
    if not chat.repository.get_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    try:
        user_message, assistant_message = chat.add_user_message_and_generate(conversation_id, payload.text)
    except ModelConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return MessageCreateResponse(user_message=record_to_message(user_message), assistant_message=record_to_message(assistant_message))


@router.get("/api/memory/status", response_model=MemoryStatusResponse)
def memory_status(request: Request) -> MemoryStatusResponse:
    return MemoryStatusResponse(**request.app.state.memory_loader.status())
