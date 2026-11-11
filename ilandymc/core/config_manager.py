import os, tempfile
from pathlib import Path
import yaml
from platformdirs import user_config_path
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from urllib.parse import urlparse

class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = 1
    language: str = Field(default="en", pattern="^(en|ru)$")
    auto_update: bool = False
    update_manifest_url: str | None = None

    @field_validator("update_manifest_url")
    @classmethod
    def validate_manifest_url(cls, value):
        if value is not None:
            parsed = urlparse(value)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError("Update manifest URL must be HTTPS and contain no credentials")
        return value

    @model_validator(mode="after")
    def require_manifest_when_auto_update_enabled(self):
        if self.auto_update and not self.update_manifest_url:
            raise ValueError("update_manifest_url is required when auto_update is enabled")
        return self

class ConfigManager:
    def __init__(self, path=None):
        self.path = Path(path) if path else Path(user_config_path("IlandyMC", "VibranceCloud")) / "config.yml"
    def load(self):
        if not self.path.exists(): return AppConfig()
        try: return AppConfig.model_validate(yaml.safe_load(self.path.read_text()) or {})
        except Exception as exc: raise RuntimeError(f"Invalid config {self.path}: {exc}") from exc
    def save(self, config):
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd, tmp = tempfile.mkstemp(prefix=".config-", dir=self.path.parent)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w") as f:
                yaml.safe_dump(config.model_dump(), f, sort_keys=True); f.flush(); os.fsync(f.fileno())
            os.replace(tmp, self.path); os.chmod(self.path, 0o600)
        except Exception:
            try: os.unlink(tmp)
            except FileNotFoundError: pass
            raise
