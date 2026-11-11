# IlandyMC 1.0.0

IlandyMC 1.0.0 establishes the first stable feature baseline for the manager.

## Compatibility contract

1. A new server is downloaded into a private staging directory.
2. The selected server JAR is launched in staging so that the server itself creates the initial world and its native `server.properties`.
3. IlandyMC stops that bootstrap process before committing the installation.
4. The settings editor exposes only catalogue keys present in the generated file.
5. Unsupported keys are hidden and rejected; unknown server-native keys are retained.
6. Managed defaults such as `online-mode=false` are applied only if the selected server generated that key.

Existing server directories are not overwritten or automatically regenerated. Updating IlandyMC does not change existing worlds or their `server.properties` files.

## Before production use

Run the external acceptance checklist in `RELEASE_CHECKLIST.md` on clean Debian/Ubuntu hosts and against real Vanilla/Paper server JARs. The local test suite uses offline fixtures and fake Java launchers; it does not certify live server compatibility.

**Security:** with `online-mode=false`, use a correctly configured authenticated proxy or another trusted authentication layer, and block direct untrusted access to the backend.
