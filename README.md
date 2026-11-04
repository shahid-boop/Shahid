# Shahid Assistant — Windows 11

A modular Windows desktop assistant with chat, voice, local skills, task handling and an optional localhost dashboard.

## Implemented capabilities

- OpenAI-compatible and Gemini text providers with local persistent conversation memory
- Gemini Live continuous microphone input and streaming speaker output, with an explicit stop control
- Animated Tkinter desktop HUD with pulsing assistant orb, moving waveform, live status, always-on-top, compact and right-docked layouts
- Push-to-talk Whisper transcription and text-to-speech
- Localhost-only browser dashboard
- Explicit skill and trusted plugin registries; optional Docker-isolated third-party Python plugin execution
- Windows health checks, Settings launcher, allowlisted app launch and individually confirmed UI actions
- Workspace-scoped file tools, on-demand screen capture and webcam still photos
- Local reminders, opt-in Windows notifications and health polling
- Topic watchlist with opt-in scheduled public-web polling
- Durable task queue with claim/complete/fail/retry state and an opt-in worker for approved handlers

## Requirements

- Windows 11 and Python 3.11+
- An API key for the selected LLM provider
- Microphone/speakers for voice features
- Optional webcam for camera capture

## Install

Open PowerShell in the repository folder:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

Or install manually:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set either `OPENAI_API_KEY` and `OPENAI_MODEL`, or `GOOGLE_API_KEY` in the local `.env` file. Never commit real credentials.

## Launch

```powershell
# Desktop HUD
.\run.ps1

# Settings
.\.venv\Scripts\python.exe main.py --settings

# Local browser dashboard: http://127.0.0.1:8765
.\.venv\Scripts\python.exe main.py --server

# Optional reminder notifications
.\.venv\Scripts\python.exe main.py --reminders

# Optional background system-health polling
.\.venv\Scripts\python.exe main.py --monitor

# Optional scheduled topic polling (topics live in data/topics.json)
.\.venv\Scripts\python.exe main.py --watch-topics

# Optional worker for explicitly approved durable task kinds
.\.venv\Scripts\python.exe main.py --run-tasks

# Gemini Live text CLI
.\.venv\Scripts\python.exe main.py --gemini-live
```

The HUD's **Start Live Voice** control opens a continuous Gemini Live audio session. **Stop Live Voice** interrupts playback and disconnects. This requires `GOOGLE_API_KEY`, `google-genai`, `sounddevice`, a microphone and speakers. Echo reduction uses an adaptive NLMS filter when a WASAPI loopback input is exposed by PortAudio. Voice-activity barge-in detection clears queued assistant playback when the microphone captures speech. Device support, tuning and false-interrupt behavior must be validated on the target PC; the manual Stop control remains available.

## CLI skills

```text
/help
/skills
/skill system_monitor {}
/skill computer_settings {"page":"sound"}
/skill camera_capture {"output_path":"camera.png","device_index":0}
/skill windows_automation {"action":"open_notepad","confirmed":true}
/skill windows_automation {"action":"click","x":400,"y":300,"confirmed":true}
/plugins
/plugin system_monitor {}
/skill topic_monitoring {"action":"add","topic":"Python release notes"}
/skill topic_monitoring {"action":"check"}
/skill agent_tasks {"action":"add","task":"Search Python release notes","kind":"web_search","payload":{"query":"Python release notes"}}
/skill agent_tasks {"action":"list"}
```

Run `main.py --run-tasks` to execute queued tasks of registered kinds. Currently the worker registers only `web_search`. Unknown task kinds remain queued and are not executed. Manual tasks remain stored until explicitly handled.

## Third-party plugin sandbox

Install and start Docker Desktop using Linux containers. The built-in `sandbox_python` plugin runs submitted Python code in a short-lived container with networking disabled, read-only root filesystem, dropped Linux capabilities, no-new-privileges, PID/memory/CPU limits, an unprivileged UID and a small temporary filesystem. It receives only JSON input over stdin and has no host-folder mounts. The Docker daemon and host kernel remain trusted; this is defense-in-depth, not a guarantee against every container escape. Example CLI call:

```text
/plugin sandbox_python {"source":"def run(payload): return {'message': payload['message']}","payload":{"message":"hello"}}
```

## Safety boundaries

- Plugins are registered explicitly and run in-process. Arbitrary third-party plugin discovery/import and OS-level sandboxing are **not** enabled. Register only code you trust.
- UI automation is a limited allowlist: confirmed app launches, clicks, text entry, safe key presses and selected hotkeys. It is not unrestricted control.
- File tools are restricted to `workspace/`; creation does not overwrite or delete existing files.
- Microphone, camera and screen capture are activated only by explicit user actions.
- Background reminders, health polling, topic polling and task processing are opt-in.
- The dashboard binds to loopback. Do not expose it publicly without authentication and TLS.
- API keys belong in the ignored local `.env` file or environment variables.

## Target-device diagnostics

After installing dependencies and configuring the API key in your local environment, run this on the Windows 11 PC:

```powershell
.\\.venv\\Scripts\\python.exe tools\\windows_device_diagnostics.py
```

It reports microphone/speaker enumeration, default camera capture, API-key presence and Docker availability. It does not print secret values or send API requests. Run a separate short Live Voice session to validate Gemini credentials and real-time audio round-trip.

## Tests

```powershell
.\.venv\Scripts\python.exe -m compileall -q .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

GitHub Actions runs the same compile and unit-test commands on Windows. A passing CI run does not replace a real Windows 11 device check.

## Verification limits

The code and unit-test workflow can be checked in CI. This environment cannot physically test your PC's microphone, speakers, webcam, GPU/audio drivers or API credentials. Full-device validation must be performed on the target Windows 11 machine before treating this as a production release.
