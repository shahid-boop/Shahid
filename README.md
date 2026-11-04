# Shahid Assistant — Windows 11

This is the **diagram-first implementation branch**. It starts from the repository's clean `main` branch and adds a modular Python foundation. The original `main` branch and the earlier `architecture-foundation` branch are left unchanged.

## Foundation modules implemented

- `main.py`: CLI, desktop UI and dashboard entry point
- `ui.py`: Tkinter desktop chat HUD
- `server.py`: browser dashboard and JSON chat endpoint, bound to loopback only
- `engine_pipeline.py`: provider boundary for OpenAI-compatible chat APIs
- `config_manager.py`: environment configuration and local `.env` loading
- `memory_manager.py`: bounded, persistent local conversation history
- `skills/registry.py`: explicit allowlist for local skills
- `tests/test_foundation.py`: unit tests for memory, configuration and skill registration

The original diagram remains in `diagram.png`. This first coding pass establishes the core runtime and UI/dashboard paths. Gemini Live audio, speech recognition/TTS, Windows computer-control skills, the complete animated HUD and hardware validation are **not yet complete** and are not claimed as complete.

## Requirements

- Windows 11
- Python 3.11 or later
- An API key for an OpenAI-compatible provider to use AI chat

## Setup

In PowerShell, from the repository folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
# Edit .env and set OPENAI_API_KEY
python -m unittest discover -s tests -v
python main.py --ui
```

For the browser dashboard:

```powershell
python main.py --server
```

Then open http://127.0.0.1:8765. The dashboard intentionally refuses non-loopback binding. Never commit a real API key or the local `.env` file.

For terminal chat run `python main.py --chat` (or simply `python main.py`).

## Security and limitations

- The dashboard binds only to loopback and does not expose configuration or credentials.
- Skills run only when explicitly registered. No arbitrary plugin imports or code execution are enabled.
- Conversation history is stored locally in `data/conversations.json`; use `/clear` in CLI to clear the default conversation.
- Provider chat currently supports OpenAI-compatible `/chat/completions` APIs. Gemini Live and audio providers are follow-up work.
- Do not commit API keys or share your local `.env` file.

## Validation status

Unit tests are included and a GitHub Actions workflow runs compilation and tests on Windows. A passing CI run does not replace testing on the actual target PC. This environment has not tested the user's physical microphone, speakers, webcam, Windows automation or provider credentials.
