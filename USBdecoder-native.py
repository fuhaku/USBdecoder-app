import sys
import json

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QLabel, QTextEdit, QFileDialog, QComboBox
)

def parse_device_descriptor(data):
    if len(data) < 18:
        raise ValueError("Data too short for a USB Device Descriptor (needs 18 bytes)")

    descriptor = {
        "bLength": data[0],
        "bDescriptorType": data[1],
        "bcdUSB": f"0x{data[3]:02x}{data[2]:02x}",  # Little Endian
        "bDeviceClass": data[4],
        "bDeviceSubClass": data[5],
        "bDeviceProtocol": data[6],
        "bMaxPacketSize0": data[7],
        "idVendor": f"0x{data[9]:02x}{data[8]:02x}",
        "idProduct": f"0x{data[11]:02x}{data[10]:02x}",
        "bcdDevice": f"0x{data[13]:02x}{data[12]:02x}",
        "iManufacturer": data[14],
        "iProduct": data[15],
        "iSerialNumber": data[16],
        "bNumConfigurations": data[17],
    }
    return descriptor

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
            else:
                result = {"error": "Unsupported conversion type selected."}
            pretty_result = json.dumps(result, indent=4)
            self.resultText.setPlainText(pretty_result)
        except Exception as e:
            self.resultText.setPlainText(f"Error: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = USBDecoderApp()
    ex.show()
    sys.exit(app.exec())
