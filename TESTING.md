# IlandyMC test guide

## Run locally

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m compileall -q ilandymc tests
pytest -q
ilandy --help
ilandy install --help
```

The test suite is deliberately offline. It never contacts Mojang/Paper/Fabric services and never
starts a real Minecraft server. It uses fake provider responses, temporary directories and a
short-lived fake Java launcher.

## Coverage focus

- provider registry and artifact URL/checksum policy;
- installer EULA gate, mocked download, atomic no-overwrite commit and generated RCON config;
- metadata path validation and server identity/PID reuse defenses;
- actual subprocess start/status/stop using a fake launcher;
- backup/restore round-trip, symlink rejection, tamper detection and traversal rejection;
- systemd unit injection validation.

## Before production rollout

Run the separate VM acceptance plan in `RELEASE_CHECKLIST.md` on clean Debian 12 and Ubuntu 24.04
machines. Include a real Paper and Vanilla install, first boot, RCON stop, restart after reboot,
backup/restore, permissions audit, and a test with a non-root service account.
