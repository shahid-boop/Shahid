# Shahid Assistant — Windows 11

A modular Windows desktop assistant based on the supplied architecture diagram.

## Implemented modules

- Conversation runtime with local persistent transcript and bounded recent context
- OpenAI-compatible chat provider, Gemini text provider, and a Gemini Live session mode
- Tkinter desktop chat HUD with configurable always-on-top behavior and separate settings window
- Push-to-talk microphone capture, Whisper speech-to-text and text-to-speech adapters
- Gemini Live continuous microphone-to-speaker streaming session with a stop control (requires Gemini API key and working audio devices)\n- Compact and right-docked HUD layouts
- Browser dashboard served on localhost with chat and status endpoints
- Skill and plugin registries
- Windows system health checks, allowlisted app detection/launch, and Settings page launcher
- Workspace-scoped text file reading/creation and local video opening
- Local reminders, opt-in Windows toast scheduler, web search, topic watchlist and scheduled topic polling\n- Durable local task queue with claim/complete/fail/retry lifecycle and an opt-in worker for explicitly registered task handlers
- On-demand screen capture and on-demand webcam still-photo capture
- Opt-in background system health polling module
- Unit tests and Windows GitHub Actions workflow

## Still incomplete / requires further work

- Gemini Live text CLI is implemented; full-duplex live microphone capture and streaming speaker playback still need end-to-end integration
- Rich animated HUD overlay, docking/compact modes and complete settings coverage
- Production-grade Windows UI automation and permission/approval UX
- External plugin package discovery/sandboxing is intentionally not enabled; plugins must be explicitly registered as trusted Python handlers
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

# CLI with explicit opt-in background health monitoring
.\.venv\Scripts\python.exe main.py --monitor

# Gemini Live text session
.\.venv\Scripts\python.exe main.py --gemini-live
```

Choose the engine in the settings window and restart the app after changing it. The HUD can be kept always on top from Settings. The **Start Live Voice** HUD control opens a continuous Gemini Live audio session; **Stop Live Voice** interrupts playback and closes the session. This requires `GOOGLE_API_KEY`, `google-genai`, `sounddevice`, a microphone and speakers. Echo cancellation and automatic barge-in detection are not included. Gemini Live text mode uses the separate `GOOGLE_API_KEY` and `GEMINI_LIVE_MODEL` settings: `python main.py --gemini-live`. The browser dashboard binds to loopback only and must not be exposed to the public internet without authentication and TLS.

## CLI skills

```text
/help
/skills
/skill system_monitor {}
/skill computer_settings {"page":"sound"}
/skill camera_capture {"output_path":"camera.png","device_index":0}
/skill windows_automation {"action":"open_notepad","confirmed":true}
/plugins
/plugin system_monitor {}
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

This is an implementation draft, not a production-verified release. Automated CI must pass on the current branch, and real Windows 11 device testing with configured API credentials is still required. Third-party plugin sandboxing, unrestricted UI automation, animated HUD effects, echo cancellation and speech barge-in detection are not claimed as implemented.
