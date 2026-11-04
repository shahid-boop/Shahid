# Optional voice setup (Windows 11)

1. Use Python 3.11 or newer and activate the project's virtual environment.
2. Install packages: `python -m pip install -r requirements-voice.txt`.
3. Set `AI_PROVIDER` and the corresponding API key in your local `.env`.
4. Start voice mode: `python main.py --voice`.
5. Speech recognition uses Google's online recognition endpoint with `ur-PK`; internet is required.
6. pyttsx3 uses a voice installed in Windows. Accent, gender, and Urdu pronunciation depend on installed voices.
7. Confirm Windows microphone and speaker permissions/devices are enabled.

This is optional speech input/output, not Gemini Live audio. Core chat remains available without audio dependencies.
