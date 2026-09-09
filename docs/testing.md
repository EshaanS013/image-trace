# Testing

## Automated coverage

Backend tests cover chunked hashes, empty and streamed content, GPS conversion, Haversine distance, derived-speed skip conditions, timestamp priority/naive handling/timezone assumptions, path and content validation, transactional intake behavior, versioned findings, review history, controlled integrity mismatch, PDF provenance, and manifest content. HTTP tests exercise the complete case-to-report vertical slice.

Frontend tests cover case listing, essential navigation, and theme behavior. The Playwright workflow creates a case, uploads generated evidence, inspects raw metadata, runs analysis, records a qualified finding review, re-verifies integrity, generates a report, and downloads the PDF.

## Commands

Use the exact commands in `README.md` or `AGENTS.md`. CI runs Python 3.12 and Node 22 on Ubuntu. Local verification was performed on Python 3.13 and Node 22 on Windows.

## Security checks

Run `npm audit --omit=dev` for shipped frontend dependencies and `python -m pip check` for Python dependency consistency. Development-tool advisories are documented when they cannot affect the built browser bundle.

