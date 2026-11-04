# Shahid Assistant — Windows 11

A modular Windows desktop assistant built from the supplied architecture diagram.

## Current implementation

- Conversation runtime with bounded recent context and local persistent transcript
- OpenAI-compatible chat provider (credentials supplied through environment variables)
- Tkinter desktop chat HUD with explicit push-to-talk recording
- OpenAI Whisper speech-to-text and OpenAI text-to-speech adapters
- Localhost-only dashboard API
- Skill and plugin registries
- Windows system health checks, allowlisted app detection/launch, and Settings page launcher
- Workspace-scoped text file reading/creation and local video opening
- Local reminders, web search, topic watchlist, one-shot proactive checks
- Opt-in background health polling module
- Unit tests and GitHub Actions workflow

Some diagram elements remain incomplete: Gemini Live session runtime, full settings UI, camera capture, robust plugin discovery/contracts, task scheduling/notifications, production-grade Windows automation, and end-to-end Windows validation.

## Requirements

- Windows 11
- Python 3.11+
- An OpenAI API key for chat and cloud speech services
- Microphone permission for push-to-talk
- Optional internet connection for web search and provider calls

## Install

Open PowerShell in the repository directory:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set `OPENAI_API_KEY` and `OPENAI_MODEL`. Never commit your real `.env` file.

The current provider reads environment variables directly. To load `.env` automatically, install/use python-dotenv in your launch environment or set the variables in PowerShell before starting.

```powershell
$env:OPENAI_API_KEY="your-key"
$env:OPENAI_MODEL="your-model"
python main.py
```

Launch the desktop HUD:

```powershell
python main.py --ui
```

Launch the local dashboard API:

```powershell
python main.py --server
```

The dashboard binds to `127.0.0.1:8765` only. It is not intended to be exposed to the public internet.

## CLI skills

```text
/help
/skills
/skill system_monitor {}
/skill computer_settings {"page":"sound"}
/skill reminders {"action":"add","text":"Call home","due_at":"2026-11-04T18:00:00+05:00"}
```

Skills execute only when explicitly invoked. File tools are restricted to the local `workspace/` folder. File creation does not overwrite or delete existing files. Screen capture is explicit; it is not continuous. App launching uses an allowlist.

## Tests

```powershell
python -m unittest discover -s tests -v
```

## Security notes

- Keep API keys in environment variables or a local ignored `.env` file.
- Do not expose the dashboard server beyond localhost without adding authentication and TLS.
- Review any operating-system automation before enabling it.
- Microphone capture is push-to-talk, not always-on.
- Background health monitoring is opt-in and must be started by the application/user.

## Project status

This is an active implementation, not yet a fully completed or verified release. The Gemini Live runtime, full Windows settings experience, camera workflow, dependable scheduled notifications, complete plugin lifecycle and end-to-end tests on a real Windows 11 machine remain to be implemented and verified.
