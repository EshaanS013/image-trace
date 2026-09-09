# Data model

`cases` own evidence, analyses, jobs, custody events, and reports. `evidence_files` identify a controlled original by an opaque storage key and own one `image_metadata` record plus notes. `analysis_runs` are immutable snapshots of analyzer, rule-set, application, build, and canonical hashed configuration. Findings belong to one run and optionally relate two evidence items. Finding review events preserve every human state transition. Reports reference one completed run.

Foreign keys use restrictive or cascading behavior appropriate to ownership, and common case/status/time lookups are indexed. Case numbers and storage keys are unique. UUIDs prevent submitted names from becoming paths.

## Timestamp policy

Raw values remain stored when normalization fails. Priority is DateTimeOriginal, DateTimeDigitized, GPS UTC date/time, then source filesystem modification time. Filename ordering is reserved as the documented lowest-confidence option. A timezone-naive embedded timestamp remains local/unknown and has no UTC value unless a valid case-level IANA timezone assumption is applied; that assumption is labelled and retained in analysis configuration.

