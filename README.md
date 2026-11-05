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
- Camera HUD produces frames through a callback; the desktop HUD now provides a consent-gated local camera preview with a Stop Camera control.
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


## Advanced diagram modules (opt-in)
Install the optional Windows integrations with `python -m pip install -r requirements-live.txt`. These are not part of the minimal install because audio, camera, and native desktop dependencies vary by PC.

- **Gemini Live audio:** `python main.py --live` streams 16 kHz microphone PCM to Gemini Live and plays 24 kHz response PCM through the default speaker. Configure `GOOGLE_API_KEY`; the model and API access must support Live. Press Ctrl+C to stop.
- **Whisper:** use `realtime.whisper_transcriber.WhisperTranscriber` to transcribe a recorded audio file locally. First model use downloads model weights.
- **Wake word:** `realtime.wake_word.WakeWordDetector` scores caller-supplied PCM16 frames. Microphone ownership stays with the calling app.
- **Screen/camera:** `/run capture_screen {"confirm":true}` and `/run capture_camera {"confirm":true}` save a still image. The camera and screen are never accessed without explicit confirmation.
- **HUD video:** `vision.hud_video.HudVideo` streams webcam frames to a callback; the caller owns the preview window and must stop it.
- **Topic monitoring:** `/run start_topic_monitor {"feeds":["https://example.org/rss"],"keywords":["python"],"interval_seconds":900}`; stop with `/run stop_topic_monitor {}`. Windows toast notifications require winotify. Only HTTPS RSS/Atom feeds are accepted; polling is opt-in.
- **Windows preferences and app identity:** `/run list_windows_preferences {}`, `/run set_windows_preference {"name":"dark_app_mode","enabled":true,"confirm":true}`, and `/run lookup_installed_app {"name":"Notepad"}`. Registry writes are limited to allowlisted HKCU values.
- **Desktop automation:** `/run desktop_screenshot {"confirm":true}`, `/run desktop_click {"x":500,"y":300,"confirm":true}`, and `/run desktop_type {"text":"hello","confirm":true}`. This is coordinate-based automation, not a vision agent; PyAutoGUI's fail-safe remains enabled.
- **Signed plugin packages:** `plugins.marketplace.install_archive` verifies an Ed25519-signed manifest and archive SHA-256, rejects traversal/symlink entries and enforces package limits. Installation does not execute plugin code; review and explicit activation are separate. This is a local marketplace core, not a hosted public catalog/publisher ecosystem.

### Important boundaries
Gemini Live needs a Live-enabled Google API key and working microphone/speaker drivers. Whisper runs locally but may download large model weights and use significant RAM/CPU. Screen/camera access can expose private information; invoke only when you intend to capture. Desktop clicks/typing affect the active desktop and require explicit confirmation. Topic monitoring runs only after the start skill is called and stops when the process exits. A production hosted plugin marketplace still needs a publisher portal, trusted signing-key distribution/rotation, moderation, update/revocation service, and sandboxed plugin runtime; this repository deliberately does not execute downloaded plugin code automatically.


## Desktop HUD tools and voice controls
Run `python main.py --ui` to open the Tkinter desktop HUD. The HUD now has:

- **Chat area:** the existing provider-backed chat and persistent conversation history, plus a one-phrase **Voice input** button. Microphone capture starts only after the user presses that button.
- **Speak replies:** an optional checkbox that sends generated replies to the configured local speech engine. Install `requirements-voice.txt` first; microphone/speaker availability depends on the Windows PC.
- **Tools window:** open it from the desktop HUD to access the same allowlisted skill registry used by the CLI, including reminders, workspace file operations, app/web helpers, system status, screen/camera capture, Windows preferences, desktop actions, monitoring and signed-plugin installation.
- **Whisper transcription:** run `transcribe_audio` with a local `audio_path`; choose a supported model size and optional language code. The local Whisper model may download weights on first use.
- **Wake-word listening:** run `listen_for_wake_word` for a bounded 1–120 second microphone window. The HUD asks for confirmation first; no background microphone listener is started automatically.
- **Per-action approval:** screen/camera capture, desktop input, Windows preference changes, plugin installation, topic-monitor startup and local state-changing actions require a confirmation dialog in the HUD. The existing skill handlers still enforce their own confirmation flags where applicable. A rejected confirmation runs no action.

The Tools tab dispatches only registered skills; it is not a general shell or arbitrary-code console. Optional dependencies, API keys and real Windows hardware are still required for the corresponding integrations. Gemini Live remains available through the explicit `python main.py --live` command; the HUD does not silently start an always-on microphone or camera.

## Latest desktop HUD integration
The desktop HUD now includes manual, consent-gated controls for:
- **Gemini Live:** start/stop microphone and speaker session; the audio runner reacts to Gemini Live interruption events by aborting queued playback so a user can barge in.
- **Camera Preview:** opens the webcam only after confirmation, displays frames locally, and provides an explicit Stop Camera control. No frames are uploaded.
- **Whisper File:** select a local audio file and transcribe it with the optional faster-whisper dependency in a background worker.
- **Wake Word:** a separately confirmed, bounded 30-second microphone listen; it ends on detection or timeout.
- **Tools window:** tool execution now runs in a background worker so slow optional model loads do not freeze the Tkinter window.

The camera, Whisper and wake-word controls require their optional dependencies from the relevant requirements files. The EXE build workflow currently packages the core application; optional native/audio/vision/model dependencies are not guaranteed to be bundled in the EXE and may need a Python installation with the optional requirements. Real microphone, speaker, camera, and echo-cancellation behavior still requires Windows 11 hardware validation.

## Remaining production work (not claimed complete)
- Validate Gemini Live barge-in and audio-device cleanup on physical Windows 11 hardware; acoustic echo cancellation is not implemented by this code.
- Add continuous microphone streaming for Whisper (current HUD transcription is file-based).
- Integrate wake-word detection as a deliberate user-configured session trigger; it is currently a bounded, manual listen.
- Build a real visual computer-control agent only with additional per-action approvals and screen-boundary protections; current automation is bounded click/type/screenshot.
- A production plugin marketplace still needs trusted signing-key lifecycle, hosted catalog/publisher review, revocation/update service, and an OS-level isolated runtime. Current code verifies local signed packages but does not sandbox or auto-execute plugin code.
- Run end-to-end tests with actual Windows 11 microphone, speakers, camera, and supported API credentials.