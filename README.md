<p align="center">
  <img src="./usb_decoder_re.png" alt="USB Decoder Icon" width="120" height="120">
</p>

# USB Decoder

**USB Decoder** is a cross-platform GUI application for converting USB protocol payloads into human-readable formats.  
Ideal for reverse-engineering USB devices, embedded hardware development, and protocol analysis.

Supports decoding:

- **Device Descriptors** (18 bytes)
- **Configuration Descriptors** (9+ bytes)
- **String Descriptors** (UTF-16LE Unicode)
- **Interface Descriptors** (9 bytes)
- **Endpoint Descriptors** (7 bytes)
- **HID Descriptors** (9 bytes)

Also features:

- 🔎 **Smart Suggestions** (auto-detects descriptor types when possible)
- 🧹 **Clear Button** to reset input/output
- 🚫 **Error Handling** with friendly pop-up messages
- 📜 **UTF-16 Unicode decoding** for USB string fields

---

## 🚀 Quickstart (From Source)

```bash
# 1) Clone the repository and enter
git clone https://github.com/fuhaku/USBdecoder-app.git
cd USBdecoder-app

# 2) Make helper scripts executable - may require sudo
chmod +x setup.sh 
chmod +x build-gui-app.sh

# 3) Bootstrap, build, and package in one go. May also require sudo if already run once.
./setup.sh

# 4) Launch the packaged app
enjoy open "dist/USB Decoder.app"
