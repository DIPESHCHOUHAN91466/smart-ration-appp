@echo off
REM Starts the Smart Ration backend API (port 5188), the optional Python AI
REM service (port 8001) and the frontend (port 5173) in separate windows.
REM The app works without the AI window; AI panels then show "unavailable".
cd /d "%~dp0"
start "SmartRation Backend" cmd /k dotnet run --project backend\SmartRation.Api --launch-profile http
if exist backend\SmartRation.AI\.venv\Scripts\python.exe (
  start "SmartRation AI" cmd /k "cd /d backend\SmartRation.AI && .venv\Scripts\python -m uvicorn smartration_ai.main:create_app --factory --host 127.0.0.1 --port 8001"
) else (
  echo Python AI service not set up - see README "Python AI service". Continuing without it.
)
start "SmartRation Frontend" cmd /k npm run dev --prefix frontend
