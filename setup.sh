#!/usr/bin/env bash
set -e

# 1) Pick a Python for packaging: prefer 3.12 if installed
if command -v python3.12 &>/dev/null; then
  PY=python3.12
else
  PY=python3
fi

# 2) Create or reuse packaging venv
if [ ! -d pkg-venv ]; then
  echo "🔧 Creating packaging venv with $PY..."
  $PY -m venv pkg-venv
fi
echo "🔌 Activating pkg-venv..."
# shellcheck disable=SC1091
source pkg-venv/bin/activate

# 3) Upgrade pip & install PyQt6 + PyInstaller
echo "📥 Installing PyQt6 and PyInstaller..."
pip install --upgrade pip
pip install PyQt6 pyinstaller==6.13.0

# 4) Ensure create-dmg is present
if ! command -v create-dmg &>/dev/null; then
  echo "⚠️ create-dmg not found. Installing via Homebrew..."
  if command -v brew &>/dev/null; then
    brew install create-dmg
  else
    echo "‼️ Please install Homebrew or create-dmg manually."
    exit 1
  fi
fi

# 5) Delegate to build script
echo "▶️ Running build-gui-app.sh..."
./build-gui-app.sh
