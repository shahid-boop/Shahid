# Shahid Assistant — Windows 11

A modular Python desktop assistant. All advanced work is additive on `diagram-audit-implementation`; prior features and branches remain preserved.

## Retained foundation
- CLI chat, Tkinter desktop chat HUD (`--ui`), localhost dashboard (`--server`).
- OpenAI-compatible chat and Gemini text API.
- Local bounded conversation memory, reminders, task queue, workspace file skills.
- Allowlisted Windows app launch and website opening.
- Windows CI compile and unit-test workflow.

## Advanced diagram modules added
- **Gemini Live:** optional asynchronous Live API session adapter in `realtime/gemini_live.py`, with PCM16 input and streamed response events.
- **Whisper:** optional local faster-whisper transcription in `realtime/whisper_transcriber.py`.
- **Wake word:** openWakeWord PCM16 detector in `realtime/wake_word.py`; caller supplies audio frames.
- **Screen/camera capture:** explicit opt-in snapshots in `vision/capture.py`; no silent recording or uploads.
- **HUD video:** opt-in camera frame source in `vision/hud_video.py`; UI callback owns frame rendering and stop lifecycle.
- **Topic monitoring:** user-configured HTTPS RSS/Atom feeds, keyword filtering, deduplication and background polling in `monitoring/topic_monitor.py`.
- **Notifications:** Windows toast helper in `monitoring/notifications.py`.
- **Windows preferences:** narrow HKCU allowlist in `windows/settings.py`; changes require explicit confirmation.
- **Desktop automation:** PyAutoGUI click/type/screenshot primitives with explicit confirmation, screen bounds checks and fail-safe in `automation/desktop.py`.
- **Plugin marketplace core:** Ed25519-signed manifest verification, SHA-256 archive pinning and zip-slip/size checks in `plugins/marketplace.py`.

## Optional setup
Install base packages and tests:
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```
Install advanced optional dependencies:
```powershell
python -m pip install -r requirements-live.txt
```
Configure `GOOGLE_API_KEY` for Gemini Live. Live API model access and account availability depend on Google's current API entitlement. Whisper downloads a model on first use. Camera/microphone, PyAutoGUI and Windows toast behavior require a real Windows PC and user permissions.

## Important integration boundaries
- The modules are callable library components. The existing CLI/dashboard/HUD do not automatically start always-on mic, webcam, screen capture, or background monitoring.
- Gemini Live adapter expects the Google GenAI Live API and PCM16 frames supplied by an audio capture loop; this repository does not yet provide a polished duplex audio-device UI.
- Whisper accepts an audio file; live microphone chunking and diarization are not included.
- Wake-word detection accepts PCM16 frames; a microphone streaming loop and custom wake-word model provisioning are not bundled.
- Camera HUD produces frames through a callback; embedding a polished video widget in Tkinter remains a UI integration task.
- TopicMonitor is opt-in and supports RSS/Atom keyword matching. Start it from an app lifecycle and supply a callback; no monitor runs until explicitly started.
- Windows settings are limited to three documented HKCU preferences. No arbitrary registry edits or administrator-level system changes.
- Desktop automation supports bounded clicks and typing only. It does not execute shell commands, bypass UAC, or autonomously operate arbitrary apps.
- Plugin marketplace code verifies signed local archives; a hosted catalog, publisher onboarding, payment, revocation service, sandboxed execution and update channel are not provided. Plugins are executable Python and must be reviewed.
- Camera/screen captures and desktop actions require user consent. No remote upload or covert capture is implemented.

## Run existing modes
`python main.py --chat`, `python main.py --ui`, `python main.py --server`, `python main.py --voice`.

## Security
- Dashboard binds to loopback only.
- Local tools are allowlisted; no arbitrary shell execution.
- Workspace file tools are confined to `workspace/`.
- Never commit API keys or `.env`.
