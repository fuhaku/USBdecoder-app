<p align="center">
  <img src="./usb_decoder_re.png" alt="USB Decoder Icon" width="120" height="120">
</p>

# USB Decoder

**USB Decoder** is a Python-based application for converting raw USB protocol payloads into human-readable formats.  
It is cross-platform at the source code level (Linux, Windows,...cOS), but the packaged GUI (`.app`) currently targets **macOS**.

Ideal for:

- Reverse-engineering USB devices
- Embedded hardware development
- USB protocol analysis and debugging

---

## 🛠️ Features

- **Auto‑detect Descriptor Type**: Automatically recognizes and decodes your USB descriptor
- **Supported Descriptors**:
  - Device Descriptor (18 bytes)
  - Configuration Descriptor (9+ bytes)
  - String Descriptor (UTF‑16LE Unicode)
  - Interface Descriptor (9 bytes)
  - Endpoint Descriptor (7 bytes)
  - HID Descriptor (9 bytes)
  - BOS Descriptor
  - Interface Association (IAD) Descriptor
  - DFU Functional Descriptor
- 🔎 **Smart Suggestions**: If you pick the wrong descriptor type, the app suggests the correct one
- 📁 **Load from File**: Open binary files or `.txt` files containing ASCII hex — both are parsed correctly
- 🧹 **Clear All**: Reset both input and output fields with one click
- 📋 **Copy to Clipboard**: Copy decoded output instantly to your clipboard
- 🌗 **Dark Theme** toggle: Switch between light/dark modes, with your choice remembered
- 🔧 **Persisted Settings**: Window size and theme preferences are saved across sessions
- 🔀 **Split View**: Adjustable side‑by‑side input and output panels
- 📝 **Contextual Notes**: Endpoint transfer‑type hints and extra interface/class information
- 🚫 **Friendly Error Handling**: Clear pop‑ups guide you through errors
- 🍏 **macOS Packaging**: Standalone `.app` bundle and `.dmg` installer via `setup.sh`

---

## 🚀 Quickstart (from Source)

### macOS (App Bundle with Setup Script)

```bash
# 1) Clone the repository and enter it
git clone https://github.com/fuhaku/USBdecoder-app.git
cd USBdecoder-app

# 2) Make helper scripts executable (may require sudo)
chmod +x setup.sh
chmod +x build-gui-app.sh

# 3) Bootstrap, build, and package in one go (may require sudo if re-running)
./setup.sh

# 4) Launch the packaged app
open "dist/USB Decoder.app"
```

### Linux / Windows (Run Inside a Virtual Environment)

```bash
# 1) Clone the repository and enter it
git clone https://github.com/fuhaku/USBdecoder-app.git
cd USBdecoder-app

# 2) Create and activate a virtual environment
# Linux/macOS:
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell):
python -m venv venv
./venv/Scripts/Activate.ps1

# 3) Install required dependencies
pip install PyQt6

# 4) Run the application
python USBdecoder-native.py
```

> ✅ Note: Always activate the virtual environment (`source venv/bin/activate` or `Activate.ps1`) before running the app.

---

## 📂 Repository Layout

```text
USBdecoder-native.py      # Main PyQt6 GUI application (full source code)
setup.sh                  # Bootstrap and packaging script for macOS
build-gui-app.sh           # Helper script called by setup.sh
usb_decoder_re.png         # App logo/icon
requirements.txt           # Python dependencies (PyQt6, PyInstaller)
README.md                  # You're reading it
```

---

## 📦 Requirements

- **Python 3.10+** (Tested with Python 3.11 and 3.12)
- **PyQt6** (`pip install PyQt6`)
- Optional: **PyInstaller** (for packaging into an app on macOS)

The `setup.sh` script handles virtual environment setup and dependency installation automatically if you're using it.

---

## 📜 License

This project is released under the **MIT License**.  
See [LICENSE](LICENSE) for full details.

---

# 🚀 Happy decoding and USB exploration!

