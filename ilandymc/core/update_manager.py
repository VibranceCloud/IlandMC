from __future__ import annotations
import hashlib, json, os, re, subprocess, sys, tempfile, zipfile
from email.parser import Parser
from pathlib import Path
from urllib.parse import urlparse
import httpx
from ilandymc import __version__

class UpdateError(RuntimeError): pass

class UpdateManager:
    def __init__(self, manifest_url: str | None, install_root: Path = Path("/opt/ily")):
        self.manifest_url = manifest_url
        self.install_root = Path(install_root)

    def fetch_manifest(self):
        if not self.manifest_url: raise UpdateError("Update manifest URL is not configured")
        parsed = urlparse(self.manifest_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise UpdateError("Update manifest must use HTTPS and contain no credentials")
        try:
            with httpx.Client(timeout=15, follow_redirects=False) as client:
                response = client.get(self.manifest_url, headers={"User-Agent": "IlandyMC-Updater/0.7"})
                response.raise_for_status()
                data = response.json()
        except Exception as exc: raise UpdateError(f"Cannot retrieve update manifest: {exc}") from exc
        if not isinstance(data, dict): raise UpdateError("Invalid update manifest")
        version, url, digest = data.get("version"), data.get("url"), data.get("sha256")
        if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
            raise UpdateError("Invalid release version in manifest")
        parsed_release = urlparse(url) if isinstance(url, str) else None
        if (not parsed_release or parsed_release.scheme != "https" or not parsed_release.hostname
                or parsed_release.username or parsed_release.password):
            raise UpdateError("Release URL must use HTTPS and contain no credentials")
        if not isinstance(digest, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", digest):
            raise UpdateError("Manifest must provide a SHA-256 digest")
        return {"version": version, "url": url, "sha256": digest.lower()}

    def check(self):
        release = self.fetch_manifest()
        return {**release, "update_available": self._version_key(release["version"]) > self._version_key(__version__)}

    @staticmethod
    def _version_key(value): return tuple(int(x) for x in value.split("."))

    def apply(self, release):
        if not release.get("update_available"): return False
        if not (self.install_root / "venv" / "bin" / "python").is_file():
            raise UpdateError("Managed /opt/ily virtual environment not found")
        self.install_root.mkdir(parents=True, exist_ok=True)
        fd, archive = tempfile.mkstemp(prefix=".ily-update-", suffix=".whl", dir=self.install_root)
        os.close(fd)
        try:
            digest = hashlib.sha256()
            with httpx.stream("GET", release["url"], timeout=60, follow_redirects=False,
                              headers={"User-Agent": "IlandyMC-Updater/0.7"}) as response:
                response.raise_for_status()
                with open(archive, "wb") as out:
                    total = 0
                    for chunk in response.iter_bytes():
                        total += len(chunk)
                        if total > 100 * 1024 * 1024: raise UpdateError("Update wheel exceeds 100 MiB")
                        digest.update(chunk); out.write(chunk)
            if digest.hexdigest() != release["sha256"]:
                raise UpdateError("Update wheel SHA-256 mismatch")
            try:
                with zipfile.ZipFile(archive) as wheel:
                    metadata_files = [n for n in wheel.namelist()
                                      if n.endswith('.dist-info/METADATA') and n.count('/') == 1]
                    if len(metadata_files) != 1:
                        raise UpdateError("Wheel must contain exactly one distribution METADATA file")
                    metadata = Parser().parsestr(wheel.read(metadata_files[0]).decode('utf-8'))
                    if metadata.get('Name', '').lower().replace('_', '-') != 'ilandymc' or metadata.get('Version') != release['version']:
                        raise UpdateError("Wheel name/version does not match update manifest")
            except (zipfile.BadZipFile, UnicodeDecodeError, KeyError) as exc:
                raise UpdateError("Downloaded update is not a valid Python wheel") from exc
            python = self.install_root / "venv" / "bin" / "python"
            result = subprocess.run([str(python), "-m", "pip", "install", "--no-deps", "--no-index",
                                     "--force-reinstall", archive], capture_output=True, text=True)
            if result.returncode: raise UpdateError((result.stderr or result.stdout or "pip failed").strip())
            return True
        finally:
            Path(archive).unlink(missing_ok=True)
