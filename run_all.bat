@echo off

echo Starting Backend...
start cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 2

echo Starting Frontend...
start cmd /k "cd frontend && flutter run -d chrome"