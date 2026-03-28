@echo off
setlocal

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo [1/2] Running backend tests...
python -m pytest
if errorlevel 1 (
  echo.
  echo Backend tests failed.
  exit /b 1
)

echo.
echo [2/2] Building frontend...
call npm --prefix "%ROOT_DIR%frontend" run check
if errorlevel 1 (
  echo.
  echo Frontend check failed.
  exit /b 1
)

echo.
echo All checks passed.
exit /b 0
