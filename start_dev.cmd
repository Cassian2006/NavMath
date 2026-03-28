@echo off
setlocal EnableDelayedExpansion

set "ROOT_DIR=%~dp0"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=5173"

call :require_command python "Python"
if errorlevel 1 exit /b 1
call :require_command npm "npm"
if errorlevel 1 exit /b 1

echo Cleaning ports %BACKEND_PORT% and %FRONTEND_PORT%...
call :kill_port %BACKEND_PORT%
call :kill_port %FRONTEND_PORT%

echo.
echo Starting backend...
start "NavMath Backend" cmd /k "cd /d ""%ROOT_DIR%"" && python run.py"

echo Starting frontend...
start "NavMath Frontend" cmd /k "cd /d ""%ROOT_DIR%frontend"" && npm run dev"

echo.
echo Backend:  http://127.0.0.1:%BACKEND_PORT%
echo Frontend: http://127.0.0.1:%FRONTEND_PORT%
exit /b 0

:require_command
where %~1 >nul 2>nul
if errorlevel 1 (
  echo %~2 is not available in PATH.
  exit /b 1
)
exit /b 0

:kill_port
set "TARGET_PORT=%~1"
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%TARGET_PORT% .*LISTENING"') do (
  echo Killing PID %%P on port %TARGET_PORT%...
  taskkill /F /PID %%P >nul 2>nul
)
exit /b 0
