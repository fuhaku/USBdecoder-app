import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QLabel, QTextEdit, QFileDialog, QComboBox, QMessageBox
)

def parse_device_descriptor(data):
    if len(data) < 18:
        raise ValueError("Device Descriptor requires at least 18 bytes")
    output = []
    output.append(f"* {data[0]:02X} → `bLength` = {data[0]} bytes")
    output.append(f"* {data[1]:02X} → `bDescriptorType` = {data[1]} (DEVICE descriptor)")
    output.append(f"* {data[2]:02X} {data[3]:02X} → `bcdUSB` = USB {data[3]:02X}.{data[2]:02X}")
    output.append(f"* {data[4]:02X} → `bDeviceClass` = {data[4]}")
    output.append(f"* {data[5]:02X} → `bDeviceSubClass` = {data[5]}")
    output.append(f"* {data[6]:02X} → `bDeviceProtocol` = {data[6]}")
    output.append(f"* {data[7]:02X} → `bMaxPacketSize0` = {data[7]} bytes")
    output.append(f"* {data[8]:02X} {data[9]:02X} → `idVendor` = 0x{data[9]:02X}{data[8]:02X}")
    output.append(f"* {data[10]:02X} {data[11]:02X} → `idProduct` = 0x{data[11]:02X}{data[10]:02X}")
    output.append(f"* {data[12]:02X} {data[13]:02X} → `bcdDevice` = {data[13]}.{data[12]}")
    output.append(f"* {data[14]:02X} → `iManufacturer` = {data[14]}")
    output.append(f"* {data[15]:02X} → `iProduct` = {data[15]}")
    output.append(f"* {data[16]:02X} → `iSerialNumber` = {data[16]}")
    output.append(f"* {data[17]:02X} → `bNumConfigurations` = {data[17]}")
    return "\n".join(output)

def parse_configuration_descriptor(data):
    if len(data) < 9:
        raise ValueError("Configuration Descriptor requires at least 9 bytes")
    output = []
    total_length = data[2] | (data[3] << 8)
    output.append(f"* {data[0]:02X} → `bLength` = {data[0]} bytes")
    output.append(f"* {data[1]:02X} → `bDescriptorType` = {data[1]} (CONFIGURATION descriptor)")
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
    try:
        decoded = data[2:data[0]].decode('utf-16-le')
    except Exception:
        decoded = "<decode error>"
    output = []
    output.append(f"* {data[0]:02X} → `bLength` = {data[0]} bytes")
    output.append(f"* {data[1]:02X} → `bDescriptorType` = {data[1]} (STRING descriptor)")
    output.append(f"* Decoded String → {decoded}")
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
    wMaxPacketSize = data[4] | (data[5] << 8)
    output = []
    output.append(f"* {data[0]:02X} → `bLength` = {data[0]} bytes")
    output.append(f"* {data[1]:02X} → `bDescriptorType` = {data[1]} (ENDPOINT descriptor)")
    output.append(f"* {data[2]:02X} → `bEndpointAddress` = 0x{data[2]:02X}")
    output.append(f"* {data[3]:02X} → `bmAttributes` = 0x{data[3]:02X}")
    output.append(f"* {data[4]:02X} {data[5]:02X} → `wMaxPacketSize` = {wMaxPacketSize} bytes")
    output.append(f"* {data[6]:02X} → `bInterval` = {data[6]} ms")
    return "\n".join(output)

def parse_hid_descriptor(data):
    if len(data) < 9:
        raise ValueError("HID Descriptor requires at least 9 bytes")
    wDescriptorLength = data[7] | (data[8] << 8)
    output = []
    output.append(f"* {data[0]:02X} → `bLength` = {data[0]} bytes")
    output.append(f"* {data[1]:02X} → `bDescriptorType` = {data[1]} (HID descriptor)")
    output.append(f"* {data[2]:02X} {data[3]:02X} → `bcdHID` = {data[3]:02X}.{data[2]:02X}")
    output.append(f"* {data[4]:02X} → `bCountryCode` = {data[4]}")
    output.append(f"* {data[5]:02X} → `bNumDescriptors` = {data[5]}")
    output.append(f"* {data[6]:02X} → `bDescriptorType` (Class Specific) = {data[6]}")
    output.append(f"* {data[7]:02X} {data[8]:02X} → `wDescriptorLength` = {wDescriptorLength} bytes")
    return "\n".join(output)

def suggest_descriptor_type(bDescriptorType):
    mapping = {
        0x01: "device_descriptor",
        0x02: "configuration_descriptor",
        0x03: "string_descriptor",
        0x04: "interface_descriptor",
        0x05: "endpoint_descriptor",
        0x21: "hid_descriptor",
    }
    return mapping.get(bDescriptorType, None)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout()

    label = QLabel("Select Descriptor Type:")
    layout.addWidget(label)

    combo = QComboBox()
    combo.addItems(["device_descriptor", "configuration_descriptor", "string_descriptor", "interface_descriptor", "endpoint_descriptor", "hid_descriptor"])
    layout.addWidget(combo)

    textEdit = QTextEdit()
    layout.addWidget(textEdit)

    uploadButton = QPushButton("Upload")
    layout.addWidget(uploadButton)

    convertButton = QPushButton("Convert")
    layout.addWidget(convertButton)

    clearButton = QPushButton("Clear")
    layout.addWidget(clearButton)

    quitButton = QPushButton("Quit")
    layout.addWidget(quitButton)

    resultText = QTextEdit()
    resultText.setReadOnly(True)
    layout.addWidget(resultText)

    def upload_file():
        fileName, _ = QFileDialog.getOpenFileName(window, "Open File", "", "All Files (*)")
        if fileName:
            with open(fileName, 'r') as file:
                content = file.read()
                textEdit.setPlainText(content)

    def convert_data():
        mode = combo.currentText()
        hex_data = textEdit.toPlainText()
        try:
            bytes_list = bytes.fromhex(hex_data.replace("\n", " ").replace("\r", " ").replace("\t", " ").replace(",", " "))
            if len(bytes_list) > 1:
                suggested = suggest_descriptor_type(bytes_list[1])
                if suggested and suggested != mode:
                    QMessageBox.information(window, "Suggestion", f"This data looks like a '{suggested}'. You selected '{mode}'.")

            if mode == "device_descriptor":
                parsed = parse_device_descriptor(bytes_list)
            elif mode == "configuration_descriptor":
                parsed = parse_configuration_descriptor(bytes_list)
            elif mode == "string_descriptor":
                parsed = parse_string_descriptor(bytes_list)
            elif mode == "interface_descriptor":
                parsed = parse_interface_descriptor(bytes_list)
            elif mode == "endpoint_descriptor":
                parsed = parse_endpoint_descriptor(bytes_list)
            elif mode == "hid_descriptor":
                parsed = parse_hid_descriptor(bytes_list)
            else:
                parsed = "Unsupported mode selected."
            resultText.setPlainText(parsed)
        except Exception as e:
            QMessageBox.critical(window, "Error", str(e))

    def clear_fields():
        textEdit.clear()
        resultText.clear()

    uploadButton.clicked.connect(upload_file)
    convertButton.clicked.connect(convert_data)
    clearButton.clicked.connect(clear_fields)
    quitButton.clicked.connect(window.close)

    window.setLayout(layout)
    window.setWindowTitle("USB Descriptor Parser")
    window.show()
    sys.exit(app.exec())
