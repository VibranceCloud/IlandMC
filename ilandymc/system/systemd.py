from __future__ import annotations
import os, pwd, re, shutil, subprocess, tempfile
from pathlib import Path
UNIT_DIR = Path('/etc/systemd/system')

def _safe_atom(value, label):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.@-]+', value):
        raise ValueError(f'Invalid {label}')
    return value

def _safe_path(path, label):
    path = Path(path).resolve()
    value = str(path)
    if not value.startswith('/') or any(c.isspace() or c in '\n\r\t' for c in value):
        raise ValueError(f'{label} must be an absolute path without whitespace')
    return path

def render_unit(name, working_directory, user='minecraft', java='java', memory_mb=2048,
                jar='server.jar', restart='on-failure', restart_sec=10, stop_timeout=120):
    name = _safe_atom(name, 'unit name'); user = _safe_atom(user, 'service user')
    if not isinstance(jar, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+\.jar', jar):
        raise ValueError('Invalid jar filename')
    if not isinstance(memory_mb, int) or isinstance(memory_mb, bool) or not 512 <= memory_mb <= 1_000_000:
        raise ValueError('Invalid memory limit')
    if restart not in ('no', 'on-failure', 'always'): raise ValueError('Invalid restart policy')
    if not isinstance(restart_sec, int) or not 1 <= restart_sec <= 300: raise ValueError('Invalid restart delay')
    if not isinstance(stop_timeout, int) or not 10 <= stop_timeout <= 600: raise ValueError('Invalid stop timeout')
    wd = _safe_path(working_directory, 'working directory')
    java_path = shutil.which(java) if '/' not in java else str(Path(java).resolve())
    if not java_path: raise ValueError('Java executable not found')
    java_path = _safe_path(java_path, 'Java executable')
    return f'''[Unit]
Description=IlandyMC Minecraft server {name}
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User={user}
Group={user}
WorkingDirectory={wd}
ExecStart={java_path} -Xms{memory_mb}M -Xmx{memory_mb}M -jar {jar} nogui
Restart={restart}
RestartSec={restart_sec}
KillSignal=SIGTERM
TimeoutStopSec={stop_timeout}
SuccessExitStatus=0 143
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths={wd}
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
LockPersonality=true
LimitNOFILE=65535
UMask=0027

[Install]
WantedBy=multi-user.target
'''

def systemd_available():
    return Path('/run/systemd/system').exists() and shutil.which('systemctl') is not None and subprocess.run(
        ['systemctl', '--version'], capture_output=True, check=False).returncode == 0

class SystemdError(RuntimeError): pass

class SystemdManager:
    def __init__(self, unit_dir=UNIT_DIR, runner=subprocess.run):
        self.unit_dir = Path(unit_dir); self.runner = runner
    @staticmethod
    def unit_name(name): return f"ilandymc-{_safe_atom(name, 'server name')}.service"
    def _run(self, args):
        result = self.runner(args, capture_output=True, text=True, check=False)
        if result.returncode:
            raise SystemdError((result.stderr or result.stdout or 'systemctl failed').strip())
        return result
    @staticmethod
    def ensure_service_user(username):
        _safe_atom(username, 'service user')
        try: account = pwd.getpwnam(username)
        except KeyError:
            if os.geteuid() != 0: raise SystemdError('Root privileges required to create service account')
            result = subprocess.run(['useradd','--system','--user-group','--home-dir','/nonexistent',
                '--no-create-home','--shell','/usr/sbin/nologin',username],capture_output=True,text=True,check=False)
            if result.returncode: raise SystemdError((result.stderr or 'useradd failed').strip())
            account = pwd.getpwnam(username)
        if account.pw_uid == 0: raise SystemdError('Refusing to run Minecraft as root')
        return account
    def install(self, name, working_directory, user='minecraft', java='java', memory_mb=2048,
                jar='server.jar', enable=True):
        if os.geteuid() != 0: raise SystemdError('Root privileges required to install system services')
        if not systemd_available(): raise SystemdError('systemd is not available on this host')
        unit = self.unit_name(name); account = self.ensure_service_user(user)
        wd = _safe_path(working_directory, 'working directory')
        if not wd.is_dir(): raise SystemdError('Server directory does not exist')
        content = render_unit(name, wd, user, java, memory_mb, jar)
        # Reject symlinks before changing any ownership.
        for current, dirs, files in os.walk(wd, followlinks=False):
            for entry in dirs + files:
                if (Path(current) / entry).is_symlink(): raise SystemdError('Symlinks are not allowed in server directory')
        for current, dirs, files in os.walk(wd, followlinks=False):
            for entry in dirs + files: os.chown(Path(current) / entry, account.pw_uid, account.pw_gid)
        os.chown(wd, account.pw_uid, account.pw_gid)
        # The service account needs execute permission on the managed registry parent.
        os.chmod(wd.parent, 0o755)
        self.unit_dir.mkdir(parents=True, exist_ok=True); destination = self.unit_dir / unit
        if destination.exists(): raise SystemdError(f'Unit already exists: {destination}')
        fd, tmp = tempfile.mkstemp(prefix=f'.{unit}.', dir=self.unit_dir, text=True)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                stream.write(content); stream.flush(); os.fsync(stream.fileno())
            os.chmod(tmp, 0o644); os.replace(tmp, destination)
            self._run(['systemctl','daemon-reload'])
            if enable: self._run(['systemctl','enable','--now',unit])
            return destination
        except Exception:
            Path(tmp).unlink(missing_ok=True); destination.unlink(missing_ok=True)
            try: self._run(['systemctl','daemon-reload'])
            except Exception: pass
            raise
    def uninstall(self, name):
        if os.geteuid() != 0: raise SystemdError('Root privileges required to remove system services')
        if not systemd_available(): raise SystemdError('systemd is not available on this host')
        unit = self.unit_name(name); self._run(['systemctl','disable','--now',unit])
        destination = self.unit_dir / unit; destination.unlink(missing_ok=True)
        self._run(['systemctl','daemon-reload']); return destination
    def status(self, name):
        if not systemd_available(): raise SystemdError('systemd is not available on this host')
        result = self.runner(['systemctl','is-active',self.unit_name(name)],capture_output=True,text=True,check=False)
        return (result.stdout or result.stderr or 'unknown').strip()
    def installed(self, name):
        return (self.unit_dir / self.unit_name(name)).is_file()

    def start(self, name):
        if not systemd_available(): raise SystemdError('systemd is not available on this host')
        self._run(['systemctl', 'start', self.unit_name(name)])

    def stop(self, name):
        if not systemd_available(): raise SystemdError('systemd is not available on this host')
        self._run(['systemctl', 'stop', self.unit_name(name)])

    def restart(self, name):
        if not systemd_available(): raise SystemdError('systemd is not available on this host')
        self._run(['systemctl', 'restart', self.unit_name(name)])

    def refresh(self, name, working_directory, java='java', memory_mb=2048, jar='server.jar'):
        """Regenerate an existing managed unit after offline server setting changes."""
        if os.geteuid() != 0: raise SystemdError('Root privileges required to update a system service')
        if not systemd_available(): raise SystemdError('systemd is not available on this host')
        unit = self.unit_name(name); destination = self.unit_dir / unit
        if not destination.is_file(): return False
        old = destination.read_text(encoding='utf-8')
        match = re.search(r'^User=([^\n]+)$', old, re.M)
        user = match.group(1) if match else 'minecraft'
        content = render_unit(name, working_directory, user, java, memory_mb, jar)
        fd, tmp = tempfile.mkstemp(prefix=f'.{unit}.', dir=self.unit_dir, text=True)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                stream.write(content); stream.flush(); os.fsync(stream.fileno())
            os.chmod(tmp, 0o644); os.replace(tmp, destination)
            self._run(['systemctl', 'daemon-reload'])
            return True
        except Exception:
            Path(tmp).unlink(missing_ok=True)
            raise

