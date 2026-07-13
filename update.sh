#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PLUGIN_DIR"

if [ ! -x ".venv/bin/python" ]; then
    echo "Virtual environment missing; running installer."
    exec ./install.sh
fi

.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install --upgrade --force-reinstall -r requirements.txt

echo "Python dependencies updated."
echo "Restart Domoticz to reload the plugin."
