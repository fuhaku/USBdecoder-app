import sys
import json
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QFileDialog, QComboBox, QMessageBox,
    QSplitter, QMainWindow, QToolBar, QStatusBar, QCheckBox
)
from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QPalette, QColor, QAction, QIcon, QFont

# USB descriptor type constants
DEVICE_DESCRIPTOR = 0x01
CONFIG_DESCRIPTOR = 0x02
STRING_DESCRIPTOR = 0x03
INTERFACE_DESCRIPTOR = 0x04
ENDPOINT_DESCRIPTOR = 0x05
HID_DESCRIPTOR = 0x21
BOS_DESCRIPTOR = 0x0F
IAD_DESCRIPTOR = 0x0B
DFU_DESCRIPTOR = 0x21

def parse_device_descriptor(data):
    if len(data) < 18:
        raise ValueError("Device Descriptor requires at least 18 bytes")
    output = []
    output.append(f"* {data[0]:02X} → `bLength` = {data[0]} bytes")
    output.append(f"* {data[1]:02X} → `bDescriptorType` = {data[1]} (DEVICE descriptor)")
    output.append(f"* {data[2]:02X} {data[3]:02X} → `bcdUSB` = USB {data[3]:02X}.{data[2]:02X}")
    
    class_name = get_device_class_name(data[4])
    output.append(f"* {data[4]:02X} → `bDeviceClass` = {data[4]} ({class_name})")
    output.append(f"* {data[5]:02X} → `bDeviceSubClass` = {data[5]}")
    output.append(f"* {data[6]:02X} → `bDeviceProtocol` = {data[6]}")
    output.append(f"* {data[7]:02X} → `bMaxPacketSize0` = {data[7]} bytes")
    
    # Look up vendor name from the USB ID database if available
    vendor_id = (data[9] << 8) | data[8]
    vendor_name = get_vendor_name(vendor_id)
    if vendor_name:
        output.append(f"* {data[8]:02X} {data[9]:02X} → `idVendor` = 0x{data[9]:02X}{data[8]:02X} ({vendor_name})")
    else:
        output.append(f"* {data[8]:02X} {data[9]:02X} → `idVendor` = 0x{data[9]:02X}{data[8]:02X}")
    
    # Look up product name if available
    product_id = (data[11] << 8) | data[10]
    product_name = get_product_name(vendor_id, product_id)
    if product_name:
        output.append(f"* {data[10]:02X} {data[11]:02X} → `idProduct` = 0x{data[11]:02X}{data[10]:02X} ({product_name})")
    else:
        output.append(f"* {data[10]:02X} {data[11]:02X} → `idProduct` = 0x{data[11]:02X}{data[10]:02X}")
    
    output.append(f"* {data[12]:02X} {data[13]:02X} → `bcdDevice` = {data[13]}.{data[12]}")
    output.append(f"* {data[14]:02X} → `iManufacturer` = {data[14]} (String descriptor index)")
    output.append(f"* {data[15]:02X} → `iProduct` = {data[15]} (String descriptor index)")
    output.append(f"* {data[16]:02X} → `iSerialNumber` = {data[16]} (String descriptor index)")
    output.append(f"* {data[17]:02X} → `bNumConfigurations` = {data[17]}")
    
    # Add helpful notes for Cynthion/Packetry users
    if vendor_id and product_id:
        output.append("\nNote: These VID/PID values identify the device manufacturer and product. Look for these in Packetry to track your device.")
    
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
    output.append(f"* {data[5]:02X} → `bConfigurationValue` = {data[5]} (Used in SetConfiguration request)")
    output.append(f"* {data[6]:02X} → `iConfiguration` = {data[6]} (String descriptor index)")
    
    # Decode bmAttributes
    bmAttributes = data[7]
    attr_output = []
    if bmAttributes & 0x80:
        attr_output.append("Self-powered")
    else:
        attr_output.append("Bus-powered")
    if bmAttributes & 0x40:
        attr_output.append("Remote Wakeup")
    
    output.append(f"* {data[7]:02X} → `bmAttributes` = 0x{data[7]:02X} ({', '.join(attr_output)})")
    output.append(f"* {data[8]:02X} → `bMaxPower` = {data[8]*2} mA")
    
    # Add helpful notes for Cynthion/Packetry users
    output.append("\nNote: In Packetry, the Configuration descriptor is typically sent after the Device descriptor during enumeration.")
    output.append("The total length field indicates how large the full configuration is, including all interface and endpoint descriptors that follow.")
    
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
    output.append(f"* Decoded String → \"{decoded}\"")
    
    # Add helpful notes for Cynthion/Packetry users
    output.append("\nNote: String descriptors are used to provide human-readable information. In Packetry, look for GetDescriptor(String) requests to see when the host requests these values.")
    
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
    
    # Add class information
    class_code = data[5]
    class_name = get_interface_class_name(class_code)
    output.append(f"* {data[5]:02X} → `bInterfaceClass` = {data[5]} ({class_name})")
    
    # Add subclass information
    subclass_name = get_interface_subclass_name(class_code, data[6])
    output.append(f"* {data[6]:02X} → `bInterfaceSubClass` = {data[6]} ({subclass_name})")
    
    # Add protocol information
    protocol_name = get_interface_protocol_name(class_code, data[6], data[7])
    output.append(f"* {data[7]:02X} → `bInterfaceProtocol` = {data[7]} ({protocol_name})")
    
    output.append(f"* {data[8]:02X} → `iInterface` = {data[8]} (String descriptor index)")
    
    # Add helpful notes for Cynthion/Packetry users
    output.append("\nNote: Interface descriptors define the logical groups of endpoints. In Packetry, these follow the Configuration descriptor and define the function and purpose of the device.")
    
    return "\n".join(output)

def parse_endpoint_descriptor(data):
    if len(data) < 7:
        raise ValueError("Endpoint Descriptor requires at least 7 bytes")
    wMaxPacketSize = data[4] | (data[5] << 8)
    output = []
    output.append(f"* {data[0]:02X} → `bLength` = {data[0]} bytes")
    output.append(f"* {data[1]:02X} → `bDescriptorType` = {data[1]} (ENDPOINT descriptor)")
    
    # Decode endpoint address
    endpoint_num = data[2] & 0x0F
    endpoint_dir = "IN" if data[2] & 0x80 else "OUT"
    output.append(f"* {data[2]:02X} → `bEndpointAddress` = 0x{data[2]:02X} (EP{endpoint_num} {endpoint_dir})")
    
    # Decode attributes
    transfer_type = data[3] & 0x03
    transfer_types = {0: "Control", 1: "Isochronous", 2: "Bulk", 3: "Interrupt"}
    transfer_type_name = transfer_types.get(transfer_type, "Unknown")
    
    sync_type = (data[3] & 0x0C) >> 2
    sync_types = {0: "No Sync", 1: "Asynchronous", 2: "Adaptive", 3: "Synchronous"}
    sync_type_name = sync_types.get(sync_type, "Unknown") if transfer_type == 1 else "N/A"
    
    usage_type = (data[3] & 0x30) >> 4
    usage_types = {0: "Data", 1: "Feedback", 2: "Implicit feedback", 3: "Reserved"}
    usage_type_name = usage_types.get(usage_type, "Unknown") if transfer_type == 1 else "N/A"
    
    attr_str = f"{transfer_type_name}"
    if transfer_type == 1:  # Isochronous
        attr_str += f", {sync_type_name}, {usage_type_name}"
    
    output.append(f"* {data[3]:02X} → `bmAttributes` = 0x{data[3]:02X} ({attr_str})")
    output.append(f"* {data[4]:02X} {data[5]:02X} → `wMaxPacketSize` = {wMaxPacketSize} bytes")
    
    # Decode interval
    if transfer_type == 1 or transfer_type == 3:  # Isochronous or Interrupt
        if wMaxPacketSize > 0:
            interval_desc = f"Every {data[6]} frames"
        else:
            interval_desc = "N/A (Not used)"
    else:
        interval_desc = "N/A (Not used for Control/Bulk)"
    
    output.append(f"* {data[6]:02X} → `bInterval` = {data[6]} ({interval_desc})")
    
    # Add helpful notes for Cynthion/Packetry users
    if transfer_type == 2:  # Bulk
        output.append("\nNote: Bulk endpoints are used for large data transfers. In Packetry, look for data transactions using this endpoint number.")
    elif transfer_type == 3:  # Interrupt
        output.append("\nNote: Interrupt endpoints are used for time-critical but small data. Common for HID devices like keyboards/mice.")
    elif transfer_type == 1:  # Isochronous
        output.append("\nNote: Isochronous endpoints are used for streaming data like audio/video. They provide guaranteed bandwidth but no retry on errors.")
    
    return "\n".join(output)

def parse_hid_descriptor(data):
    if len(data) < 9:
        raise ValueError("HID Descriptor requires at least 9 bytes")
    wDescriptorLength = data[7] | (data[8] << 8)
    output = []
    output.append(f"* {data[0]:02X} → `bLength` = {data[0]} bytes")
    output.append(f"* {data[1]:02X} → `bDescriptorType` = {data[1]} (HID descriptor)")
    output.append(f"* {data[2]:02X} {data[3]:02X} → `bcdHID` = {data[3]:02X}.{data[2]:02X} (HID spec version)")
    
    # Decode country code
    country_codes = {
        0: "Not localized",
        1: "Arabic",
        2: "Belgian",
        3: "Canadian-Bilingual",
        4: "Canadian-French",
        5: "Czech Republic",
        6: "Danish",
        7: "Finnish",
        8: "French",
        9: "German",
        10: "Greek",
        11: "Hebrew",
        12: "Hungary",
        13: "International (ISO)",
        14: "Italian",
        15: "Japan (Katakana)",
        16: "Korean",
        17: "Latin American",
        18: "Dutch/Netherlands",
        19: "Norwegian",
        20: "Persian (Farsi)",
        21: "Poland",
        22: "Portuguese",
        23: "Russia",
        24: "Slovakia",
        25: "Spanish",
        26: "Swedish",
        27: "Swiss/French",
        28: "Swiss/German",
        29: "Switzerland",
        30: "Taiwan",
        31: "Turkish-Q",
        32: "UK",
        33: "US",
        34: "Yugoslavia",
        35: "Turkish-F"
    }
    country_name = country_codes.get(data[4], "Unknown")
    output.append(f"* {data[4]:02X} → `bCountryCode` = {data[4]} ({country_name})")
    
    output.append(f"* {data[5]:02X} → `bNumDescriptors` = {data[5]} (Number of class descriptors)")
    output.append(f"* {data[6]:02X} → `bDescriptorType` (Class Specific) = {data[6]} (Usually REPORT descriptor)")
    output.append(f"* {data[7]:02X} {data[8]:02X} → `wDescriptorLength` = {wDescriptorLength} bytes")
    
    # Add helpful notes for Cynthion/Packetry users
    output.append("\nNote: HID descriptors are found in Human Interface Devices (keyboards, mice, etc). In Packetry, look for GetDescriptor(Report) requests that follow to get the full HID report format.")
    
    return "\n".join(output)

def parse_interface_association_descriptor(data):
    if len(data) < 8:
        raise ValueError("Interface Association Descriptor requires at least 8 bytes")
    output = []
    output.append(f"* {data[0]:02X} → `bLength` = {data[0]} bytes")
    output.append(f"* {data[1]:02X} → `bDescriptorType` = {data[1]} (INTERFACE ASSOCIATION descriptor)")
    output.append(f"* {data[2]:02X} → `bFirstInterface` = {data[2]}")
    output.append(f"* {data[3]:02X} → `bInterfaceCount` = {data[3]}")
    
    # Add class information
    class_name = get_device_class_name(data[4])
    output.append(f"* {data[4]:02X} → `bFunctionClass` = {data[4]} ({class_name})")
    output.append(f"* {data[5]:02X} → `bFunctionSubClass` = {data[5]}")
    output.append(f"* {data[6]:02X} → `bFunctionProtocol` = {data[6]}")
    output.append(f"* {data[7]:02X} → `iFunction` = {data[7]} (String descriptor index)")
    
    # Add helpful notes for Cynthion/Packetry users
    output.append("\nNote: IADs group multiple interfaces together as a single function (like a webcam with both audio and video). In Packetry, these appear before the interfaces they reference.")
    
    return "\n".join(output)

def parse_cdc_interface_descriptor(data):
    if len(data) < 5:
        raise ValueError("CDC Interface Descriptor requires at least 5 bytes")
    output = []
    output.append(f"* {data[0]:02X} → `bLength` = {data[0]} bytes")
    output.append(f"* {data[1]:02X} → `bDescriptorType` = {data[1]} (CS_INTERFACE descriptor)")
    
    # Decode subtype
    subtypes = {
        0x00: "Header Functional",
        0x01: "Call Management Functional",
        0x02: "Abstract Control Management Functional",
        0x06: "Union Functional",
        0x07: "Country Selection Functional",
        0x08: "Telephone Operational Modes Functional",
        0x09: "USB Terminal Functional",
        0x0A: "Network Channel Terminal",
        0x0B: "Protocol Unit Functional",
        0x0C: "Extension Unit Functional",
        0x0D: "Multi-Channel Management Functional",
        0x0E: "CAPI Control Management Functional",
        0x0F: "Ethernet Networking Functional",
        0x10: "ATM Networking Functional"
    }
    subtype_name = subtypes.get(data[2], "Unknown")
    output.append(f"* {data[2]:02X} → `bDescriptorSubtype` = {data[2]} ({subtype_name})")
    
    # Different subtypes have different formats
    if data[2] == 0x00:  # Header Functional Descriptor
        output.append(f"* {data[3]:02X} {data[4]:02X} → `bcdCDC` = {data[4]:02X}.{data[3]:02X} (CDC spec version)")
    elif data[2] == 0x01:  # Call Management Functional Descriptor
        if len(data) >= 6:
            capabilities = []
            if data[3] & 0x01:
                capabilities.append("Device handles call management")
            if data[3] & 0x02:
                capabilities.append("Management over Comm interface")
            output.append(f"* {data[3]:02X} → `bmCapabilities` = 0x{data[3]:02X} ({', '.join(capabilities) if capabilities else 'None'})")
            output.append(f"* {data[4]:02X} → `bDataInterface` = {data[4]}")
    elif data[2] == 0x02:  # Abstract Control Management Functional Descriptor
        if len(data) >= 5:
            capabilities = []
            if data[3] & 0x01:
                capabilities.append("CommFeature")
            if data[3] & 0x02:
                capabilities.append("LineCoding")
            if data[3] & 0x04:
                capabilities.append("SendBreak")
            if data[3] & 0x08:
                capabilities.append("NetworkConnection")
            output.append(f"* {data[3]:02X} → `bmCapabilities` = 0x{data[3]:02X} ({', '.join(capabilities) if capabilities else 'None'})")
    elif data[2] == 0x06:  # Union Functional Descriptor
        output.append(f"* {data[3]:02X} → `bControlInterface` = {data[3]}")
        for i in range(4, data[0]):
            output.append(f"* {data[i]:02X} → `bSubordinateInterface{i-4}` = {data[i]}")
    
    # Add helpful notes for Cynthion/Packetry users
    output.append("\nNote: CDC descriptors are used in Communication Device Class devices like USB-to-Serial adapters. In Packetry, these appear within the Interface descriptors they modify.")
    
    return "\n".join(output)

def parse_bos_descriptor(data):
    if len(data) < 5:
        raise ValueError("BOS Descriptor requires at least 5 bytes")
    total_length = data[2] | (data[3] << 8)
    output = []
    output.append(f"* {data[0]:02X} → `bLength` = {data[0]} bytes")
    output.append(f"* {data[1]:02X} → `bDescriptorType` = {data[1]} (BOS descriptor)")
    output.append(f"* {data[2]:02X} {data[3]:02X} → `wTotalLength` = {total_length} bytes")
    output.append(f"* {data[4]:02X} → `bNumDeviceCaps` = {data[4]}")
    
    # Add helpful notes for Cynthion/Packetry users
    output.append("\nNote: The BOS (Binary Device Object Store) descriptor is a USB 3.0+ feature that describes device capabilities. In Packetry, look for this after device enumeration on USB 3.0+ devices.")
    
    return "\n".join(output)

def parse_dfu_functional_descriptor(data):
    if len(data) < 9:
        raise ValueError("DFU Functional Descriptor requires at least 9 bytes")
    output = []
    output.append(f"* {data[0]:02X} → `bLength` = {data[0]} bytes")
    output.append(f"* {data[1]:02X} → `bDescriptorType` = {data[1]} (DFU FUNCTIONAL descriptor)")
    output.append(f"* {data[2]:02X} → `bmAttributes` = 0x{data[2]:02X}")
    
    # Decode attributes
    attribs = []
    if data[2] & 0x01:
        attribs.append("Can Download")
    if data[2] & 0x02:
        attribs.append("Can Upload")
    if data[2] & 0x04:
        attribs.append("Manifestation Tolerant")
    if data[2] & 0x08:
        attribs.append("Will Detach")
    
    if attribs:
        output.append(f"  → {', '.join(attribs)}")
    
    output.append(f"* {data[3]:02X} {data[4]:02X} → `wDetachTimeOut` = {data[3] | (data[4] << 8)} ms")
    output.append(f"* {data[5]:02X} {data[6]:02X} → `wTransferSize` = {data[5] | (data[6] << 8)} bytes")
    output.append(f"* {data[7]:02X} {data[8]:02X} → `bcdDFUVersion` = {data[8]:02X}.{data[7]:02X}")
    
    # Add helpful notes for Cynthion/Packetry users
    output.append("\nNote: DFU (Device Firmware Upgrade) descriptors indicate the device can be reprogrammed. In Packetry, these appear within Interface descriptors for programmable devices.")
    
    return "\n".join(output)

def get_device_class_name(class_code):
    classes = {
        0x00: "Use class information in the Interface Descriptors",
        0x01: "Audio",
        0x02: "Communications and CDC Control",
        0x03: "Human Interface Device (HID)",
        0x05: "Physical",
        0x06: "Image",
        0x07: "Printer",
        0x08: "Mass Storage",
        0x09: "Hub",
        0x0A: "CDC-Data",
        0x0B: "Smart Card",
        0x0D: "Content Security",
        0x0E: "Video",
        0x0F: "Personal Healthcare",
        0x10: "Audio/Video Devices",
        0xDC: "Diagnostic Device",
        0xE0: "Wireless Controller",
        0xEF: "Miscellaneous",
        0xFE: "Application Specific",
        0xFF: "Vendor Specific"
    }
    return classes.get(class_code, "Unknown")

def get_interface_class_name(class_code):
    # Use the device class names for interfaces too, but with some additions
    interface_classes = get_device_class_name(class_code)
    
    # Additional interface classes not in the device class list
    additional_classes = {
        0x0B: "Smart Card",
        0x0D: "Content Security",
        0xDC: "Diagnostic",
        0xE0: "Wireless Controller",
        0xEF: "Miscellaneous",
        0xFE: "Application Specific"
    }
    
    return additional_classes.get(class_code, interface_classes)

def get_interface_subclass_name(class_code, subclass_code):
    # HID subclasses
    if class_code == 0x03:  # HID
        subclasses = {
            0x00: "No Subclass",
            0x01: "Boot Interface"
        }
        return subclasses.get(subclass_code, "Unknown")
    
    # Mass Storage subclasses
    elif class_code == 0x08:  # Mass Storage
        subclasses = {
            0x01: "Reduced Block Commands (RBC)",
            0x02: "SFF-8020i/MMC-2 (CD/DVD)",
            0x03: "QIC-157 (Tape)",
            0x04: "UFI (Floppy)",
            0x05: "SFF-8070i (Floppy)",
            0x06: "SCSI Transparent Command Set"
        }
        return subclasses.get(subclass_code, "Unknown")
    
    # CDC subclasses
    elif class_code == 0x02:  # CDC
        subclasses = {
            0x00: "Reserved",
            0x01: "Direct Line Control Model",
            0x02: "Abstract Control Model",
            0x03: "Telephone Control Model",
            0x04: "Multi-Channel Control Model",
            0x05: "CAPI Control Model",
            0x06: "Ethernet Networking Control Model",
            0x07: "ATM Networking Control Model",
            0x08: "Wireless Handset Control Model",
            0x09: "Device Management",
            0x0A: "Mobile Direct Line Model",
            0x0B: "OBEX",
            0x0C: "Ethernet Emulation Model"
        }
        return subclasses.get(subclass_code, "Unknown")
    
    # For other classes, just return a generic response
    return f"Subclass {subclass_code:02X}"

def get_interface_protocol_name(class_code, subclass_code, protocol_code):
    # HID protocols
    if class_code == 0x03:  # HID
        if subclass_code == 0x01:  # Boot Interface
            protocols = {
                0x00: "None",
                0x01: "Keyboard",
                0x02: "Mouse"
            }
            return protocols.get(protocol_code, "Unknown")
    
    # Mass Storage protocols
    elif class_code == 0x08:  # Mass Storage
        protocols = {
            0x00: "CBI with command completion",
            0x01: "CBI without command completion",
            0x50: "Bulk-Only Transport"
        }
        return protocols.get(protocol_code, "Unknown")
    
    # For other classes, just return a generic response
    return f"Protocol {protocol_code:02X}"

def get_vendor_name(vendor_id):
    # This is a small subset of common USB vendors
    # In a real implementation, you would load this from a file
    vendors = {
        0x046D: "Logitech",
        0x045E: "Microsoft",
        0x05AC: "Apple",
        0x8087: "Intel",
        0x0483: "STMicroelectronics",
        0x1D6B: "Linux Foundation",
        0x0403: "FTDI",
        0x0D28: "Arm",
        0x2109: "VIA Labs",
        0x0B6F: "Cynthion/Great Scott Gadgets",
        0x18D1: "Google",
        0x1209: "InterBiometrics",  # Generic descriptor used by many open hardware devices
        0x16C0: "Van Ooijen Technische Informatica",  # Used by many open hardware projects
        0x0951: "Kingston",
        0x0BDA: "Realtek",
        0x0930: "Toshiba",
        0x04B4: "Cypress",
        0x2341: "Arduino",
        0x239A: "Adafruit",
        0x04D8: "Microchip",
        0x04E8: "Samsung",
        0x054C: "Sony",
        0x0525: "NetChip",
        0x1366: "SEGGER",
        0xFFFF: "Packet capture/Cynthion placeholder"
    }
    return vendors.get(vendor_id, None)

def get_product_name(vendor_id, product_id):
    # This is a very small subset of common products
    # In a real implementation, you would load this from a file
    products = {
        (0x046D, 0xC52B): "Unifying Receiver",
        (0x046D, 0xC534): "Unifying Receiver",
        (0x05AC, 0x8290): "MacBook Internal Keyboard",
        (0x0B6F, 0x0001): "Great Scott Gadgets Cynthion",
        (0x2109, 0x3431): "USB Hub",
        (0x0483, 0x5740): "STM32 Virtual COM Port",
        (0x1209, 0x0001): "Packetry Analyzer",
        (0x1366, 0x0105): "SEGGER J-Link",
        (0x2341, 0x0043): "Arduino Uno",
        (0x239A, 0x800B): "Adafruit Feather",
        (0x0BDA, 0x8153): "Realtek USB 3.0 Ethernet Adapter",
        (0x18D1, 0x4EE1): "Google Pixel",
        (0xFFFF, 0x0001): "Packet Capture Placeholder"
    }
    return products.get((vendor_id, product_id), None)

def parse_descriptor(data):
    """
    Parse a USB descriptor based on its type
    """
    if len(data) < 2:
        raise ValueError("Invalid descriptor data, too short")
    
    descriptor_type = data[1]
    
    if descriptor_type == DEVICE_DESCRIPTOR:
        return parse_device_descriptor(data)
    elif descriptor_type == CONFIG_DESCRIPTOR:
        return parse_configuration_descriptor(data)
    elif descriptor_type == STRING_DESCRIPTOR:
        return parse_string_descriptor(data)
    elif descriptor_type == INTERFACE_DESCRIPTOR:
        return parse_interface_descriptor(data)
    elif descriptor_type == ENDPOINT_DESCRIPTOR:
        return parse_endpoint_descriptor(data)
    elif descriptor_type == HID_DESCRIPTOR and data[0] == 9:  # Check length to distinguish from DFU
        return parse_hid_descriptor(data)
    elif descriptor_type == DFU_DESCRIPTOR and data[0] == 9:  # Check length to distinguish from HID
        return parse_dfu_functional_descriptor(data)
    elif descriptor_type == IAD_DESCRIPTOR:
        return parse_interface_association_descriptor(data)
    elif descriptor_type == BOS_DESCRIPTOR:
        return parse_bos_descriptor(data)
    elif descriptor_type == 0x24:  # CDC Class-Specific descriptor
        return parse_cdc_interface_descriptor(data)
    else:
        return f"Unknown descriptor type: {descriptor_type:02X}"

def bytes_to_display_string(data):
    """Convert a bytes object to a displayable hex string"""
    hex_values = [f"{b:02X}" for b in data]
    return " ".join(hex_values)

def parse_hex_string(hex_string):
    """Parse a hex string into bytes"""
    try:
        # Remove any whitespace or common separators
        hex_string = hex_string.replace(" ", "").replace(",", "").replace(":", "").replace("\n", "").replace("\t", "")
        
        # Remove '0x' prefixes if present
        hex_string = hex_string.replace("0x", "")
        
        # Ensure even number of characters
        if len(hex_string) % 2 != 0:
            hex_string = "0" + hex_string
        
        # Convert to bytes
        return bytes.fromhex(hex_string)
    except ValueError as e:
        raise ValueError(f"Invalid hex string: {e}")

class USBDecoderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("USB Descriptor Decoder")
        self.setMinimumSize(1000, 600)
        
        # Create main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        
        # Create splitter for input/output
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)
        
        # Input panel
        self.input_widget = QWidget()
        self.input_layout = QVBoxLayout(self.input_widget)
        
        self.input_label = QLabel("Enter USB descriptor bytes as hex:")
        self.input_layout.addWidget(self.input_label)
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Example: 12 01 00 02 00 00 00 40 5E 04 3D 00 01 02 01 02 00 01")
        self.input_layout.addWidget(self.input_text)
        
        # Descriptor type selector
        self.descriptor_type_layout = QHBoxLayout()
        self.descriptor_type_label = QLabel("Descriptor Type:")
        self.descriptor_type_combo = QComboBox()
        self.descriptor_type_combo.addItem("Auto-detect", -1)
        self.descriptor_type_combo.addItem("Device", DEVICE_DESCRIPTOR)
        self.descriptor_type_combo.addItem("Configuration", CONFIG_DESCRIPTOR)
        self.descriptor_type_combo.addItem("String", STRING_DESCRIPTOR)
        self.descriptor_type_combo.addItem("Interface", INTERFACE_DESCRIPTOR)
        self.descriptor_type_combo.addItem("Endpoint", ENDPOINT_DESCRIPTOR)
        self.descriptor_type_combo.addItem("HID", HID_DESCRIPTOR)
        self.descriptor_type_combo.addItem("BOS", BOS_DESCRIPTOR)
        self.descriptor_type_combo.addItem("Interface Association", IAD_DESCRIPTOR)
        self.descriptor_type_combo.addItem("DFU Functional", DFU_DESCRIPTOR)
        
        self.descriptor_type_layout.addWidget(self.descriptor_type_label)
        self.descriptor_type_layout.addWidget(self.descriptor_type_combo)
        self.input_layout.addLayout(self.descriptor_type_layout)
        
        self.decode_button = QPushButton("Decode")
        self.decode_button.clicked.connect(self.decode_descriptor)
        self.input_layout.addWidget(self.decode_button)
        
        self.load_file_button = QPushButton("Load from File")
        self.load_file_button.clicked.connect(self.load_from_file)
        self.input_layout.addWidget(self.load_file_button)
        
        # Output panel
        self.output_widget = QWidget()
        self.output_layout = QVBoxLayout(self.output_widget)
        
        self.output_label = QLabel("Decoded Descriptor:")
        self.output_layout.addWidget(self.output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_layout.addWidget(self.output_text)
        
        self.copy_button = QPushButton("Copy to Clipboard")
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.output_layout.addWidget(self.copy_button)
        
        # Add widgets to splitter
        self.splitter.addWidget(self.input_widget)
        self.splitter.addWidget(self.output_widget)
        self.splitter.setSizes([400, 600])
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)
        
        # Add actions to toolbar
        self.clear_action = QAction("Clear All", self)
        self.clear_action.triggered.connect(self.clear_all)
        self.toolbar.addAction(self.clear_action)
        
        self.about_action = QAction("About", self)
        self.about_action.triggered.connect(self.show_about)
        self.toolbar.addAction(self.about_action)
        
        # Set dark theme option
        self.dark_theme_check = QCheckBox("Dark Theme")
        self.dark_theme_check.stateChanged.connect(self.toggle_theme)
        self.toolbar.addWidget(self.dark_theme_check)
        
        # Load settings
        self.settings = QSettings("USBDecoder", "USBDecoderApp")
        self.load_settings()
        
        # Show a welcome message
        self.output_text.setPlainText("Welcome to the USB Descriptor Decoder!\n\n"
                                     "Enter USB descriptor bytes in hex format, then click 'Decode'.\n\n"
                                     "Examples:\n"
                                     "- Device Descriptor: 12 01 00 02 00 00 00 40 5E 04 3D 00 01 02 01 02 00 01\n"
                                     "- Config Descriptor: 09 02 20 00 01 01 00 80 32\n"
                                     "- Interface Descriptor: 09 04 00 00 02 08 06 50 00\n\n"
                                     "Tip: When analyzing USB devices with Packetry or Wireshark, copy the descriptor bytes here for detailed information.")
        
    def decode_descriptor(self):
        try:
            hex_string = self.input_text.toPlainText().strip()
            if not hex_string:
                self.output_text.setPlainText("Please enter descriptor data in hex format.")
                return
            
            data = parse_hex_string(hex_string)
            if len(data) < 2:
                self.output_text.setPlainText("Descriptor data is too short.")
                return
            
            descriptor_type_index = self.descriptor_type_combo.currentIndex()
            if descriptor_type_index == 0:  # Auto-detect
                result = parse_descriptor(data)
            else:
                # Override the descriptor type if manually selected
                descriptor_type = self.descriptor_type_combo.currentData()
                if data[1] != descriptor_type:
                    # Create a new data array with the selected descriptor type
                    new_data = bytearray(data)
                    new_data[1] = descriptor_type
                    data = bytes(new_data)
                result = parse_descriptor(data)
            
            # Display the result
            self.output_text.setPlainText(result)
            self.status_bar.showMessage("Descriptor decoded successfully!", 3000)
        except Exception as e:
            self.output_text.setPlainText(f"Error: {str(e)}")
            self.status_bar.showMessage("Error decoding descriptor", 3000)
    
    def load_from_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Binary File", "", "All Files (*);;Binary Files (*.bin);;Text Files (*.txt)"
        )
        
        if not file_name:
            return
        
        try:
            with open(file_name, 'rb') as f:
                data = f.read()
            
            # If it's a text file, try to parse it as hex
            if file_name.lower().endswith('.txt'):
                with open(file_name, 'r') as f:
                    text_data = f.read()
                try:
                    data = parse_hex_string(text_data)
                except ValueError:
                    # If parsing as hex fails, use the binary data anyway
                    pass
            
            # Display the hex representation in the input field
            hex_str = bytes_to_display_string(data)
            self.input_text.setPlainText(hex_str)
            
            # Try to decode
            self.decode_descriptor()
            
        except Exception as e:
            self.output_text.setPlainText(f"Error loading file: {str(e)}")
            self.status_bar.showMessage("Error loading file", 3000)
    
    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.output_text.toPlainText())
        self.status_bar.showMessage("Copied to clipboard!", 2000)
    
    def clear_all(self):
        self.input_text.clear()
        self.output_text.clear()
        self.descriptor_type_combo.setCurrentIndex(0)
        self.status_bar.showMessage("Cleared all fields", 2000)
    
    def show_about(self):
        QMessageBox.about(self, "About USB Descriptor Decoder",
                          "USB Descriptor Decoder v1.0\n\n"
                          "A tool to decode USB descriptor bytes into human-readable format.\n\n"
                          "Useful for USB developers, security researchers, and anyone working with low-level USB protocols.\n\n"
                          "This tool helps decode standard USB descriptors including:\n"
                          "- Device descriptors\n"
                          "- Configuration descriptors\n"
                          "- Interface descriptors\n"
                          "- Endpoint descriptors\n"
                          "- HID descriptors\n"
                          "- And more specialized descriptor types\n\n"
                          "For use with Cynthion, Packetry, Wireshark, or any USB analysis tools.")
    
    def toggle_theme(self, state):
        if state == Qt.CheckState.Checked.value:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
        
        # Save the setting
        self.settings.setValue("dark_theme", state == Qt.CheckState.Checked.value)
    
    def apply_dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        
        QApplication.setPalette(dark_palette)
        
        # Set stylesheet for additional elements
        self.setStyleSheet("""
            QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }
            QTextEdit { background-color: #1e1e1e; color: #f0f0f0; }
        """)
    
    def apply_light_theme(self):
        QApplication.setPalette(QApplication.style().standardPalette())
        self.setStyleSheet("")
    
    def load_settings(self):
        # Load window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Load dark theme setting
        dark_theme = self.settings.value("dark_theme", False, type=bool)
        self.dark_theme_check.setChecked(dark_theme)
        if dark_theme:
            self.apply_dark_theme()
    
    def save_settings(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("dark_theme", self.dark_theme_check.isChecked())
    
    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for better cross-platform experience
    
    # Set application-wide font
    font = QFont("Segoe UI" if sys.platform == "win32" else "Helvetica")
    font.setPointSize(10)
    app.setFont(font)
    
    window = USBDecoderApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()