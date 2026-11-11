import hashlib, json, os, tarfile, tempfile, time, shutil, hmac
from pathlib import Path
from .server_manager import ServerManager

def _sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""): h.update(chunk)
    return h.hexdigest()

class BackupManager:
    def __init__(self, root=Path("/opt/ilandy/backups"), servers=Path("/opt/ilandy/servers")):
        self.root = Path(root).resolve(); self.manager = ServerManager(servers)
    def create(self, name):
        source = self.manager.server_path(name); self.manager.metadata(name)
        if self.manager.status(name) == "running":
            raise RuntimeError("Stop server before backup for a consistent snapshot")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        target = self.root / f"{name}-{time.strftime('%Y%m%dT%H%M%S', time.gmtime())}-{time.time_ns()}-{os.getpid()}.tar.gz"
        fd, tmp = tempfile.mkstemp(dir=self.root, prefix=".backup-"); os.close(fd)
        try:
            with tarfile.open(tmp, "w:gz") as tar:
                for item in sorted(source.rglob("*")):
                    if item.is_symlink(): raise ValueError(f"Refusing to back up symlink: {item}")
                    if item.is_file() or item.is_dir():
                        tar.add(item, arcname=str(Path(name) / item.relative_to(source)), recursive=False)
            digest = _sha256(tmp); os.chmod(tmp, 0o600); os.replace(tmp, target)
            side_tmp = target.with_suffix(target.suffix + ".sha256.tmp")
            side_tmp.write_text(digest + "  " + target.name + "\n")
            os.chmod(side_tmp, 0o600); os.replace(side_tmp, target.with_suffix(target.suffix + ".sha256"))
            return target
        except Exception:
            Path(tmp).unlink(missing_ok=True); raise
    def restore(self, archive, name):
        archive = Path(archive).resolve()
        dest = self.manager.server_path(name)
        if dest.exists() and self.manager.status(name) == "running":
            raise RuntimeError("Stop server before restore")
        if not archive.is_file(): raise FileNotFoundError(archive)
        side = archive.with_suffix(archive.suffix + ".sha256")
        if not side.is_file(): raise ValueError("Backup checksum missing")
        expected = side.read_text().split()[0]
        if not hmac.compare_digest(expected, _sha256(archive)): raise ValueError("Backup checksum mismatch")
        if dest.exists(): raise FileExistsError("Restore never overwrites an existing server")
        self.manager.root.mkdir(parents=True, exist_ok=True, mode=0o750)
        staging = Path(tempfile.mkdtemp(prefix=f".{name}.restore-", dir=self.manager.root))
        try:
            with tarfile.open(archive, "r:gz") as tar:
                members = tar.getmembers()
                for member in members:
                    rel = Path(member.name)
                    if rel.is_absolute() or ".." in rel.parts or not rel.parts or rel.parts[0] != name:
                        raise ValueError("Unsafe archive member path")
                    if not (member.isdir() or member.isfile()):
                        raise ValueError("Backup contains a link or special file")
                tar.extractall(staging, members=members, filter="data")
            extracted = staging / name
            if not (extracted / "ilandy.json").is_file(): raise ValueError("Invalid server backup")
            meta = json.loads((extracted / "ilandy.json").read_text())
            if meta.get("name") != name or meta.get("schema_version") != 1:
                raise ValueError("Backup server identity mismatch")
            os.rename(extracted, dest); return dest
        finally:
            shutil.rmtree(staging, ignore_errors=True)
