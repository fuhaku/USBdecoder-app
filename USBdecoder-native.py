import sys
import json

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QLabel, QTextEdit, QFileDialog, QComboBox
)

def parse_device_descriptor(data):
    if len(data) < 18:
        raise ValueError("Data too short for a USB Device Descriptor (needs 18 bytes)")

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
    output.append(f"* {data[0]:02X} → `bLength` = {data[0]} bytes (Total length of this descriptor)")
    output.append(f"* {data[1]:02X} → `bDescriptorType` = {data[1]} ({descriptor_type_desc(data[1])} descriptor)")
    output.append(f"* {data[2]:02X} {data[3]:02X} → `bcdUSB` = USB Spec {data[3]:02X}.{data[2]:02X} (Little-Endian for 0x{data[3]:02X}{data[2]:02X})")
    output.append(f"* {data[4]:02X} → `bDeviceClass` = 0x{data[4]:02X} ({device_class_desc(data[4])})")
    output.append(f"* {data[5]:02X} → `bDeviceSubClass` = {data[5]} (Subclass value)")
    output.append(f"* {data[6]:02X} → `bDeviceProtocol` = {data[6]} (Protocol value)")
    output.append(f"* {data[7]:02X} → `bMaxPacketSize0` = {data[7]} bytes (0x{data[7]:02X})")
    output.append(f"* {data[8]:02X} {data[9]:02X} → `idVendor` = 0x{data[9]:02X}{data[8]:02X} (Little-Endian Vendor ID)")
    output.append(f"* {data[10]:02X} {data[11]:02X} → `idProduct` = 0x{data[11]:02X}{data[10]:02X} (Little-Endian Product ID)")
    output.append(f"* {data[12]:02X} {data[13]:02X} → `bcdDevice` = Version {data[13]}.{data[12]} (Little-Endian for 0x{data[13]:02X}{data[12]:02X})")
    output.append(f"* {data[14]:02X} → `iManufacturer` = {data[14]} (Index of String Descriptor for Manufacturer)")
    output.append(f"* {data[15]:02X} → `iProduct` = {data[15]} (Index of String Descriptor for Product)")
    output.append(f"* {data[16]:02X} → `iSerialNumber` = {data[16]} (Index of String Descriptor for Serial Number)")
    output.append(f"* {data[17]:02X} → `bNumConfigurations` = {data[17]} (Number of possible configurations)")

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
    output.append(f"* {data[0]:02X} → `bLength` = {length} bytes (Total length of this descriptor)")
    output.append(f"* {data[1]:02X} → `bDescriptorType` = {descriptor_type} (STRING descriptor)")
    for i in range(2, length, 2):
        if i+1 < length:
            char_bytes = f"{data[i]:02X} {data[i+1]:02X}"
            char = raw_string_bytes[i-2:i-2+2].decode('utf-16-le', errors='replace')
            output.append(f"* {char_bytes} → '{char}' (UTF-16 LE)")
    output.append(f"* Decoded String: \"{decoded_string}\"")

    return "\n".join(output)

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
        self.combo.addItem("hid_report")
        self.combo.addItem("hex_dump")
        self.combo.addItem("raw_bytes")
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
                result = parse_device_descriptor(bytes_list)
            elif conversionType == "string_descriptor":
                result = parse_string_descriptor(bytes_list)
            else:
                result = f"Parsing for '{conversionType}' is not yet implemented."

            self.resultText.setPlainText(result)
        except Exception as e:
            self.resultText.setPlainText(f"Error: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = USBDecoderApp()
    ex.show()
    sys.exit(app.exec())
