import sys
import json

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QLabel, QTextEdit, QFileDialog, QComboBox, QMessageBox
)

def parse_device_descriptor(data):
    if len(data) < 18:
        raise ValueError("Device Descriptor requires at least 18 bytes")

    def descriptor_type_desc(val):
        return {
            1: "DEVICE",
            2: "CONFIGURATION",
            3: "STRING",
            4: "INTERFACE",
            5: "ENDPOINT",
            0x21: "HID",
        }.get(val, "Unknown")

    def device_class_desc(val):
        return {
            0x00: "Defined at Interface level",
            0x02: "Communications and CDC Control",
            0x03: "Human Interface Device (HID)",
            0x08: "Mass Storage",
            0x09: "Hub",
        }.get(val, "Vendor-specific or Reserved")

    output = []
    output.append(f"* {data[0]:02X} → `bLength` = {data[0]} bytes")
    output.append(f"* {data[1]:02X} → `bDescriptorType` = {data[1]} ({descriptor_type_desc(data[1])} descriptor)")
    output.append(f"* {data[2]:02X} {data[3]:02X} → `bcdUSB` = USB Spec {data[3]:02X}.{data[2]:02X} (Little-Endian)")
    output.append(f"* {data[4]:02X} → `bDeviceClass` = 0x{data[4]:02X} ({device_class_desc(data[4])})")
    output.append(f"* {data[5]:02X} → `bDeviceSubClass` = {data[5]}")
    output.append(f"* {data[6]:02X} → `bDeviceProtocol` = {data[6]}")
    output.append(f"* {data[7]:02X} → `bMaxPacketSize0` = {data[7]} bytes")
    output.append(f"* {data[8]:02X} {data[9]:02X} → `idVendor` = 0x{data[9]:02X}{data[8]:02X}")
    output.append(f"* {data[10]:02X} {data[11]:02X} → `idProduct` = 0x{data[11]:02X}{data[10]:02X}")
    output.append(f"* {data[12]:02X} {data[13]:02X} → `bcdDevice` = Version {data[13]}.{data[12]}")
    output.append(f"* {data[14]:02X} → `iManufacturer` = {data[14]}")
    output.append(f"* {data[15]:02X} → `iProduct` = {data[15]}")
    output.append(f"* {data[16]:02X} → `iSerialNumber` = {data[16]}")
    output.append(f"* {data[17]:02X} → `bNumConfigurations` = {data[17]}")

    return "\n".join(output)

def parse_configuration_descriptor(data):
    if len(data) < 9:
        raise ValueError("Configuration Descriptor requires at least 9 bytes")

    output = []
    output.append(f"* {data[0]:02X} → `bLength` = {data[0]} bytes")
    output.append(f"* {data[1]:02X} → `bDescriptorType` = {data[1]} (CONFIGURATION descriptor)")
    total_length = data[2] | (data[3] << 8)
    output.append(f"* {data[2]:02X} {data[3]:02X} → `wTotalLength` = {total_length} bytes")
    output.append(f"* {data[4]:02X} → `bNumInterfaces` = {data[4]}")
    output.append(f"* {data[5]:02X} → `bConfigurationValue` = {data[5]}")
    output.append(f"* {data[6]:02X} → `iConfiguration` = {data[6]}")
    output.append(f"* {data[7]:02X} → `bmAttributes` = 0x{data[7]:02X}")
    output.append(f"* {data[8]:02X} → `bMaxPower` = {data[8]*2} mA")

    return "\n".join(output)

def parse_string_descriptor(data):
    if len(data) < 2:
        raise ValueError("String Descriptor requires at least 2 bytes")

    length = data[0]
    descriptor_type = data[1]
    if descriptor_type != 3:
        raise ValueError("Not a String Descriptor (bDescriptorType != 3)")

    raw_string_bytes = data[2:length]
    try:
        decoded_string = raw_string_bytes.decode('utf-16-le')
    except Exception as e:
        decoded_string = f"<decode error: {e}>"

    output = []
    output.append(f"* {data[0]:02X} → `bLength` = {length} bytes")
    output.append(f"* {data[1]:02X} → `bDescriptorType` = {descriptor_type} (STRING descriptor)")
    output.append(f"* Decoded String: \"{decoded_string}\"")

    return "\n".join(output)

def parse_interface_descriptor(data):
    if len(data) < 9:
        raise ValueError("Interface Descriptor requires at least 9 bytes")

    output = []
    output.append(f"* {data[0]:02X} → `bLength` = {data[0]} bytes")
    output.append(f"* {data[1]:02X} → `bDescriptorType` = {data[1]} (INTERFACE descriptor)")
    output.append(f"* {data[2]:02X} → `bInterfaceNumber` = {data[2]}")
    output.append(f"* {data[3]:02X} → `bAlternateSetting` = {data[3]}")
    output.append(f"* {data[4]:02X} → `bNumEndpoints` = {data[4]}")
    output.append(f"* {data[5]:02X} → `bInterfaceClass` = {data[5]}")
    output.append(f"* {data[6]:02X} → `bInterfaceSubClass` = {data[6]}")
    output.append(f"* {data[7]:02X} → `bInterfaceProtocol` = {data[7]}")
    output.append(f"* {data[8]:02X} → `iInterface` = {data[8]}")

    return "\n".join(output)

def parse_endpoint_descriptor(data):
    if len(data) < 7:
        raise ValueError("Endpoint Descriptor requires at least 7 bytes")

    output = []
    output.append(f"* {data[0]:02X} → `bLength` = {data[0]} bytes")
    output.append(f"* {data[1]:02X} → `bDescriptorType` = {data[1]} (ENDPOINT descriptor)")
    output.append(f"* {data[2]:02X} → `bEndpointAddress` = 0x{data[2]:02X}")
    output.append(f"* {data[3]:02X} → `bmAttributes` = 0x{data[3]:02X}")
    wMaxPacketSize = data[4] | (data[5] << 8)
    output.append(f"* {data[4]:02X} {data[5]:02X} → `wMaxPacketSize` = {wMaxPacketSize} bytes")
    output.append(f"* {data[6]:02X} → `bInterval` = {data[6]} ms")

    return "\n".join(output)

def attempt_decode_utf16(data):
    try:
        raw_string = data[2:data[0]]
        decoded = raw_string.decode('utf-16-le')
        return f"UTF-16 LE: \"{decoded}\""
    except Exception as e:
        return f"<decode error: {e}>"

class USBDecoderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('USB Payload Decoder')

        layout = QVBoxLayout()

        self.label = QLabel('Select Conversion Type:')
        layout.addWidget(self.label)

        self.combo = QComboBox()
        self.combo.addItem("device_descriptor")
        self.combo.addItem("configuration_descriptor")
        self.combo.addItem("string_descriptor")
        self.combo.addItem("interface_descriptor")
        self.combo.addItem("endpoint_descriptor")
        layout.addWidget(self.combo)

        self.textEdit = QTextEdit()
        layout.addWidget(self.textEdit)

        self.uploadButton = QPushButton('Upload File')
        self.uploadButton.clicked.connect(self.uploadFile)
        layout.addWidget(self.uploadButton)

        self.convertButton = QPushButton('Convert')
        self.convertButton.clicked.connect(self.convertData)
        layout.addWidget(self.convertButton)

        self.quitButton = QPushButton('Quit')
        self.quitButton.clicked.connect(self.close)
        layout.addWidget(self.quitButton)

        self.resultText = QTextEdit()
        self.resultText.setReadOnly(True)
        layout.addWidget(self.resultText)

        self.setLayout(layout)

    def uploadFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*)")
        if fileName:
            with open(fileName, 'r') as file:
                content = file.read()
                self.textEdit.setPlainText(content)

    def convertData(self):
        conversionType = self.combo.currentText()
        hexData = self.textEdit.toPlainText()
        try:
            bytes_list = bytes.fromhex(hexData.replace("\n", " ").replace("\r", " ").replace("\t", " ").replace(",", " "))

            if conversionType == "device_descriptor":
                parsed = parse_device_descriptor(bytes_list)
            elif conversionType == "configuration_descriptor":
                parsed = parse_configuration_descriptor(bytes_list)
            elif conversionType == "string_descriptor":
                parsed = parse_string_descriptor(bytes_list)
                parsed += "\n\n---\nPossible Decoded String(s):\n" + attempt_decode_utf16(bytes_list)
            elif conversionType == "interface_descriptor":
                parsed = parse_interface_descriptor(bytes_list)
            elif conversionType == "endpoint_descriptor":
                parsed = parse_endpoint_descriptor(bytes_list)
            else:
                parsed = f"Parsing for '{conversionType}' is not yet implemented."

            self.resultText.setPlainText(parsed)
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = USBDecoderApp()
    ex.show()
    sys.exit(app.exec())
