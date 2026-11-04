# Run the Shahid Assistant desktop HUD.
$ErrorActionPreference = "Stop"
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Virtual environment missing. Run .\install.ps1 first."
}
& .\.venv\Scripts\python.exe main.py --ui
