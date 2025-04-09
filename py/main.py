import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox
)
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import serial.tools.list_ports

from serial_reader import SerialReader
from frame import FrameProcessor

# Define the command constants
START_CMD    = "START____"
STOP_CMD     = "STOP_____"
TRGMODE_CMD  = "TRGMODE__"
INTMODE_CMD  = "INTMODE__"

class LivePlotter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live ADC/GPIO Plot")
        self.resize(1000, 600)

        # Time reference
        self.start_time_us = None

        # Data buffers
        self.time_data = []
        self.voltage_data = []
        self.gpio_lines = []
        
        # Digital signal data
        self.digital_time_data = []
        self.digital_signal_data = []

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
        
        # Create a second Y axis for digital signal
        self.digital_axis = pg.ViewBox()
        self.plot_widget.scene().addItem(self.digital_axis)
        self.plot_widget.getAxis("right").linkToView(self.digital_axis)
        self.plot_widget.getAxis("right").setLabel("Digital Signal")
        self.digital_axis.setYRange(-0.1, 1.1)  # For boolean values (0-1)
        
        # Link X axes
        self.digital_axis.setXLink(self.plot_widget.getViewBox())
        
        # Create curves for both signals
        self.adc_curve = self.plot_widget.plot(pen=pg.mkPen("b", width=2))
        self.digital_curve = pg.PlotCurveItem(pen=pg.mkPen("r", width=2))
        self.digital_axis.addItem(self.digital_curve)
        
        # Update views on resize
        self.plot_widget.getViewBox().sigResized.connect(self._update_views)

        # --- Controls ---
        self.port_selector = QComboBox()
        self.refresh_ports()
        self.port_selector.currentTextChanged.connect(self.connect_serial)

        self.start_btn    = QPushButton("Start")
        self.stop_btn     = QPushButton("Stop")
        self.trgmode_btn  = QPushButton("Trigger Mode")
        self.intmode_btn  = QPushButton("Internal Mode")

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

    def _update_views(self):
        # Update the second ViewBox when the first one changes
        self.digital_axis.setGeometry(self.plot_widget.getViewBox().sceneBoundingRect())
        self.digital_axis.linkedViewChanged(self.plot_widget.getViewBox(), self.digital_axis.XAxis)

    def start_plotting(self):
        if not self.is_running:
            self.is_running = True
            self.set_controls_enabled(False)  # Disable other controls
            self.time_data.clear()
            self.voltage_data.clear()
            self.digital_time_data.clear()
            self.digital_signal_data.clear()
            self.clear_gpio_lines()
            self.adc_curve.setData([], [])
            self.digital_curve.setData([], [])
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
                self.start_time_us = int.from_bytes(data[:4], byteorder="little")  # Use all 4 bytes for timestamp
                self.time_data.clear()
                self.voltage_data.clear()
                self.digital_time_data.clear()
                self.digital_signal_data.clear()
                
                # Initialize digital signal with a starting point at time 0
                self.digital_time_data.append(0)
                self.digital_signal_data.append(0)  # Assume starting at LOW
                self.digital_curve.setData(self.digital_time_data, self.digital_signal_data)
                
                self.clear_gpio_lines()
                self.adc_curve.setData([], [])
                print(f"[SYNC] Start time: {self.start_time_us} µs")
            else:
                print(f"Invalid data for timestamp: {data}")
                return

        elif header == 0xA0 and self.start_time_us is not None:
            if self.is_running:
                if len(data) > 0:
                    voltages = self.frame_processor.parse_frame(data)
                    sample_interval_us = 1000  # Adjust as needed
                    last_time = self.time_data[-1] if self.time_data else 0
                    times = [last_time + (i * sample_interval_us / 1000.0) for i in range(1, len(voltages) + 1)]
                    self.time_data.extend(times)
                    self.voltage_data.extend(voltages)
                    self.adc_curve.setData(self.time_data, self.voltage_data)
                else:
                    print("No ADC data found")
                    return

        elif header == 0xB0 and self.start_time_us is not None:
            print(f"[DEBUG] GPIO packet received! Data length: {len(data)} bytes")
            print(f"[DEBUG] Raw GPIO data: {' '.join([f'{b:02X}' for b in data])}")
            
            if len(data) % 5 == 0:  # GPIO event format (timestamp + level)
                for i in range(0, len(data), 5):
                    ts_bytes = data[i:i+4]
                    level = data[i+4]
                    
                    # Extract the timestamp in microseconds
                    gpio_time_us = int.from_bytes(ts_bytes, byteorder="little")
                    
                    # Convert to milliseconds for display
                    rel_time_ms = gpio_time_us / 1000.0
                    
                    # Debug print
                    print(f"[GPIO] Event at {rel_time_ms:.3f} ms, level={level}")
                    
                    # Add vertical line for event visualization
                    self.add_gpio_line(rel_time_ms, level)
                    
                    # Add point to digital signal plot for continuous visualization
                    if self.digital_time_data and rel_time_ms > self.digital_time_data[-1]:
                        # Add a point just before the transition to create a step
                        self.digital_time_data.append(rel_time_ms - 0.001)
                        self.digital_signal_data.append(self.digital_signal_data[-1])  # Previous state
                    
                    # Add the transition point
                    self.digital_time_data.append(rel_time_ms)
                    self.digital_signal_data.append(1 if level else 0)  # Use actual level
                    
                    # Update the digital plot
                    self.digital_curve.setData(self.digital_time_data, self.digital_signal_data)
            else:
                print(f"Invalid GPIO data size: {len(data)} bytes")
                return

    def add_gpio_line(self, time_ms, level):
        color = "r" if level else "g"
        line = pg.InfiniteLine(pos=time_ms, angle=90, pen=pg.mkPen(color, width=1.5, style=Qt.DashLine))
        self.plot_widget.addItem(line)
        self.gpio_lines.append(line)

    def clear_gpio_lines(self):
        for line in self.gpio_lines:
            self.plot_widget.removeItem(line)
        self.gpio_lines.clear()

    def closeEvent(self, event):
        if self.serial_reader:
            self.serial_reader.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LivePlotter()
    win.show()
    sys.exit(app.exec_())
