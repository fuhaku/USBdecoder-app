<p align="center">
  <img src="./usb_decoder_re.png" alt="USB Decoder Icon" width="120" height="120">
</p>

# USB Decoder

**USB Decoder** is a Python-based application for converting raw USB protocol payloads into human-readable formats.  
It is cross-platform at the source code level (Linux, Windows, macOS), but the packaged GUI (`.app`) currently targets **macOS**.

Ideal for:

- Reverse-engineering USB devices
- Embedded hardware development
- USB protocol analysis and debugging

---

## 🛠️ Features

- **Device Descriptors** decoding (18 bytes)
- **Configuration Descriptors** decoding (9+ bytes)
- **String Descriptors** decoding (UTF-16LE Unicode)
- **Interface Descriptors** decoding (9 bytes)
- **Endpoint Descriptors** decoding (7 bytes)
- **HID Descriptors** decoding (9 bytes)
- 🔎 **Smart Suggestions** (detects descriptor type automatically if you choose the wrong one)
- 🧹 **Clear Button** to reset input and output fields
- 🚫 **Friendly Error Handling** with pop-up messages
- 📜 **UTF-16 Unicode decoding** for embedded USB strings
- 🍏 Creates a standalone .app and .dmg installer for easy distribution on macOS

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

---

### Absolutely — great idea! 🔥  
Running inside a **virtual environment (venv)** is much more professional, safer, and keeps things clean — especially for Linux and Windows users.

Here’s the **updated Linux/Windows instructions** you can directly replace in your README:

---

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