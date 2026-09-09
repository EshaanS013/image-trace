$ErrorActionPreference = "Stop"
Start-Process -FilePath ".\apps\backend\.venv\Scripts\python.exe" -ArgumentList "-m", "uvicorn", "image_trace.main:app", "--app-dir", "apps/backend", "--host", "127.0.0.1", "--port", "8000" -WindowStyle Hidden
Set-Location "apps/frontend"
npm run dev

