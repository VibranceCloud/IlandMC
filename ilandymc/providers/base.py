from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict, Field, model_validator
import httpx
from urllib.parse import urlparse

class Artifact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    software: str
    minecraft_version: str
    build: str
    download_url: str
    checksum: str | None = None
    checksum_algorithm: str | None = None
    filename: str = Field(default="server.jar", pattern=r"^[A-Za-z0-9._-]+$")

    @model_validator(mode="after")
    def validate_security(self):
        parsed = urlparse(self.download_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Artifact download URL must use HTTPS without credentials")
        if self.checksum and not self.checksum_algorithm:
            raise ValueError("Checksum algorithm must be specified when checksum is present")
        if self.checksum_algorithm and self.checksum_algorithm not in ("sha1", "sha256", "sha512"):
            raise ValueError("Unsupported artifact checksum algorithm")
        return self

class Provider(ABC):
    name: str
    def __init__(self, client=None):
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(30, connect=10), follow_redirects=True,
            headers={"User-Agent": "IlandyMC/0.5.0 (+https://github.com/VibranceCloud/IlandyMC)"})
    @abstractmethod
    async def versions(self) -> list[str]: ...
    @abstractmethod
    async def latest_artifact(self, version: str) -> Artifact: ...
    async def close(self):
        if self._owns_client:
            await self.client.aclose()
