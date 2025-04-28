#!/usr/bin/env bash
set -e

# 1) Activate the packaging venv
# shellcheck disable=SC1091
source pkg-venv/bin/activate

# 2) Clean
echo "🧹 Cleaning old build artifacts..."
rm -rf build dist dmg-folder "USB Decoder.app" __pycache__ *.dmg

# 3) Locate Qt 'platforms' plugins
echo "🔍 Locating Qt platform plugins..."
PLUGINS_DIR=$(python - << 'EOF'
import site, os
sp = site.getsitepackages()[0]
print(os.path.join(sp, 'PyQt6', 'Qt6', 'plugins', 'platforms'))
EOF
)

# 4) Build with PyInstaller
echo "⚙️ Building USB Decoder GUI with PyInstaller..."
pyinstaller \
  --noconfirm \
  --windowed \
  --name "USB Decoder" \
  --icon usb_decoder_re.icns \
  --collect-submodules PyQt6 \
  --add-data "${PLUGINS_DIR}:PyQt6/Qt6/plugins/platforms" \
  USBdecoder-native.py

# 5) Sign
echo "🔏 Signing the .app (ad-hoc)..."
codesign --force --deep --sign - dist/"USB Decoder.app"

# 6) Create DMG
echo "📦 Packaging into USB Decoder.dmg..."
rm -rf dmg-folder
mkdir dmg-folder
cp -R dist/"USB Decoder.app" dmg-folder/
create-dmg \
  --volname "USB Decoder" \
  --window-size 500 300 \
  --app-drop-link 400 150 \
  "USB Decoder.dmg" \
  dmg-folder

echo "✅ Build complete! Launch with:\n  open \"dist/USB Decoder.app\""
