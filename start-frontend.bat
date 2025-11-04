@echo off
echo ========================================
echo Starting TraderBot Frontend (React)
echo ========================================
echo.

cd frontend

if not exist node_modules (
    echo Node modules not found. Installing dependencies...
    call npm install
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo Starting React development server...
echo Frontend will be available at http://localhost:3000
echo.
echo Press CTRL+C to stop the server
echo.

call npm run dev

