# Architecture

## System shape

The browser client talks only to the versioned FastAPI surface. The API coordinates narrowly scoped services, a SQLAlchemy repository boundary, SQLite records, and controlled filesystem storage. The frontend never receives an absolute storage path.

```text
React workspace -> /api/v1 -> thin FastAPI routes -> domain services
                                                  |-> SQLite (records/audit/jobs)
                                                  |-> controlled storage (originals/derivatives/reports)
```

SQLite is configured with WAL, foreign keys, and a busy timeout. Models and query boundaries permit a later PostgreSQL repository without moving behavior into route handlers.

## Service boundaries

- `evidence_service`: validates, preserves, registers, and transactionally creates the acquisition event
- `hash_service`: chunked SHA-256 for acquisition and verification
- `metadata_service`: hostile-input-safe raw extraction and normalized fields
- `timeline_service`: timestamp priority, timezone policy, confidence, and reasons
- `geo_service`: GPS conversion, Haversine distance, and derived speed
- `analysis_service`: immutable versioned runs and explainable rule outputs
- `report_service`: analysis-bound HTML/PDF rendering, report hash, manifest, and custody event
- `storage_service`: controlled relative keys and root-containment checks

Upload jobs are durable database records with explicit stage, counts, status, attempts, errors, cancellation intent, and timestamps. The MVP executes bounded work in-process and permits partial batch success. A production restart can identify unfinished jobs without requiring Redis or a distributed queue.

## Evidence and report flow

An accepted upload is copied once to a generated UUID directory. The server decodes actual content, records a streamed acquisition hash, extracts metadata, commits evidence plus its initial custody event in one transaction, and generates only a derivative thumbnail. A report references one completed analysis run, is finalized before hashing, and receives a separate manifest so the PDF never contains its own hash.

