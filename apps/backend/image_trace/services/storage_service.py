from pathlib import Path, PurePath

from ..config import settings


class StorageService:
    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or settings.storage_root).resolve()

    def ensure_roots(self) -> None:
        for folder in ("originals", "derivatives", "reports", "exports"):
            (self.root / folder).mkdir(parents=True, exist_ok=True)

    def resolve(self, key: str) -> Path:
        if PurePath(key).is_absolute() or ".." in PurePath(key).parts:
            raise ValueError("Unsafe storage key")
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Storage path escapes configured root")
        return path

    def original_path(self, case_id: str, evidence_id: str) -> tuple[str, Path]:
        key = f"originals/{case_id}/{evidence_id}/original-file"
        return key, self.resolve(key)

    def thumbnail_path(self, case_id: str, evidence_id: str) -> tuple[str, Path]:
        key = f"derivatives/{case_id}/{evidence_id}/thumbnail.webp"
        return key, self.resolve(key)


storage = StorageService()
