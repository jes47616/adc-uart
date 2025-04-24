import serial
import threading
from PyQt5.QtCore import QObject, pyqtSignal

PACKET_SIZE = 21
VALID_HEADERS = {0xA0, 0xB0, 0xC0, 0xD0}


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
            timeout=1,  # Prevent blocking forever
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

    def log_packet(self, packet: bytes):
        hex_str = " ".join(f"{b:02X}" for b in packet)
        # print(f"[PACKET] {hex_str}")

    def log_desync(self, byte: int):
        print(f"[DESYNC] Dropped byte: {byte:02X}")

    def read_loop(self):
        while self.running:
            try:
                data = self.ser.read(self.ser.in_waiting or 1)
                if not data:
                    continue

                self.buffer.extend(data)

                while len(self.buffer) >= PACKET_SIZE:
                    if self.buffer[0] in VALID_HEADERS:
                        packet = bytes(self.buffer[:PACKET_SIZE])
                        self.log_packet(packet)
                        self.packet_received.emit(packet)
                        self.buffer = self.buffer[PACKET_SIZE:]
                    else:
                        self.log_desync(self.buffer[0])
                        self.buffer.pop(0)

            except serial.SerialException as e:
                print(f"[ERROR] Serial exception: {e}")
                self.running = False
                break
            except Exception as e:
                print(f"[ERROR] Unexpected exception: {e}")
                self.running = False
                break
