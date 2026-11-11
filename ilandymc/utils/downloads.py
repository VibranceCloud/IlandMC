import hashlib, os, tempfile
from pathlib import Path
from urllib.parse import urlparse
import httpx

async def download_verified(url: str, destination: Path, checksum: str | None = None,
                            checksum_algorithm: str = "sha256", timeout=180,
                            max_bytes: int = 2_000_000_000):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Artifact URL must be an HTTPS URL without embedded credentials")
    if checksum_algorithm not in hashlib.algorithms_available:
        raise ValueError("Unsupported checksum algorithm")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(destination)
    fd, tmp = tempfile.mkstemp(prefix=".download-", dir=destination.parent)
    digest = hashlib.new(checksum_algorithm)
    total = 0
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=15),
                                     follow_redirects=True, max_redirects=5) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                if response.url.scheme != "https":
                    raise ValueError("Artifact redirect downgraded from HTTPS")
                length = response.headers.get("content-length")
                if length and int(length) > max_bytes:
                    raise ValueError("Artifact exceeds configured size limit")
                with os.fdopen(fd, "wb") as out:
                    async for chunk in response.aiter_bytes(1024 * 1024):
                        total += len(chunk)
                        if total > max_bytes:
                            raise ValueError("Artifact exceeds configured size limit")
                        out.write(chunk); digest.update(chunk)
                    out.flush(); os.fsync(out.fileno())
        actual = digest.hexdigest()
        if checksum and actual.lower() != checksum.lower():
            raise ValueError(f"{checksum_algorithm.upper()} checksum mismatch")
        os.chmod(tmp, 0o640)
        os.replace(tmp, destination)
        return actual
    except Exception:
        try: os.close(fd)
        except OSError: pass
        Path(tmp).unlink(missing_ok=True)
        raise
