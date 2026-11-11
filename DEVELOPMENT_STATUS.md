# Development status — IlandyMC 1.0.0

1.0.0 is a stabilization release: no new server configuration schema was introduced. The 0.9.0 version-aware property detection and safe filtering behavior are retained.

Implemented: 26.x / Java 25 compatibility, verified provider downloads, transactional initial install,
PID identity validation, RCON stop, backup integrity and restore path validation, hardened systemd
lifecycle, `/opt/ily` application installer, opt-in verified application updates, and version-aware
`server.properties` editing.

On first install, the downloaded server build is started once inside its private staging directory.
It creates the world and its own native `server.properties`; IlandyMC waits for the ready marker,
sends `stop`, and only then detects supported keys. The UI and CLI expose only catalogue keys found
in that generated file. Missing options are hidden and rejected, and the installer does not inject
speculative keys. Unknown/native server properties are retained. `online-mode=false` and loopback
RCON are applied only if the installed build generated those keys. Since offline mode permits username spoofing,
the backend must be protected by an authenticated proxy or another trusted authentication layer.

Validation is local/offline only. Unit tests use a fake Java launcher for the bootstrap flow; no live
Minecraft JAR was run in this environment. No user server credentials or server access were
requested or used. The Textual runtime, real Paper/Vanilla compatibility, RCON interoperability,
systemd integration, and installation on a clean Debian/Ubuntu VM still require acceptance testing.
Do not claim production certification.

Remaining release gates include real Paper/Vanilla + RCON interoperability; clean VM installation;
Forge/NeoForge; complete mod/plugin dependency management; transactional server updates/rollback;
scheduled backup retention; distro matrix; security/dependency audit; signed reproducible artifacts.
