@echo off
echo ========================================
echo Starting TraderBot Backend (FastAPI)
echo ========================================
echo.

REM Activate virtual environment
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo WARNING: Virtual environment not found!
    echo Please run: python -m venv .venv
    pause
    exit /b 1
)

echo.
echo Starting FastAPI server on http://localhost:5000
echo WebSocket available at ws://localhost:5000/ws
echo API Documentation: http://localhost:5000/docs
echo.
echo Press CTRL+C to stop the server
echo.

python -m uvicorn backend.app:app --host 0.0.0.0 --port 5000 --reload

