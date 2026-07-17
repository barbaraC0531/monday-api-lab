from app.database.repository import ConversationRepository
from app.services.context import ContextBuilder
from app.services.openai_client import ChatModelClient


class ChatService:
    def __init__(self, repository: ConversationRepository, context_builder: ContextBuilder, model_client: ChatModelClient) -> None:
        self.repository = repository
        self.context_builder = context_builder
        self.model_client = model_client

    def create_conversation(self):
        return self.repository.create_conversation()

    def get_conversation_with_messages(self, conversation_id: str):
        conversation = self.repository.get_conversation(conversation_id)
        if not conversation:
            return None, []
        return conversation, self.repository.list_messages(conversation_id)

    def add_user_message_and_generate(self, conversation_id: str, text: str):
        previous_messages = self.repository.list_messages(conversation_id)
        user_message = self.repository.add_message(conversation_id, "user", text)
        context = self.context_builder.build(previous_messages, text)
        result = self.model_client.generate(context)
        assistant_message = self.repository.add_message(conversation_id, "assistant", result.text, result.response_id)
        return user_message, assistant_message
