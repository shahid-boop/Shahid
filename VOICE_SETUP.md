# Optional voice setup (Windows 11)

1. Use Python 3.11 or newer.
2. Install the optional packages: `python -m pip install -r requirements-voice.txt`.
3. Start with `python main.py --voice` after the voice mode is wired into the application entry point.
4. Speech recognition currently uses Google's online recognition endpoint; it is not offline and needs internet access.
5. pyttsx3 uses an installed Windows voice. Voice gender, accent, and Urdu pronunciation depend on voices installed on the PC.
6. Microphone and speaker permissions/devices must be enabled in Windows.

This module is optional. Core chat remains usable without audio dependencies.
