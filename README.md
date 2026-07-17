# monday-api-lab

`monday-api-lab` is a private, local-first Python MVP for the software foundation of a future conversational AI persona named Monday. This repository intentionally contains only fictional example persona and memory content.

## Architecture

- **FastAPI app** in `app/main.py` serves JSON routes and a minimal HTML chat UI.
- **Configuration** in `app/config.py` reads `.env` values with safe defaults.
- **API routes** in `app/api/routes.py` expose health, conversation, message, and memory status endpoints.
- **SQLite repository** in `app/database/repository.py` stores conversations and messages behind a replaceable abstraction.
- **Memory loaders** in `app/memory/loaders.py` load persona and stable-memory Markdown without modifying them.
- **Context builder** in `app/services/context.py` combines persona, stable memory, recent messages, and the current user message.
- **Model clients** in `app/services/openai_client.py` wrap the official OpenAI SDK Responses API and provide a deterministic fake for tests.
- **Static UI** in `app/templates/` and `app/static/` provides a lightweight browser chat page.

## Windows local setup

Open PowerShell in the repository root.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` locally. Never commit `.env`.

```dotenv
OPENAI_API_KEY=your-local-key-if-you-want-model-calls
OPENAI_MODEL=gpt-4.1-mini
DATABASE_PATH=./monday_api_lab.db
CALL_MODEL_ON_TOUCH=false
```

The app starts without `OPENAI_API_KEY`; model-backed message submission returns a clear configuration error until a key is set.

## Running the server

```powershell
uvicorn app.main:app --reload
```

Then open <http://127.0.0.1:8000/>.

## Running tests

```powershell
pytest
```

Automated tests use fake model clients and must not make OpenAI API requests.

## Persona and memory files

- Commit only fictional examples: `memory/persona.example.md` and `memory/stable_memory.example.md`.
- Store private local files as `memory/persona.md` and `memory/stable_memory.md`.
- Do not commit raw private archives, exports, logs, or secrets.

## Files that must never be committed

- `.env`
- SQLite databases such as `*.db`, `*.sqlite`, and `*.sqlite3`
- `memory/persona.md`
- `memory/stable_memory.md`
- `memory/raw_archives/`
- private conversation archives or real personal data

## Current limitations

- No authentication; this is for local private use only.
- No automatic long-term memory writing.
- No archive import pipeline.
- Stable memory is included in full because the example file is small.
- Retrieval-based memory is not implemented yet.

## Planned future stages

1. Add retrieval-backed memory selection behind the context-builder interface.
2. Add explicit, reviewable memory curation tools.
3. Add richer local evaluation tests for persona behavior without private data.
4. Add optional deployment hardening only if the project stops being local-only.
