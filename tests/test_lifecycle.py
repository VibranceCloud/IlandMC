import json, os, time
from pathlib import Path
import pytest
from ilandymc.core.server_manager import ServerManager, ServerError

def server(root, launcher):
    p = root / "testworld"; p.mkdir(parents=True)
    (p / "server.jar").write_text("test")
    (p / "ilandy.json").write_text(json.dumps({
        "schema_version": 1, "name": "testworld", "jar": "server.jar",
        "memory_mb": 512, "java": str(launcher)
    }))
    return p

def test_real_subprocess_start_status_stop(tmp_path):
    launcher = tmp_path / "fake-java"
    launcher.write_text("#!/bin/bash\nexec -a \"$PWD/server.jar\" sleep 30\n")
    launcher.chmod(0o755)
    server(tmp_path, launcher)
    manager = ServerManager(tmp_path)
    manager.start("testworld")
    assert manager.status("testworld") == "running"
    record = json.loads((tmp_path / "testworld" / "server.pid").read_text())
    assert record["start_ticks"] > 0
    manager.stop("testworld", timeout=3)
    assert manager.status("testworld") == "stopped"

def test_pid_reuse_or_wrong_process_never_signalled(tmp_path):
    launcher = tmp_path / "fake-java"
    launcher.write_text("#!/bin/bash\nexec -a unrelated-process sleep 30\n")
    launcher.chmod(0o755)
    p = server(tmp_path, launcher)
    import subprocess
    proc = subprocess.Popen(["sleep", "30"], cwd=p)
    try:
        (p / "server.pid").write_text(json.dumps({"pid": proc.pid, "start_ticks": 1}))
        manager = ServerManager(tmp_path)
        with pytest.raises(ServerError):
            manager.stop("testworld", timeout=1)
        assert proc.poll() is None
    finally:
        proc.terminate(); proc.wait(timeout=3)

def test_unknown_server_fails_closed(tmp_path):
    with pytest.raises(ServerError):
        ServerManager(tmp_path).status("not-here")


def test_status_detects_pid_file_for_unrelated_live_process(tmp_path):
    import subprocess
    p=server(tmp_path, tmp_path/"unused")
    proc=subprocess.Popen(["sleep","30"],cwd=p)
    try:
        (p/"server.pid").write_text(json.dumps({"pid":proc.pid}))
        with pytest.raises(ServerError):
            ServerManager(tmp_path).status("testworld")
    finally:
        proc.terminate(); proc.wait(timeout=3)
