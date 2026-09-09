@echo off
setlocal
cd /d "%~dp0"
echo Publishing IMAGE TRACE to GitHub...
git push -u origin main
if errorlevel 1 (
  echo.
  echo Push failed. Please confirm GitHub CLI login with: gh auth status
  pause
  exit /b 1
)
echo.
echo Published successfully: https://github.com/EshaanS013/image-trace
pause
