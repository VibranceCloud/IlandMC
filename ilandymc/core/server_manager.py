import json, os, signal, subprocess, time, tempfile
from pathlib import Path

class ServerError(RuntimeError): pass

class ServerManager:
    def __init__(self, root=Path("/opt/ilandy/servers")):
        self.root = Path(root).resolve()
    def server_path(self, name):
        if not name or name in (".", "..") or "/" in name or "\\" in name:
            raise ValueError("Invalid server name")
        path = (self.root / name).resolve()
        if path.parent != self.root: raise ValueError("Server path escapes registry")
        return path
    def list(self):
        if not self.root.exists(): return []
        return sorted(p.name for p in self.root.iterdir()
                      if p.is_dir() and (p / "ilandy.json").is_file())
    def metadata(self, name):
        p = self.server_path(name) / "ilandy.json"
        if not p.is_file(): raise ServerError(f"Unknown server {name}")
        try: data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc: raise ServerError("Invalid server metadata") from exc
        if data.get("name") != name or data.get("schema_version") != 1:
            raise ServerError("Server metadata mismatch or unsupported schema")
        if not isinstance(data.get("memory_mb"), int) or not 512 <= data["memory_mb"] <= 1_000_000:
            raise ServerError("Invalid memory setting in metadata")
        jar = data.get("jar")
        if not isinstance(jar, str) or Path(jar).name != jar: raise ServerError("Unsafe jar path")
        java = data.get("java", "java")
        if not isinstance(java, str) or not java or "\0" in java: raise ServerError("Invalid Java executable")
        port = data.get("game_port", 25565)
        if not isinstance(port, int) or isinstance(port, bool) or not 1024 <= port <= 65535:
            raise ServerError("Invalid game port in metadata")
        return data
    def _pid_record(self, name):
        p = self.server_path(name) / "server.pid"
        try: record = json.loads(p.read_text())
        except (OSError, ValueError, TypeError): return None
        if not isinstance(record, dict) or not isinstance(record.get("pid"), int): return None
        return record
    @staticmethod
    def _proc_info(pid):
        base = Path(f"/proc/{pid}")
        try:
            raw = (base / "stat").read_text()
            # comm may contain spaces and ')' so split after its final closing parenthesis.
            tail = raw[raw.rfind(")") + 2:].split()
            state, start_ticks = tail[0], int(tail[19])
            cmd = (base / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
            cwd = (base / "cwd").resolve()
            return {"state": state, "start_ticks": start_ticks, "cmd": cmd, "cwd": cwd}
        except (OSError, ValueError, IndexError, ProcessLookupError):
            return None
    def _identity_matches(self, record, path):
        info = self._proc_info(record["pid"])
        if not info or info["state"] == "Z": return False
        if record.get("start_ticks") is not None and info["start_ticks"] != record["start_ticks"]:
            return False
        return str(path.resolve()) in info["cmd"] and info["cwd"] == path.resolve()
    def status(self, name):
        path = self.server_path(name); self.metadata(name)
        rec = self._pid_record(name)
        if not rec: return "stopped"
        info = self._proc_info(rec["pid"])
        if info is None or info["state"] == "Z": return "stopped"
        if not self._identity_matches(rec, path):
            raise ServerError("PID file exists but process identity cannot be verified")
        return "running"
    def start(self, name):
        path = self.server_path(name); meta = self.metadata(name)
        if self.status(name) == "running": return
        jar = path / meta["jar"]
        if not jar.is_file(): raise ServerError("Server jar missing")
        java = meta.get("java", "java")
        if "/" in java and not Path(java).is_file(): raise ServerError("Java executable missing")
        log = (path / "server.log").open("ab")
        try:
            proc = subprocess.Popen([java, f"-Xms{meta['memory_mb']}M",
                f"-Xmx{meta['memory_mb']}M", "-jar", str(jar), "nogui"],
                cwd=path, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True, close_fds=True, env={**os.environ, "LANG":"C.UTF-8"})
        finally: log.close()
        info = None
        for _ in range(20):
            info = self._proc_info(proc.pid)
            if info: break
            time.sleep(.025)
        if not info or info["state"] == "Z":
            raise ServerError(f"Server exited during startup; inspect {path/'server.log'}")
        record = json.dumps({"pid": proc.pid, "started_at": time.time(),
                             "start_ticks": info["start_ticks"]}) + "\n"
        fd, tmp = tempfile.mkstemp(prefix=".pid-", dir=path)
        try:
            with os.fdopen(fd, "w") as f: f.write(record); f.flush(); os.fsync(f.fileno())
            os.chmod(tmp, 0o640); os.replace(tmp, path / "server.pid")
        except Exception:
            Path(tmp).unlink(missing_ok=True)
            try: os.kill(proc.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            raise
        time.sleep(0.1)
        if self.status(name) != "running":
            (path / "server.pid").unlink(missing_ok=True)
            raise ServerError(f"Server exited during startup; inspect {path/'server.log'}")
    def stop(self, name, timeout=90):
        path = self.server_path(name); self.metadata(name)
        rec = self._pid_record(name)
        if not rec: return
        if not self._identity_matches(rec, path):
            info = self._proc_info(rec["pid"])
            if info is None or info["state"] == "Z":
                (path / "server.pid").unlink(missing_ok=True); return
            raise ServerError("PID identity could not be verified; refusing to signal process")
        pid = rec["pid"]
        secret = path / "rcon.secret"
        rcon_sent = False
        rcon_enabled = True
        properties_file = path / "server.properties"
        if properties_file.is_file():
            from .properties import parse_properties
            configured, _ = parse_properties(properties_file.read_text(encoding="utf-8"))
            rcon_enabled = configured.get("enable-rcon", "false").lower() == "true"
        if secret.is_file() and rcon_enabled:
            try:
                from .rcon import RCONClient
                meta = self.metadata(name)
                RCONClient("127.0.0.1", meta["rcon_port"], secret.read_text().strip()).command("stop")
                rcon_sent = True
            except Exception:
                pass
        deadline = time.monotonic() + timeout
        if not rcon_sent:
            try: os.kill(pid, signal.SIGTERM)
            except ProcessLookupError: pass
        while time.monotonic() < deadline:
            info = self._proc_info(pid)
            expected_ticks = rec.get("start_ticks")
            if info is None or info["state"] == "Z" or (expected_ticks is not None and info["start_ticks"] != expected_ticks):
                (path / "server.pid").unlink(missing_ok=True); return
            if rcon_sent and time.monotonic() + 2 >= deadline:
                try: os.kill(pid, signal.SIGTERM)
                except ProcessLookupError: pass
            time.sleep(.25)
        raise ServerError("Graceful stop timed out; process left running")

    def supported_specs(self, name):
        """Catalogue entries supported by this server's own generated properties."""
        from .properties import SPECS, parse_properties
        path = self.server_path(name)
        self.metadata(name)
        prop = path / "server.properties"
        if not prop.is_file():
            raise ServerError("server.properties is missing")
        values, _ = parse_properties(prop.read_text(encoding="utf-8"))
        meta = self.metadata(name)
        # New installs record the detected set. Legacy installs are conservatively
        # limited to keys actually present in their existing file.
        detected = meta.get("supported_properties")
        supported = set(detected) if isinstance(detected, list) else set(values)
        return tuple(spec for spec in SPECS if spec.key in supported and spec.key in values)

    def properties(self, name):
        """Return only properties present in this server build's own file."""
        from .properties import parse_properties
        path = self.server_path(name) / "server.properties"
        if not path.is_file():
            raise ServerError("server.properties is missing")
        try:
            values, _ = parse_properties(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ServerError("Cannot read server.properties") from exc
        return values

    def set_properties(self, name, updates):
        """Update only properties detected in the target server's generated file."""
        from .properties import SPEC_BY_KEY, parse_properties, serialize_detected_properties
        if not isinstance(updates, dict) or not updates:
            raise ValueError("Provide at least one property to update")
        path = self.server_path(name)
        meta = self.metadata(name)
        if self.status(name) == "running":
            raise ServerError("Stop the server before editing server.properties")
        from ..system.systemd import SystemdManager
        service = SystemdManager()
        if service.installed(name):
            try:
                state = service.status(name)
            except Exception as exc:
                raise ServerError("Cannot verify systemd service state; refusing to edit properties") from exc
            if state not in ("inactive", "failed", "dead"):
                raise ServerError(f"Systemd service state is {state!r}; refusing to edit properties")
        prop = path / "server.properties"
        if not prop.is_file():
            raise ServerError("server.properties is missing")
        values, _ = parse_properties(prop.read_text(encoding="utf-8"))
        supported = {spec.key for spec in self.supported_specs(name)}
        for key, raw in updates.items():
            if key not in SPEC_BY_KEY:
                raise ValueError(f"Unsupported property: {key}")
            if key not in supported:
                raise ValueError(f"Property {key} is not supported by this server version")
            spec = SPEC_BY_KEY[key]
            value = str(raw).strip()
            if spec.kind == "bool":
                if value.lower() not in ("true", "false"):
                    raise ValueError(f"{key} must be true or false")
                value = value.lower()
            elif spec.kind == "int":
                try: number = int(value)
                except ValueError as exc: raise ValueError(f"{key} must be an integer") from exc
                if spec.minimum is not None and number < spec.minimum:
                    raise ValueError(f"{key} must be >= {spec.minimum}")
                if spec.maximum is not None and number > spec.maximum:
                    raise ValueError(f"{key} must be <= {spec.maximum}")
                value = str(number)
            elif spec.kind == "enum" and value not in spec.choices:
                raise ValueError(f"{key} must be one of: {', '.join(spec.choices)}")
            if "\n" in value or "\r" in value:
                raise ValueError(f"{key} cannot contain a newline")
            values[key] = value
        if "server-port" in updates:
            meta["game_port"] = int(values["server-port"])
        if "rcon.port" in updates:
            meta["rcon_port"] = int(values["rcon.port"])
        if "rcon.password" in updates:
            secret = path / "rcon.secret"
            _atomic_text(secret, values["rcon.password"] + "\n", 0o600)
        _atomic_text(prop, serialize_detected_properties(values, list(values)), 0o640)
        if any(key in updates for key in ("server-port", "rcon.port", "rcon.password")):
            _atomic_text(path / "ilandy.json", json.dumps(meta, indent=2) + "\n", 0o640)
        return values

    def configure(self, name, memory_mb=None, game_port=None):
        """Change launch memory and gameplay port only while the server is stopped."""
        import tempfile
        path = self.server_path(name)
        data = self.metadata(name)
        if self.status(name) == "running":
            raise ServerError("Stop the server before changing its settings")
        if memory_mb is not None and (not isinstance(memory_mb, int) or isinstance(memory_mb, bool)
                                      or not 512 <= memory_mb <= 1_000_000):
            raise ValueError("Memory must be between 512 and 1000000 MiB")
        if game_port is not None and (not isinstance(game_port, int) or isinstance(game_port, bool)
                                      or not 1024 <= game_port <= 65535):
            raise ValueError("Port must be between 1024 and 65535")
        if memory_mb is not None: data["memory_mb"] = memory_mb
        if game_port is not None:
            prop = path / "server.properties"
            from .properties import parse_properties
            current_values, _ = parse_properties(prop.read_text(encoding="utf-8"))
            if "server-port" not in current_values:
                raise ValueError("This server version does not expose server-port")
            data["game_port"] = game_port
            lines = prop.read_text(encoding="utf-8").splitlines() if prop.exists() else []
            found = False; output = []
            for line in lines:
                if line.startswith("server-port="):
                    if not found: output.append(f"server-port={game_port}"); found = True
                else: output.append(line)
            if found:
                _atomic_text(prop, "\n".join(output) + "\n", 0o640)
        _atomic_text(path / "ilandy.json", json.dumps(data, indent=2) + "\n", 0o640)
        return data

def _atomic_text(path, content, mode):
    fd, tmp = tempfile.mkstemp(prefix=".settings-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content); stream.flush(); os.fsync(stream.fileno())
        os.chmod(tmp, mode); os.replace(tmp, path)
    except Exception:
        Path(tmp).unlink(missing_ok=True); raise

