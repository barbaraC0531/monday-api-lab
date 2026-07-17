from app.database.repository import MessageRecord
from app.memory.loaders import MemoryLoader


class ContextBuilder:
    def __init__(self, memory_loader: MemoryLoader, recent_message_limit: int = 12) -> None:
        self.memory_loader = memory_loader
        self.recent_message_limit = recent_message_limit

    def build(self, recent_messages: list[MessageRecord], current_user_message: str) -> list[dict[str, str]]:
        persona = self.memory_loader.load_persona() or "You are Monday, a fictional local prototype assistant."
        stable_memory = self.memory_loader.load_stable_memory()
        instructions = ["# Persona Instructions", persona]
        if stable_memory:
            instructions.extend(["# Stable Memory", stable_memory])
        messages = [{"role": "system", "content": "\n\n".join(instructions)}]
        for msg in recent_messages[-self.recent_message_limit :]:
            messages.append({"role": msg.role, "content": msg.text})
        messages.append({"role": "user", "content": current_user_message})
        return messages
