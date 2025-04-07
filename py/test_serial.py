import sys
import time
from PyQt5.QtWidgets import QApplication
from serial_reader import SerialReader  # Make sure this is your correct file/module name

def handle_packet(packet):
    print(f"[RECEIVED PACKET] {packet.hex(' ')}")


def main():
    # Replace this with your actual COM port, e.g., "COM4" on Windows or "/dev/ttyUSB0" on Linux
    port = "COM7"  # <-- Change this!

    try:
        app = QApplication(sys.argv)

        reader = SerialReader(port)
        reader.packet_received.connect(handle_packet)
        reader.start()

        print("[INFO] SerialReader started. Listening for packets...\n")
        print("Press Ctrl+C to stop.\n")

        # Keep the Qt app running
        sys.exit(app.exec_())

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()
