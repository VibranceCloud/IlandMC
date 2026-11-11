import re
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class JavaRuntime:
    executable: str
    major: int
    version_text: str


def inspect_java(executable="java"):
    path = shutil.which(executable) if "/" not in executable else executable
    if not path:
        return None
    try:
        result = subprocess.run(
            [path, "-version"], capture_output=True, text=True, timeout=10, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = result.stderr or result.stdout
    match = re.search(r'version "([^\"]+)"', text)
    if result.returncode or not match:
        return None
    raw = match.group(1)
    parts = raw.split(".")
    try:
        major = int(parts[1] if parts[0] == "1" and len(parts) > 1 else parts[0].split("-")[0].split("+")[0])
    except ValueError:
        return None
    return JavaRuntime(path, major, text.strip())


def required_java_major(mc_version: str):
    """Return the minimum Java major for supported Minecraft release IDs.

    Minecraft's 2026 YY.drop numbering starts at 26.1 and requires Java 25.
    Prerelease suffixes are accepted because Mojang's manifest includes them.
    """
    if not isinstance(mc_version, str):
        raise ValueError("Minecraft version must be a string")
    match = re.fullmatch(r"(\d+)\.(\d+)(?:\.(\d+))?(?:[-+][A-Za-z0-9.-]+)?", mc_version)
    if not match:
        raise ValueError(f"Unsupported Minecraft version format: {mc_version!r}")
    major, minor, patch = (int(value or 0) for value in match.groups())
    if major == 1:
        if minor >= 20 and (minor > 20 or patch >= 5):
            return 21
        if minor >= 18:
            return 17
        if minor == 17:
            return 16
        return 8
    if 26 <= major <= 99:
        return 25
    raise ValueError(f"Unsupported Minecraft version family: {mc_version!r}")
