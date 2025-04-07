import sys
import serial
import threading
import serial.tools.list_ports
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout,
    QComboBox, QTableWidget, QTableWidgetItem, QLabel, QSplitter, QHeaderView
)
from PyQt5.QtCore import pyqtSignal, QObject, Qt

START_SIGNAL = b'\x11'
STOP_SIGNAL = b'\x22'
PACKET_SIZE = 1200

class SerialReader(QObject):
    data_received = pyqtSignal(str)
    packet_received = pyqtSignal(bytes)

    def __init__(self, port, baudrate=115200):
        super().__init__()
        self.ser = serial.Serial(port, baudrate=baudrate, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE)
        self.read_thread = threading.Thread(target=self.read_data)
        self.read_thread.daemon = True
        self.running = True
        self.in_frame_mode = False
        self.buffer = bytearray()

    def start(self):
        self.read_thread.start()

    def stop(self):
        self.running = False
        if self.ser.is_open:
            self.ser.close()

    def send_signal(self, signal_byte):
        self.ser.write(signal_byte)
        if signal_byte == START_SIGNAL:
            self.in_frame_mode = True
            self.buffer.clear()
        elif signal_byte == STOP_SIGNAL:
            self.in_frame_mode = False
            self.buffer.clear()

    def read_data(self):
        while self.running:
            if self.ser.in_waiting:
                byte = self.ser.read(1)

                if self.in_frame_mode:
                    self.buffer.extend(byte)
                    if len(self.buffer) >= PACKET_SIZE:
                        self.packet_received.emit(bytes(self.buffer))
                        self.buffer.clear()
                else:
                    try:
                        self.data_received.emit(byte.decode('ascii', errors='replace'))
                    except:
                        pass
