import sys
import re
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTextEdit, QFileDialog, QComboBox, QMessageBox
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

class USBDecoderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('USB Payload Decoder')
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon('usb_re_icon.icns'))  # Set a window icon
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.mode_select = QComboBox()
        self.mode_select.addItems([
            'device_descriptor',
            'configuration_descriptor',
            'string_descriptor',
            'interface_descriptor',
            'endpoint_descriptor',
            'hid_report',
            'hex_dump',
            'raw'
        ])

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText('Paste hex dump here or load a binary file...')

        self.convert_button = QPushButton('Convert')
        self.upload_button = QPushButton('Upload File')
        self.quit_button = QPushButton('Quit')

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.upload_button)
        button_layout.addWidget(self.convert_button)
        button_layout.addWidget(self.quit_button)

        self.output_text = QTextEdit()
        self.output_text.setPlaceholderText('Converted output will appear here...')
        self.output_text.setReadOnly(True)

        layout.addWidget(QLabel('Select Conversion Type:'))
        layout.addWidget(self.mode_select)
        layout.addWidget(QLabel('Input Hex or File Content:'))
        layout.addWidget(self.input_text)
        layout.addLayout(button_layout)
        layout.addWidget(QLabel('Result:'))
        layout.addWidget(self.output_text)

        self.setLayout(layout)

        self.upload_button.clicked.connect(self.load_file)
        self.convert_button.clicked.connect(self.convert_data)
        self.quit_button.clicked.connect(self.close)

    def load_file(self):
        file_dialog = QFileDialog()
        path, _ = file_dialog.getOpenFileName(self, 'Open Binary File', '', 'All Files (*)')
        if not path:
            return

        try:
            # Read raw file bytes
            with open(path, 'rb') as f:
                content = f.read()

            # Detect whether this is an ASCII-hex text file
            try:
                text = content.decode('ascii')
                is_hex_text = all(c in '0123456789abcdefABCDEF \t\r\n'
                                  for c in text)
            except UnicodeDecodeError:
                is_hex_text = False

            if is_hex_text:
                # Parse ASCII hex pairs into bytes
                tokens = re.findall(r'[0-9A-Fa-f]{2}', text)
                raw_bytes = bytes(int(tok, 16) for tok in tokens)
            else:
                # Treat as pure binary
                raw_bytes = content

            # Render canonical hex
            hex_str = ' '.join(f'{b:02X}' for b in raw_bytes)
            self.input_text.setPlainText(hex_str)

        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))


    def convert_data(self):
        mode = self.mode_select.currentText()
        hex_data = self.input_text.toPlainText()
        try:
            tokens = re.findall(r'[0-9A-Fa-f]{2}', hex_data)
            if not tokens:
                raise ValueError('No valid hex bytes found')
            raw = bytes(int(t, 16) for t in tokens)
        # ─── SUGGEST CORRECT DESCRIPTOR MODE ───
        descriptor_modes = {
            1: 'device_descriptor',
            2: 'configuration_descriptor',
            3: 'string_descriptor',
            4: 'interface_descriptor',
            5: 'endpoint_descriptor',
        }
        if len(raw) > 1 and mode in descriptor_modes.values():
            dt = raw[1]
            correct = descriptor_modes.get(dt)
            if correct and correct != mode:
                QMessageBox.information(
                    self,
                    'Did you mean…?',
                    f"This byte stream has bDescriptorType={dt}.\n"
                    f"You selected '{mode}', but you probably want '{correct}'."
                )

            if mode == 'device_descriptor':
                parsed = parse_device_descriptor(raw)
            elif mode == 'configuration_descriptor':
                parsed = parse_configuration_descriptor(raw)
            elif mode == 'string_descriptor':
                parsed = parse_string_descriptor(raw)
            elif mode == 'interface_descriptor':
                parsed = parse_interface_descriptor(raw)
            elif mode == 'endpoint_descriptor':
                parsed = parse_endpoint_descriptor(raw)
            elif mode == 'hid_report':
                parsed = {'report_bytes': list(raw)}
            elif mode == 'hex_dump':
                parsed = ' '.join(f"{b:02X}" for b in raw)
            elif mode == 'raw':
                parsed = {'raw_bytes': list(raw)}
            else:
                raise ValueError('Unsupported conversion type')

            if isinstance(parsed, dict):
                # nice “key: value” per line
                lines = [f"{k}: {v}" for k, v in parsed.items()]
                self.output_text.setPlainText("\n".join(lines))
            elif isinstance(parsed, list):
                # comma-separated list
                self.output_text.setPlainText(", ".join(str(x) for x in parsed))
            else:
                # string (hex dump, errors, etc.)
                self.output_text.setPlainText(str(parsed))


        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

# ========== USB Descriptor Parsers ==========

def parse_device_descriptor(data: bytes):
    if len(data) < 18:
        raise ValueError('Device Descriptor requires at least 18 bytes')
    return {
        'bLength': data[0],
        'bDescriptorType': data[1],
        'bcdUSB': hex(data[2] | (data[3] << 8)),
        'bDeviceClass': data[4],
        'bDeviceSubClass': data[5],
        'bDeviceProtocol': data[6],
        'bMaxPacketSize0': data[7],
        'idVendor': hex(data[8] | (data[9] << 8)),
        'idProduct': hex(data[10] | (data[11] << 8)),
        'bcdDevice': hex(data[12] | (data[13] << 8)),
        'iManufacturer': data[14],
        'iProduct': data[15],
        'iSerialNumber': data[16],
        'bNumConfigurations': data[17]
    }

def parse_configuration_descriptor(data: bytes):
    if len(data) < 9:
        raise ValueError('Configuration Descriptor requires at least 9 bytes')
    return {
        'bLength': data[0],
        'bDescriptorType': data[1],
        'wTotalLength': data[2] | (data[3] << 8),
        'bNumInterfaces': data[4],
        'bConfigurationValue': data[5],
        'iConfiguration': data[6],
        'bmAttributes': hex(data[7]),
        'bMaxPower': data[8]
    }

def parse_string_descriptor(data: bytes):
    if len(data) < 2:
        raise ValueError('String Descriptor requires at least 2 bytes')
    length = data[0]
    dtype = data[1]
    raw_chars = data[2:length]
    try:
        s = raw_chars.decode('utf-16-le')
    except Exception:
        s = ''.join(f"\\x{b:02X}" for b in raw_chars)
    return {
        'bLength': length,
        'bDescriptorType': dtype,
        'string': s
    }

def parse_interface_descriptor(data: bytes):
    if len(data) < 9:
        raise ValueError('Interface Descriptor requires at least 9 bytes')
    return {
        'bLength': data[0],
        'bDescriptorType': data[1],
        'bInterfaceNumber': data[2],
        'bAlternateSetting': data[3],
        'bNumEndpoints': data[4],
        'bInterfaceClass': data[5],
        'bInterfaceSubClass': data[6],
        'bInterfaceProtocol': data[7],
        'iInterface': data[8]
    }

def parse_endpoint_descriptor(data: bytes):
    if len(data) < 7:
        raise ValueError('Endpoint Descriptor requires at least 7 bytes')
    wMax = data[4] | (data[5] << 8)
    return {
        'bLength': data[0],
        'bDescriptorType': data[1],
        'bEndpointAddress': data[2],
        'bmAttributes': data[3],
        'wMaxPacketSize': wMax,
        'bInterval': data[6]
    }

# ========== Run App ==========

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = USBDecoderApp()
    window.show()
    sys.exit(app.exec())
