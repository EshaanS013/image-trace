# API

Interactive OpenAPI documentation is available at `/api/docs` while the backend is running. All product routes use the `/api/v1` prefix. Errors use `{"detail":{"code":"...","message":"..."}}` and do not expose stack traces or storage paths.

## Groups

- Cases: create, list, read, and update `/cases`
- Evidence: batch upload under a case; list/filter; inspect; thumbnail; authorized download; review; notes; re-verify
- Analysis: create and list immutable runs; read one run
- Timeline and map: ordered evidence, derived legs, privacy-safe coordinates
- Findings: case review queue, state transitions, and immutable review events
- Custody and jobs: append-only history, polling, and cancellation
- Reports: generate from a completed run; list; preview; PDF; manifest
- Runtime: `/health` and `/version`

List endpoints accept bounded page and page-size values where applicable. The evidence inventory accepts search, integrity, review, sort, and order parameters.

