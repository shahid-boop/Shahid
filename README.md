# Shahid Assistant — Windows 11

A modular Windows desktop assistant based on the supplied architecture diagram.

## Implemented modules

- Conversation runtime with local persistent transcript and bounded recent context
- OpenAI-compatible chat provider and Gemini text provider selection
- Tkinter desktop chat HUD and separate settings window
- Push-to-talk microphone capture, Whisper speech-to-text and text-to-speech adapters
- Browser dashboard served on localhost with chat and status endpoints
- Skill and plugin registries
- Windows system health checks, allowlisted app detection/launch, and Settings page launcher
- Workspace-scoped text file reading/creation and local video opening
- Local reminders, opt-in Windows toast scheduler, web search and topic watchlist
- On-demand screen capture and on-demand webcam still-photo capture
- Opt-in background system health polling module
- Unit tests and Windows GitHub Actions workflow

## Still incomplete / requires further work

- Gemini Live real-time audio conversation session (the Gemini text provider is not Gemini Live)
- Full-featured HUD overlay, animated/always-visible desktop widget and complete settings coverage
- Production-grade Windows UI automation and permission/approval UX
- Plugin package discovery, sandboxing and lifecycle management
- Persistent task execution and robust scheduled topic monitoring
- End-to-end validation on a real Windows 11 PC, including microphone, camera, GPU/audio drivers and API provider connectivity

## Requirements

- Windows 11
- Python 3.11+
- An API key for the selected cloud LLM provider
- Microphone permission for push-to-talk
- Optional webcam and internet connection for their respective features

## Install

Open PowerShell in the repository directory:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

Or manually:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set either:
- `OPENAI_API_KEY` and `OPENAI_MODEL` for `openai_compatible`, or
- `GOOGLE_API_KEY` for `gemini`.

Never commit your real `.env` file. It is ignored by Git.

## Launch

```powershell
# Desktop chat HUD with push-to-talk voice
.\run.ps1

# Settings window
.\.venv\Scripts\python.exe main.py --settings

# Browser dashboard (open http://127.0.0.1:8765)
.\.venv\Scripts\python.exe main.py --server

# CLI with explicit opt-in reminder notifications
.\.venv\Scripts\python.exe main.py --reminders
```

Choose the engine in the settings window and restart the app after changing it. The browser dashboard binds to loopback only and must not be exposed to the public internet without authentication and TLS.

## CLI skills

```text
/help
/skills
/skill system_monitor {}
/skill computer_settings {"page":"sound"}
/skill camera_capture {"output_path":"camera.png","device_index":0}
```

Skills execute only when explicitly invoked. File tools are restricted to the local `workspace/` folder. File creation does not overwrite or delete existing files. Screen and camera capture are on-demand; they are not continuous. App launching uses an allowlist.

## Tests

```powershell
.\.venv\Scripts\python.exe -m compileall -q .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Security

- Keep API keys in the local ignored `.env` file or environment variables.
- Do not expose the dashboard beyond localhost without authentication and TLS.
- Microphone recording is push-to-talk, not always-on.
- Camera and screen capture require explicit skill invocation.
- Reminder and health monitoring loops are opt-in.
- File access is workspace-scoped; create operation never overwrites/deletes.

## Project status

This is an active implementation and is not yet a completed, production-verified release. See the incomplete modules above. Windows 11 end-to-end testing and API credentials are still required before calling it complete.
