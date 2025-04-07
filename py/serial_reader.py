import serial
import threading
from PyQt5.QtCore import pyqtSignal, QObject

PACKET_SIZE = 21

class SerialReader(QObject):
    packet_received = pyqtSignal(bytes)

    def __init__(self, port, baudrate=115200):
        super().__init__()
        self.buffer = bytearray()
        self.ser = serial.Serial(
            port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            timeout=1  # Optional timeout to prevent blocking forever
        )
        self.running = False
        self.read_thread = threading.Thread(target=self.read_loop, daemon=True)

    def start(self):
        self.running = True
        self.read_thread.start()

    def stop(self):
        self.running = False
        if self.ser.is_open:
            self.ser.close()

    def send_signal(self, signal_bytes):
        if self.ser.is_open:
            self.ser.write(signal_bytes)

    def read_loop(self):
        while self.running:
            if self.ser.in_waiting:
                byte = self.ser.read(1)
                self.buffer.extend(byte)

                # Check if the packet is complete
                while len(self.buffer) >= PACKET_SIZE:
                    packet = bytes(self.buffer[:PACKET_SIZE])
                    self.packet_received.emit(packet)
                    self.buffer = self.buffer[PACKET_SIZE:]  # Remove processed packet

