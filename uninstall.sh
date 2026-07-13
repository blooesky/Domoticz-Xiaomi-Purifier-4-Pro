#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Removing isolated virtual environment only:"
echo "$PLUGIN_DIR/.venv"
rm -rf "$PLUGIN_DIR/.venv"

echo "The plugin source files and Domoticz devices were not removed."
echo "Remove the hardware entry from Domoticz manually if no longer required."
