# Shahid Assistant — Windows 11

A modular Python desktop assistant foundation, developed on the `diagram-first-implementation` branch. Existing `main` and `architecture-foundation` branches are preserved.

## Implemented features
- CLI chat, Tkinter desktop chat HUD (`--ui`), and localhost browser dashboard (`--server`).
- OpenAI-compatible `/chat/completions` and Google Gemini text API (`AI_PROVIDER=gemini`).
- Local bounded conversation history in `data/conversations.json`.
- Optional microphone input and speech output (`--voice`) using SpeechRecognition and pyttsx3.
- Allowlisted Windows tools: system info, launch Notepad/Calculator/Paint/Explorer, and open HTTP(S) websites.
- CLI tool commands: `/skills`, `/run system_info {}`, `/run launch_app {"name":"notepad"}`, `/run open_website {"url":"https://example.com"}`.
- Windows GitHub Actions compile and unit-test workflow.

## Setup
Install Python 3.11+. In PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Configure local `.env`:
- OpenAI-compatible: `AI_PROVIDER=openai`, set `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL`.
- Gemini: `AI_PROVIDER=gemini`, set `GOOGLE_API_KEY`. Text adapter currently uses `gemini-2.5-flash`.

Run:
- `python main.py --chat` — terminal chat
- `python main.py --ui` — Tkinter chat HUD
- `python main.py --server` — local browser dashboard at http://127.0.0.1:8765
- `python main.py --voice` — optional mic + speech mode (install voice requirements first)

Voice packages: `python -m pip install -r requirements-voice.txt`. Recognition uses Google's online service and needs internet. Urdu recognition requests `ur-PK`; actual accuracy and TTS accent/gender depend on installed Windows voices and audio hardware. This is not Gemini Live audio.

## Safety and limitations
- Dashboard is loopback-only; it is not exposed to the public network.
- Local tools are allowlisted; arbitrary shell execution is not enabled.
- Conversation history is local. CLI `/clear` clears the default conversation.
- Never commit `.env` or API keys.
- Webcam, full desktop vision/control, wake-word, animated HUD, Gemini Live streaming, and physical device testing are not implemented.
- CI cannot verify the user's own microphone, speakers, or API credentials. Run tests and manually verify those on the target PC.

## Validation
Run `python -m unittest discover -s tests -v`. GitHub Actions compiles the project and runs unit tests on Windows Python 3.11.
