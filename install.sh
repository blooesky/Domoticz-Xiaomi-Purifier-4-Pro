#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PLUGIN_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "Installing Xiaomi Purifier 4 Pro plugin in: $PLUGIN_DIR"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "ERROR: python3 was not found."
    exit 1
fi

if ! "$PYTHON_BIN" -m venv --help >/dev/null 2>&1; then
    echo "ERROR: Python venv support is missing."
    echo "Install it with: sudo apt install python3-venv"
    exit 1
fi

if [ ! -d ".venv" ]; then
    "$PYTHON_BIN" -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install --upgrade --force-reinstall -r requirements.txt

chmod +x install.sh update.sh uninstall.sh
chmod 644 plugin.py requirements.txt README.md

echo
echo "Installed versions:"
.venv/bin/python - <<'PY'
from importlib.metadata import version
print("python-miio:", version("python-miio"))
print("click:", version("click"))
import miio
print("miio path:", miio.__file__)
PY

echo
echo "Installation complete."
echo "Restart Domoticz and add hardware: Xiaomi Smart Air Purifier 4 Pro."
