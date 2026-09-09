# ADR 0001: Local-first storage and bounded in-process jobs

SQLite WAL mode and controlled filesystem roots satisfy the MVP without mandatory cloud services. Durable job rows expose truthful status and permit restart recovery while bounded local work avoids Redis/Celery complexity. The repository and service boundaries keep later PostgreSQL or external job execution possible without moving domain behavior into routes.

