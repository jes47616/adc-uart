import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
)
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import serial.tools.list_ports

from serial_reader import SerialReader
from frame import FrameProcessor
import datetime

# Define the command constants
START_CMD = "START____"
STOP_CMD = "STOP_____"
TRGMODE_CMD = "TRGMODE__"
INTMODE_CMD = "INTMODE__"


class LivePlotter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live ADC/GPIO Plot")
        self.resize(1000, 600)

        # Time reference
        self.start_time_us = None

        # Data buffers
        self.adc_time_data = []
        self.adc_signal_data = []

        # Digital signal data
        self.gpio_time_data = []
        self.gpio_signal_data = []

        # Serial Reader and Frame Processor
        self.serial_reader = None
        self.frame_processor = FrameProcessor()

        # Flag to track plotting state
        self.is_running = False

        # --- Plot Widget ---
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel("left", "Voltage", "V")
        self.plot_widget.setLabel("bottom", "Time", "ms")
        self.plot_widget.setYRange(0, 3.3)

        # Create curves for both signals
        self.adc_curve = self.plot_widget.plot([], [], pen=pg.mkPen("b", width=2))
        self.gpio_curve = self.plot_widget.plot([], [], pen=pg.mkPen("r", width=2))
        # --- Controls ---
        self.port_selector = QComboBox()
        self.refresh_ports()
        self.port_selector.currentTextChanged.connect(self.connect_serial)

        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.trgmode_btn = QPushButton("Continuous Mode")
        self.intmode_btn = QPushButton("Interrupt Mode")

        self.start_btn.clicked.connect(self.start_plotting)
        self.stop_btn.clicked.connect(self.stop_plotting)
        self.trgmode_btn.clicked.connect(lambda: self.send_command(TRGMODE_CMD))
        self.intmode_btn.clicked.connect(lambda: self.send_command(INTMODE_CMD))

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.port_selector)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.trgmode_btn)
        btn_layout.addWidget(self.intmode_btn)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(100)

        # --- Final Layout ---
        layout = QVBoxLayout()
        layout.addLayout(btn_layout)
        layout.addWidget(self.plot_widget)
        layout.addWidget(self.log_output)

        self.setLayout(layout)
        self.set_controls_enabled(True)

    def start_plotting(self):
        if not self.is_running:
            self.is_running = True
            self.set_controls_enabled(False)  # Disable other controls
            self.adc_time_data.clear()
            self.adc_signal_data.clear()
            self.gpio_time_data.clear()
            self.gpio_signal_data.clear()
            self.adc_curve.setData([], [])
            self.gpio_curve.setData([], [])
            self.start_time_us = None
            print("[INFO] Plotting started.")
            self.send_command(START_CMD)

    def set_controls_enabled(self, enabled):
        self.port_selector.setEnabled(enabled)
        self.trgmode_btn.setEnabled(enabled)
        self.intmode_btn.setEnabled(enabled)
        self.start_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(not enabled)  # Stop enabled only when plotting

    def stop_plotting(self):
        if self.is_running:
            self.is_running = False
            self.set_controls_enabled(True)  # Re-enable other controls
            print("[INFO] Plotting stopped.")
            self.send_command(STOP_CMD)

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        self.port_selector.clear()
        for port in ports:
            self.port_selector.addItem(port.device)

    def connect_serial(self, port_name):
        if self.serial_reader:
            self.serial_reader.stop()
            self.serial_reader = None

        if port_name:
            try:
                self.serial_reader = SerialReader(port_name)
                self.serial_reader.packet_received.connect(self.handle_packet)
                if not self.serial_reader.running:
                    self.serial_reader.start()
                print(f"[INFO] Connected to {port_name}")
            except Exception as e:
                print(f"[ERROR] Could not connect: {e}")

    def send_command(self, cmd_str):
        if self.serial_reader and self.serial_reader.ser.is_open:
            print(f"[CMD] Sending: {cmd_str}")
            self.serial_reader.ser.write(cmd_str.encode("ascii"))

    def log_packet(self, packet: bytes):
        hex_str = " ".join(f"{b:02X}" for b in packet)
        self.log_output.append(hex_str)

    def handle_packet(self, packet):
        print(f"Packet header: 0x{packet[0]:02X}")

        self.log_packet(packet)

        header = packet[0]
        data = packet[1:]

        if header == 0xC0:  # Start timestamp
            if len(data) >= 4:
                self.start_time_us = int.from_bytes(
                    data[:4], byteorder="little"
                )  # Use all 4 bytes for timestamp
                self.adc_time_data.clear()
                self.adc_signal_data.clear()
                self.gpio_time_data.clear()
                self.gpio_signal_data.clear()

                # Initialize digital signal with a starting point at time 0
                self.gpio_time_data.append(0)
                self.gpio_signal_data.append(0)  # Assume starting at LOW
                self.gpio_curve.setData(self.gpio_time_data, self.gpio_signal_data)

                self.adc_curve.setData([], [])
                print(f"[SYNC] Start time: {self.start_time_us} µs")
            else:
                print(f"Invalid data for timestamp: {data}")
                return

        elif header == 0xA0 and self.start_time_us is not None:
            if self.is_running:
                if len(data) > 0:
                    voltages = self.frame_processor.parse_frame(data)

                    # Generate relative time values in ms using the frame processor
                    relative_times_ms = (
                        self.frame_processor.generate_time_axis(len(voltages)) * 1000.0
                    )

                    # Determine where the time continues from
                    last_time = (
                        self.adc_time_data[-1]
                        + self.frame_processor.sample_period * 1000
                        if self.adc_time_data
                        else 0
                    )

                    # Shift the new times to continue smoothly
                    times = [last_time + t for t in relative_times_ms]

                    # Update time and voltage data
                    self.adc_time_data.extend(times)
                    self.adc_signal_data.extend(voltages)

                    # Update the plot
                    self.adc_curve.setData(self.adc_time_data, self.adc_signal_data)
                else:
                    print("No ADC data found")
                    return

        elif header == 0xB0 and self.start_time_us is not None:
            print(f"[DEBUG] GPIO packet received! Data length: {len(data)} bytes")
            print(f"[DEBUG] Raw GPIO data: {' '.join([f'{b:02X}' for b in data])}")

            if len(data) % 5 == 0:  # GPIO event format (timestamp + level)
                new_time_data, new_signal_data = self.handle_gpio_data(data)
                self.gpio_time_data.extend(new_time_data)
                self.gpio_signal_data.extend(new_signal_data)
                self.gpio_curve.setData(self.gpio_time_data, self.gpio_signal_data)
            else:
                print(f"Invalid GPIO data size: {len(data)} bytes")
                return

    def handle_gpio_data(self, data):
        # keep last known point so the first transition is drawn correctly
        timestamps = [self.gpio_time_data[-1]]
        levels = [self.gpio_signal_data[-1]]

        for i in range(0, len(data), 5):
            ts_ms = int.from_bytes(data[i : i + 4], byteorder="little") / 1000.0
            if ts_ms == 0:
                continue

            level = 0 if not data[i + 4] else 3.3  # already 0 or 1

            # draw a vertical edge only if level changed
            if levels[-1] != level:
                timestamps.append(ts_ms)
                levels.append(levels[-1])  # drop to previous level first
            timestamps.append(ts_ms)
            levels.append(level)  # then new level

        return timestamps[1:], levels[1:]

    def closeEvent(self, event):
        # Stop the serial reader first
        if self.serial_reader:
            self.serial_reader.stop()

        # Save GPIO data arrays if available
        try:
            if self.gpio_time_data and self.gpio_signal_data:
                # Create a timestamp for the filename
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"gpio_data_{timestamp}.csv"

                # Save data as CSV file with time,value pairs
                with open(filename, "w") as f:
                    f.write("Time_ms,Signal_Level\n")  # Header
                    for t, v in zip(self.gpio_time_data, self.gpio_signal_data):
                        f.write(f"{t:.6f},{v:.6f}\n")

                print(f"[INFO] GPIO data saved to {filename}")
        except Exception as e:
            print(f"[ERROR] Failed to save GPIO data: {str(e)}")

        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LivePlotter()
    win.show()
    win.show()
    sys.exit(app.exec_())

    win.show()
    win.show()
    sys.exit(app.exec_())
