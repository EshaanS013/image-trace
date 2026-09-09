# Methodology

## Acquisition and extraction

The server validates the submitted basename, supported extension, declared MIME type, image signature/format, full decode, file size, and pixel count. It copies in chunks to a pending path, flushes the bytes, atomically renames the file, and computes SHA-256 in chunks. Metadata is escaped and size-bounded for JSON storage and display. Thumbnails are new derivatives; originals are not rotated or recompressed.

## Time and geography

Timestamp selection follows the documented priority and records the original string, chosen source, timezone status, confidence, and rejection reason for unavailable higher-priority sources. Haversine distance uses an Earth radius of 6,371.0088 km. Speed is distance divided by positive elapsed time and is labelled derived. It is skipped for unusable coordinates, non-positive intervals, or unknown timezone comparison.

## Rule set 1.0.0

- `INTEGRITY_HASH_MISMATCH` compares acquisition and current SHA-256 values.
- `TIMESTAMP_SOURCE_FALLBACK` identifies filesystem fallback selection.
- `EDITING_SOFTWARE_PRESENT` reports the exact tag and configured pattern without a manipulation claim.
- `IMPLAUSIBLE_TRAVEL` reports the pair, distance, interval, derived speed, threshold, and timestamp confidence; default threshold is 1,000 km/h.
- `MISSING_GPS` states only that usable coordinates are absent.
- `CAMERA_SOURCE_CHANGE` compares adjacent reported make/model groups.

Every rerun creates a new analysis and new findings. Historical runs and human review events are not rewritten.

