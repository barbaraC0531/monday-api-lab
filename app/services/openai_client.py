from dataclasses import dataclass
from typing import Protocol

from openai import OpenAI


class ModelConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class ModelResult:
    text: str
    response_id: str | None = None


class ChatModelClient(Protocol):
    def generate(self, messages: list[dict[str, str]]) -> ModelResult: ...


class OpenAIResponsesClient:
    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self._client = OpenAI(api_key=api_key) if api_key else None

    def generate(self, messages: list[dict[str, str]]) -> ModelResult:
        if self._client is None:
            raise ModelConfigurationError("OPENAI_API_KEY is not configured. Add it to your local .env file to call the model.")
        response = self._client.responses.create(model=self.model, input=messages)
        return ModelResult(text=response.output_text, response_id=response.id)


class FakeModelClient:
    def __init__(self, text: str = "Fake Monday response.") -> None:
        self.text = text

    def generate(self, messages: list[dict[str, str]]) -> ModelResult:
        return ModelResult(text=self.text, response_id="fake-response-id")
