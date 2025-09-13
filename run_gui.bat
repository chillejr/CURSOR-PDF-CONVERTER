@echo off
setlocal
cd /d %~dp0

REM Ensure virtual environment
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  py -3 -m venv .venv
  if errorlevel 1 goto venv_error
  echo Installing dependencies...
  .\.venv\Scripts\python.exe -m pip install --upgrade pip
  .\.venv\Scripts\pip install -r requirements.txt
)

echo Launching GUI...
.\.venv\Scripts\python.exe cli.py gui
if errorlevel 1 pause
exit /b 0

:venv_error
echo Failed to create a virtual environment. Ensure Python 3 is installed and 'py' is on PATH.
pause
exit /b 1