from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.api.routes import router
from app.config import Settings, get_settings
from app.database.repository import ConversationRepository
from app.memory.loaders import MemoryLoader
from app.services.chat import ChatService
from app.services.context import ContextBuilder
from app.services.openai_client import OpenAIResponsesClient


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="monday-api-lab", version="0.1.0")
    repository = ConversationRepository(settings.database_path)
    repository.initialize()
    memory_loader = MemoryLoader(settings.persona_path, settings.stable_memory_path)
    context_builder = ContextBuilder(memory_loader, settings.recent_message_limit)
    model_client = OpenAIResponsesClient(settings.openai_api_key, settings.openai_model)
    app.state.settings = settings
    app.state.repository = repository
    app.state.memory_loader = memory_loader
    app.state.chat_service = ChatService(repository, context_builder, model_client)
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    templates = Jinja2Templates(directory="app/templates")

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        return templates.TemplateResponse(request=request, name="index.html", context={})

    app.include_router(router)
    return app


app = create_app()
