# Build Shahid Assistant for Windows

The Windows desktop build packages the existing Tkinter interface launched by `main.py --ui`.
It does not replace the Python source, CLI, local server, voice mode, Gemini Live mode, or
the existing feature modules.

## Build on a Windows 10/11 PC

1. Install 64-bit Python 3.11 and make sure Python is available in PATH.
2. Open the project folder in File Explorer.
3. Double-click `build_windows.bat`.
4. When it finishes, launch `dist\ShahidAssistant\ShahidAssistant.exe`.

Keep the complete `dist\ShahidAssistant\` folder together; do not copy only the EXE.
The build is a portable onedir package, not an installer.

## Build through GitHub Actions

Open the repository's Actions tab and run **Build Shahid Assistant EXE** using
**Run workflow** on the `diagram-audit-implementation` branch. Download the
`ShahidAssistant-Windows-x64` artifact from the completed run and extract it.

A push changing Python source, requirements, or the build workflow on that branch
also starts a build automatically.

## Configuration and optional features

Copy the project's `.env.example` to `.env` beside the executable (or configure the
environment variables used by the project) and add your own API credentials. Never
commit API keys.

This first EXE packages the current desktop chat UI and Python feature modules. Optional
hardware integrations (microphone, camera, screen capture, wake word, and desktop control)
may still require their documented Windows runtime packages, drivers, permissions, and
API credentials. Packaging does not turn features that are opt-in library components into
automatically running background services.
