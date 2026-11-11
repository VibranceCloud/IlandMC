# IlandyMC 1.0.0 release checklist

## Local release checks
- [x] Version metadata aligned at 1.0.0 (`pyproject.toml`, runtime version, README, changelog).
- [x] Existing server-property detection contract retained: only keys emitted by the target server build are editable.
- [x] Unsupported properties are hidden and rejected by the manager/CLI.
- [x] Unknown/native properties are preserved on save.
- [x] New-install defaults are applied only when the generated server file contains the corresponding keys.
- [x] Existing server directories are never overwritten by install.
- [ ] Build and inspect a wheel in a build environment with Hatchling installed.
- [ ] Run the TUI in a clean environment with Textual installed.

## External acceptance gates (not completed in this build environment)
- [ ] Install and upgrade on clean Debian 12 and Ubuntu 24.04 VMs.
- [ ] Run real Vanilla and Paper JAR bootstrap for legacy and current Minecraft releases.
- [ ] Verify the generated world survives bootstrap shutdown and opens on the next start.
- [ ] Exercise RCON stop and property changes against real Minecraft processes.
- [ ] Exercise systemd install/start/stop/restart/uninstall on real systemd hosts.
- [ ] Complete dependency/security audit and publish signed release provenance.

## Security and operational notes
- `online-mode=false` allows username spoofing unless an authenticated proxy/trusted authentication layer protects the backend. Never expose the backend directly to untrusted clients.
- The application does not configure firewall rules automatically.
- Back up existing worlds before upgrading the application. Application upgrades do not migrate, regenerate, or overwrite existing worlds.
- Local tests are not a substitute for the external acceptance gates above. Do not describe this release as production-certified until those gates pass.

---

## Historical implementation checks

# IlandyMC release checklist

## 0.7.0 local release gates
- [x] `ily` console entry point registered for the Textual TUI.
- [x] TUI server picker, start/stop, memory/port editing, update check/apply actions implemented.
- [x] `bootstrap/install.sh` installs the application virtual environment under `/opt/ily`.
- [x] `ilandy` CLI retained alongside `ily`.
- [x] Application auto-update is opt-in and requires an HTTPS manifest and SHA-256 wheel digest.
- [x] Wheel SHA-256 and embedded distribution name/version are checked before installation.
- [x] Server memory and port can be changed while stopped; installed systemd unit can be refreshed.
- [x] Python compilation and offline pytest suite pass.
- [x] Bootstrap shell syntax validated.
- [ ] Execute Textual UI in a clean installed environment (Textual is declared but is not installed in this build sandbox).
- [ ] Install/upgrade test on clean Debian 12 and Ubuntu 24.04 VMs.
- [ ] Exercise systemd start/stop/restart and service unit refresh on real systemd.
- [ ] Test auto-update end-to-end against a staging HTTPS manifest and built wheel.
- [ ] Add transactional A/B application update and rollback before calling updater production-grade.

## Production gates still open
- Real Minecraft/Paper and RCON integration tests.
- Firewall management and multi-instance port lifecycle.
- Transactional Minecraft server JAR updates and rollback.
- Scheduled backups and retention.
- Forge/NeoForge and mod/plugin lifecycle.
- Dependency/security audit and signed release provenance.

## 0.8.0 server.properties acceptance
- [ ] Open `ily` on a clean VM with Textual installed and scroll through the full property editor.
- [ ] Confirm each of the 71 documented options has a control and Russian description.
- [ ] Change boolean, enum, integer and text values; save, restart Minecraft, and verify server behavior.
- [ ] Confirm `online-mode=false` on a newly installed server.
- [ ] Confirm the editor refuses changes while a process-managed or systemd-managed server is active.
- [ ] Confirm secrets are not exposed in logs or sample files and RCON stop still works after password/port edits.


## 0.9.0 version-aware property detection
- [x] First install starts the downloaded server only inside the private staging directory.
- [x] Bootstrap uses loopback and port 0, disables RCON during detection, waits for ready, then requests graceful stop.
- [x] Only properties present in the generated server.properties are recorded as supported.
- [x] TUI and CLI hide unsupported catalogue entries and reject attempts to set them.
- [x] Unknown/native keys from the server-generated file are retained.
- [x] Offline tests cover generated-property detection and unsupported-key rejection.
- [ ] Run first-install bootstrap against real Vanilla and Paper JARs for both legacy and current releases.
- [ ] Verify the first-created world opens correctly after bootstrap and the selected gameplay port is applied.
- [ ] Run Textual property editor acceptance on a clean VM with Textual installed.
