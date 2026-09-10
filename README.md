# IMAGE TRACE

Public project demonstration: <https://image-trace-demo.eshaansarkhawas007.chatgpt.site>

The full system runs locally by design. The public site is a read-only product walkthrough using synthetic screenshots; it does not accept or process evidence.

IMAGE TRACE is a local-first workspace for preserving image evidence, inspecting raw and normalized metadata, reconstructing qualified timelines and routes, reviewing explainable findings, and producing versioned PDF reports with separate SHA-256 manifests.

The application is educational decision-support software. It is not a stalking tool, surveillance platform, authenticity oracle, or court-certified forensic suite. Use synthetic or consented evidence only. Missing metadata is not suspicious by itself, and metadata tags do not establish authenticity or manipulation.

## What works

- Case creation, status changes, archive, and reopen through a versioned REST API
- Batch JPEG, PNG, WebP, and TIFF intake with decode, MIME, extension, size, pixel, and path validation
- Immutable controlled originals, streamed SHA-256 acquisition hashes, derived WebP thumbnails, and custody events
- Searchable virtualized evidence inventory with normalized/raw metadata, notes, review state, and keyboard navigation
- Explicit timestamp source, original value, timezone status, confidence, and selection reason
- Shared evidence selection across inventory, chronology, offline coordinate route, and findings
- Immutable analysis runs with versioned transparent rules and auditable review transitions
- On-demand integrity re-verification, printable HTML preview, PDF generation, and SHA-256 sidecar manifest
- Independent light/dark tokens and responsive desktop, tablet, and narrow layouts

## Prerequisites

- Python 3.12 or newer
- Node.js 22 or newer and npm 10 or newer
- Google Chrome for the local Playwright workflow (CI installs Chromium)
- Optional: GTK runtime for WeasyPrint on Windows. Without it, IMAGE TRACE automatically uses its complete paginated ReportLab renderer.

## Quick start - Windows PowerShell

```powershell
cd apps/backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m alembic upgrade head
cd ../frontend
npm ci
cd ../..
.\scripts\dev.ps1
```

Open <http://127.0.0.1:5173>. API documentation is at <http://127.0.0.1:8000/api/docs>.

For an exact pre-resolved Python environment, install `apps/backend/requirements.lock` before the editable package.

## Quick start - macOS or Linux

```bash
cd apps/backend
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m alembic upgrade head
cd ../frontend
npm ci
cd ../..
chmod +x scripts/dev.sh
./scripts/dev.sh
```

## Synthetic demonstration

Generate or refresh the deterministic 20-image fixture:

```powershell
.\apps\backend\.venv\Scripts\python.exe .\scripts\generate_fixture.py
```

The committed fixture includes 14 synthetic-coordinate images, six without GPS, two declared camera groups, editing-software and timestamp-discrepancy examples, a deliberately rapid synthetic transition, and duplicate examples. It depicts no person and asserts no real-world event. See [demo script](docs/demo-script.md).

## Quality checks

```powershell
cd apps/backend
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy image_trace
.\.venv\Scripts\python.exe -m pytest
cd ../frontend
npm run lint
npm run typecheck
npm test -- --run
npm run build
cd ../../tests/e2e
npm ci
npx playwright test
```

## Architecture

The React/Vite client uses TanStack Query for server state, TanStack Table and row virtualization for evidence, React Router for case workspaces, and accessible Radix primitives for consequential overlays and metadata tabs. FastAPI routes remain thin over SQLAlchemy-backed domain services. SQLite runs in WAL mode; evidence bytes live under controlled storage roots and are never served as frontend static files. See [architecture](docs/architecture.md), [data model](docs/data-model.md), and [API guide](docs/api.md).

## Documentation

- [Project guide and system methodology](docs/IMAGE_TRACE_Project_Guide.docx)
- [Methodology](docs/methodology.md)
- [Threat model](docs/threat-model.md)
- [Limitations](docs/limitations.md)
- [Testing](docs/testing.md)
- [Demo script](docs/demo-script.md)

Licensed under the MIT License.
