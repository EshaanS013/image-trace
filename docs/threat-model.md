# Threat model

## Assets and trust boundaries

Assets are original image bytes, acquisition hashes, case context, coordinates, audit history, analysis configuration, and reports. Submitted files, filenames, MIME declarations, metadata, and report text cross an untrusted input boundary. The browser and optional online services are outside controlled evidence storage.

## Main threats and mitigations

- Traversal, overwrite, and symlink escape: generated UUID paths, basename validation, exclusive pending files, resolved-root containment
- Polyglot or mislabeled files: extension, declared MIME, Pillow format, decode, size, and pixel checks
- Decompression bombs or parser exhaustion: Pillow pixel limit, 100 MiB file limit, 100 megapixel default, 200-file batch limit
- Original mutation: no production mutation route; read-only product behavior after acquisition; verification audits mismatches
- Script/report injection: raw metadata serialized and escaped; Jinja autoescape; React text rendering
- Privacy leakage: originals are never static assets; API-controlled download; offline coordinate canvas; online tiles disabled
- Partial records: evidence, hash, metadata, and initial custody event share one database transaction
- Historical rewriting: new analysis runs and append-only review/custody events

## Residual risks

Local administrators can alter files or the database. SQLite does not provide tamper-evident audit storage. Image parsers may contain unknown vulnerabilities. Reports are not digitally signed. Users remain responsible for lawful authority, consent, and secure host operation.

