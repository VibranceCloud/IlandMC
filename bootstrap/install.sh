#!/usr/bin/env bash
set -Eeuo pipefail
# Install from a local, reviewed source tree. The update channel is configured separately.
if [[ "${EUID}" -ne 0 ]]; then echo "Run as root: sudo bash bootstrap/install.sh [source-dir]" >&2; exit 1; fi
SOURCE_DIR="$(cd "${1:-$(dirname "$0")/..}" && pwd)"
[[ -f "$SOURCE_DIR/pyproject.toml" ]] || { echo "Source tree with pyproject.toml required" >&2; exit 1; }
command -v python3 >/dev/null || { echo "Python 3 required" >&2; exit 1; }
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)' || { echo "Python 3.11+ required" >&2; exit 1; }
install -d -m 0755 /opt/ily
if [[ ! -x /opt/ily/venv/bin/python ]]; then python3 -m venv /opt/ily/venv; fi
/opt/ily/venv/bin/python -m pip install --upgrade pip
/opt/ily/venv/bin/python -m pip install --upgrade "$SOURCE_DIR"
ln -sfn /opt/ily/venv/bin/ily /usr/local/bin/ily
ln -sfn /opt/ily/venv/bin/ilandy /usr/local/bin/ilandy
echo "IlandyMC installed under /opt/ily"
echo "Run: ily"
echo "To enable automatic updates, configure auto_update and update_manifest_url in your user config.yml."
