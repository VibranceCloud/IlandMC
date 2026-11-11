# Security model

- Never run Minecraft as root. Run the application and server lifecycle as a dedicated service account.
- Use explicit privileged provisioning outside the current automatic workflow.
- Commands are passed as argument arrays; no shell interpolation is used for server process start.
- Server identifiers reject separators and traversal components.
- Configuration uses safe YAML parsing, atomic replacement and owner-only file mode.
- Downloads are staged in the destination directory, hashed while streaming, and atomically renamed. SHA-256 is enforced when the provider publishes a SHA-256 value.
- Backup restore requires a checksum sidecar, rejects traversal paths, and refuses overwrite.
- The bootstrap requires HTTPS and an externally supplied pinned checksum. It does not install an unverified release.
- Never expose RCON credentials in logs; RCON is not implemented in this release.

Before production use, audit PID ownership, service account isolation, provider checksums/signatures, archive extraction on all supported Python versions, and privilege boundaries.
