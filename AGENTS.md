# AGENTS.md

## Mission

Maintain IMAGE TRACE as a local-first, evidence-preserving educational image-forensics workspace. Use measured language. Never infer guilt, authenticity, or manipulation from metadata alone.

## Commands

- Backend setup: `cd apps/backend && python -m pip install -e ".[dev]"`
- Backend database: `cd apps/backend && alembic upgrade head`
- Backend run: `cd apps/backend && uvicorn image_trace.main:app --reload --port 8000`
- Backend checks: `cd apps/backend && ruff check . && mypy image_trace && pytest`
- Frontend setup: `cd apps/frontend && npm ci`
- Frontend run: `cd apps/frontend && npm run dev`
- Frontend checks: `cd apps/frontend && npm run lint && npm run typecheck && npm test -- --run && npm run build`
- Fixtures: `cd apps/backend && python ../../scripts/generate_fixture.py`
- End to end: `cd tests/e2e && npm ci && npx playwright test`

## Boundaries and safety

- Never modify a stored original through production code.
- Treat filenames and metadata as hostile input; do not follow embedded URLs.
- Do not expose storage paths or originals through static hosting.
- Uploaded evidence, databases, derivatives, reports, logs, and credentials must remain untracked.
- Use only synthetic or consented evidence in demonstrations.
- Preserve raw timestamp values and never label timezone-naive EXIF time as UTC.
- Automated findings are indicators requiring qualified review.

## Directory conventions

- `apps/frontend`: React client
- `apps/backend`: FastAPI service, domain services, migration
- `fixtures/synthetic-case`: deterministic public-safe fixtures
- `storage`: ignored runtime evidence and generated artifacts
- `docs`: architecture, methodology, security, API, and test records
- `tests/e2e`: Playwright workflow

## Definition of done

Required behavior is implemented end to end, migrations work from an empty database, automated checks pass, the rendered UI and generated PDF are visually inspected, documentation matches reality, and no secrets or private evidence are tracked.

