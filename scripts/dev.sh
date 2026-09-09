#!/usr/bin/env sh
set -eu
apps/backend/.venv/bin/python -m uvicorn image_trace.main:app --app-dir apps/backend --host 127.0.0.1 --port 8000 &
cd apps/frontend
npm run dev

