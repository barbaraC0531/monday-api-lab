# monday-api-lab Agent Instructions

- Never commit secrets, `.env` files, API keys, private ChatGPT archives, or real personal data.
- Preserve clear separation between persona instructions, stable memory, episodic conversation memory, and raw archives.
- Do not introduce automatic long-term-memory writing without explicit approval.
- Do not use the deprecated OpenAI Assistants API; use the OpenAI Responses API for model calls.
- Run tests after changes and keep the app runnable without an OpenAI API key.
- Prefer simple, replaceable components over premature infrastructure.
