@echo off
setlocal
cd /d "%~dp0"

python -m PyInstaller --noconfirm --clean --onedir --windowed ^
  --name ShahidAssistant ^
  --add-data ".env.example;." ^
  --collect-submodules skills ^
  --collect-submodules providers ^
  --collect-submodules monitoring ^
  --collect-submodules plugins ^
  --collect-submodules realtime ^
  --collect-submodules speech ^
  --collect-submodules vision ^
  main.py

if errorlevel 1 (
  echo.
  echo BUILD FAILED. See the error above.
  exit /b 1
)

if not exist "dist\ShahidAssistant\ShahidAssistant.exe" (
  echo BUILD FAILED: executable not found.
  exit /b 1
)

echo.
echo Build complete: dist\ShahidAssistant\ShahidAssistant.exe
echo Copy the entire ShahidAssistant folder when moving the app to another PC.
endlocal
