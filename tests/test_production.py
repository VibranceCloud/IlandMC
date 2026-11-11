import json
from pathlib import Path
import pytest
from ilandymc.providers.base import Artifact
from ilandymc.core.server_manager import ServerManager, ServerError
from ilandymc.core.backup_manager import BackupManager
from ilandymc.core.installer import install_server, InstallError
from ilandymc.system.systemd import render_unit

def make_server(root, name="survival"):
    path = root / name
    path.mkdir(parents=True)
    (path / "server.jar").write_bytes(b"jar")
    (path / "ilandy.json").write_text(json.dumps({
        "schema_version": 1, "name": name, "jar": "server.jar",
        "memory_mb": 1024, "software": "paper", "minecraft_version": "1.21.1"
    }))
    return path

def test_metadata_rejects_unsafe_jar(tmp_path):
    make_server(tmp_path)
    m = ServerManager(tmp_path)
    data = json.loads((tmp_path / "survival" / "ilandy.json").read_text())
    data["jar"] = "../outside.jar"
    (tmp_path / "survival" / "ilandy.json").write_text(json.dumps(data))
    with pytest.raises(ServerError): m.metadata("survival")

def test_backup_restore_roundtrip(tmp_path):
    servers = tmp_path / "servers"; backups = tmp_path / "backups"
    make_server(servers)
    archive = BackupManager(backups, servers).create("survival")
    restored_servers = tmp_path / "restored"
    restored = BackupManager(backups, restored_servers).restore(archive, "survival")
    assert (restored / "server.jar").read_bytes() == b"jar"


def test_backup_refuses_running_or_linked_server(tmp_path):
    path = make_server(tmp_path)
    (path / "external").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError):
        BackupManager(tmp_path / "backups", tmp_path).create("survival")

def test_artifact_validates_filename():
    with pytest.raises(Exception):
        Artifact(software="paper", minecraft_version="1.21.1", build="1",
                 download_url="https://example.com/a.jar", filename="../evil.jar")

def test_systemd_rejects_injection():
    with pytest.raises(ValueError):
        render_unit("bad;touch-root", "/tmp/server")


def test_installer_is_eula_gated(tmp_path):
    with pytest.raises(InstallError):
        install_server("survival", "paper", "1.21.1", 2048, root=tmp_path,
                       java="java", accept_eula=False)

def test_installer_transactional_commit(tmp_path, monkeypatch):
    import asyncio
    from ilandymc.core.java_manager import JavaRuntime
    import ilandymc.core.installer as installer
    class FakeProvider:
        async def latest_artifact(self, version):
            return Artifact(software="paper", minecraft_version=version, build="123",
                            download_url="https://example.test/server.jar")
        async def close(self): pass
    monkeypatch.setattr(installer, "inspect_java",
                        lambda executable: JavaRuntime("/usr/bin/java", 21, "test"))
    monkeypatch.setattr(installer, "provider_for", lambda software: FakeProvider())
    async def fake_download(url, destination, **kwargs):
        Path(destination).write_bytes(b"fake-jar")
        return "checksum"
    monkeypatch.setattr(installer, "download_verified", fake_download)
    monkeypatch.setattr(installer, "_bootstrap_properties", lambda *a, **k: {
        "motd": "A Minecraft Server", "server-port": "25565", "online-mode": "true",
        "enable-rcon": "false", "rcon.port": "25575", "rcon.password": "", "rcon.ip": ""
    })
    result = install_server("survival", "paper", "1.21.1", 2048, root=tmp_path,
                            java="java", accept_eula=True)
    meta = json.loads((result / "ilandy.json").read_text())
    assert meta["name"] == "survival" and meta["rcon_port"] > 0
    assert (result / "server.jar").read_bytes() == b"fake-jar"
    assert (result / "rcon.secret").stat().st_mode & 0o777 == 0o600
    properties = (result / "server.properties").read_text()
    assert "rcon.ip=127.0.0.1" in properties
    assert "online-mode=false" in properties
    assert "management-server-enabled=" not in properties
    assert "management-server-secret=" not in properties


def test_download_rejects_plain_http(tmp_path):
    import asyncio
    from ilandymc.utils.downloads import download_verified
    with pytest.raises(ValueError):
        asyncio.run(download_verified("http://example.com/a.jar", tmp_path / "a.jar"))


def test_installer_refuses_existing_empty_directory(tmp_path, monkeypatch):
    import ilandymc.core.installer as installer
    from ilandymc.core.java_manager import JavaRuntime
    monkeypatch.setattr(installer, "inspect_java",
                        lambda executable: JavaRuntime("/usr/bin/java", 21, "test"))
    destination = tmp_path / "survival"
    destination.mkdir()
    with pytest.raises(FileExistsError):
        install_server("survival", "paper", "1.21.1", 2048, root=tmp_path,
                       java="java", accept_eula=True)
    assert destination.is_dir() and list(destination.iterdir()) == []


def test_restore_rejects_tampered_backup(tmp_path):
    servers = tmp_path / "servers"; make_server(servers)
    manager = BackupManager(tmp_path / "backups", servers)
    archive = manager.create("survival")
    archive.write_bytes(archive.read_bytes() + b"tamper")
    with pytest.raises(ValueError, match="checksum"):
        BackupManager(tmp_path / "backups", tmp_path / "restored").restore(archive, "survival")

def test_restore_rejects_path_traversal_even_with_valid_checksum(tmp_path):
    import tarfile, io, hashlib
    backup_dir = tmp_path / "backups"; backup_dir.mkdir()
    archive = backup_dir / "bad.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        data = b"owned"
        info = tarfile.TarInfo("../outside")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(archive.suffix + ".sha256").write_text(digest)
    with pytest.raises(ValueError, match="Unsafe archive"):
        BackupManager(backup_dir, tmp_path / "servers").restore(archive, "survival")
    assert not (tmp_path / "outside").exists()

def test_systemd_unit_has_hardening_and_expected_runtime(tmp_path):
    from ilandymc.system.systemd import render_unit
    unit = render_unit('survival', tmp_path, user='minecraft', java='/usr/bin/java', memory_mb=4096)
    assert 'User=minecraft' in unit and 'Group=minecraft' in unit
    assert 'ProtectSystem=strict' in unit and 'NoNewPrivileges=true' in unit
    assert f'ReadWritePaths={tmp_path.resolve()}' in unit
    assert f"ExecStart={Path('/usr/bin/java').resolve()} -Xms4096M -Xmx4096M -jar server.jar nogui" in unit

def test_systemd_rejects_root_user_and_unsafe_paths():
    from ilandymc.system.systemd import render_unit
    with pytest.raises(ValueError): render_unit('x', '/tmp/a b', java='/usr/bin/java')
    with pytest.raises(ValueError): render_unit('x', '/tmp/x', user='bad;user', java='/usr/bin/java')

def test_systemd_unit_name_is_validated():
    from ilandymc.system.systemd import SystemdManager
    assert SystemdManager.unit_name('survival') == 'ilandymc-survival.service'
    with pytest.raises(ValueError): SystemdManager.unit_name('../bad')

def test_install_persists_custom_game_port(tmp_path, monkeypatch):
    import ilandymc.core.installer as installer
    from ilandymc.core.java_manager import JavaRuntime
    class FakeProvider:
        async def latest_artifact(self, version):
            return Artifact(software='paper', minecraft_version=version, build='123',
                            download_url='https://example.test/server.jar')
        async def close(self): pass
    monkeypatch.setattr(installer, 'inspect_java', lambda executable: JavaRuntime('/usr/bin/java', 25, 'test'))
    monkeypatch.setattr(installer, 'provider_for', lambda software: FakeProvider())
    async def fake_download(url, destination, **kwargs): Path(destination).write_bytes(b'jar'); return 'sum'
    monkeypatch.setattr(installer, 'download_verified', fake_download)
    monkeypatch.setattr(installer, '_bootstrap_properties', lambda *a, **k: {
        'motd': 'A Minecraft Server', 'server-port': '25565', 'online-mode': 'true',
        'enable-rcon': 'false', 'rcon.port': '25575', 'rcon.password': '', 'rcon.ip': ''
    })
    result = install_server('customport', 'paper', '26.1', 1024, root=tmp_path,
                            java='java', accept_eula=True, game_port=25577)
    meta = json.loads((result / 'ilandy.json').read_text())
    assert meta['game_port'] == 25577
    assert 'server-port=25577' in (result / 'server.properties').read_text()

def test_install_rejects_privileged_or_invalid_game_port(tmp_path):
    with pytest.raises(ValueError): install_server('badport', 'paper', '1.21.1', 1024,
        root=tmp_path, game_port=80, dry_run=True)


def test_generated_unit_passes_systemd_analyze_when_available(tmp_path):
    import shutil, subprocess
    from ilandymc.system.systemd import render_unit
    analyzer = shutil.which("systemd-analyze")
    if not analyzer: pytest.skip("systemd-analyze not installed")
    unit = tmp_path / "ilandymc-test.service"
    unit.write_text(render_unit("test", tmp_path, java="/usr/bin/java"))
    result = subprocess.run([analyzer, "verify", str(unit)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

def test_installer_rejects_busy_game_port(tmp_path):
    import socket
    from ilandymc.core.installer import install_server, InstallError
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(('127.0.0.1', 0)); listener.listen()
        port = listener.getsockname()[1]
        with pytest.raises(InstallError, match='unavailable'):
            install_server('busyport', 'paper', '1.21.1', 1024, root=tmp_path,
                           java='java', dry_run=True, game_port=port)
