from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="IMAGE_TRACE_", env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./image-trace.db"
    storage_root: Path = Path("../../storage")
    allowed_origins: str = "http://localhost:5173"
    max_file_mib: int = 100
    max_batch_files: int = 200
    max_megapixels: int = 100
    online_tiles_enabled: bool = False

    @property
    def origins(self) -> list[str]:
        return [value.strip() for value in self.allowed_origins.split(",") if value.strip()]


settings = Settings()
