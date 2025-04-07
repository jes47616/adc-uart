import sys
import serial
import serial.tools.list_ports
from datetime import datetime
import numpy as np
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QSplitter,
    QHeaderView,
    QDoubleSpinBox,
    QLineEdit,
    QStatusBar,
)
from PyQt5.QtCore import Qt
from serial_reader import SerialReader
from frame import FrameProcessor
from PyQt5 import QtWidgets

# Define the command constants
START_CMD = "START____"
STOP_CMD = "STOP_____"
RESET_CMD = "RESET____"
TRGMODE_CMD = "TRGMODE__"
INTMODE_CMD = "INTMODE__"


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ADC Serial Interface")
        self.resize(1200, 800)

        # Initialize frame processor
        self.frame_processor = FrameProcessor()

        # Create plot widget
        import pyqtgraph as pg

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel("left", "Voltage", "V")
        self.plot_widget.setLabel("bottom", "Time", "ms")
        self.plot_curve = self.plot_widget.plot(pen=pg.mkPen("b", width=2))
        self.plot_widget.setYRange(0, 3.3)  # Default range for 3.3V ADC

        # UI Elements
        self.port_selector = QComboBox()
        self.refresh_ports()

        # Command buttons
        self.connect_button = QPushButton("Connect")
        self.disconnect_button = QPushButton("Disconnect")
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.reset_button = QPushButton("Reset")
        self.trgmode_button = QPushButton("Trigger Mode")
        self.intmode_button = QPushButton("Interrupt Mode")

        # Status label
        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setStyleSheet("font-weight: bold;")
        self.update_status_style(False)

        # Configure button colors
        self.connect_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.disconnect_button.setStyleSheet("background-color: #f44336; color: white;")
        self.start_button.setStyleSheet("background-color: #2196F3; color: white;")
        self.stop_button.setStyleSheet("background-color: #ff9800; color: white;")
        self.reset_button.setStyleSheet("background-color: #9E9E9E; color: white;")
        self.trgmode_button.setStyleSheet("background-color: #673AB7; color: white;")
        self.intmode_button.setStyleSheet("background-color: #009688; color: white;")

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("font-family: monospace;")

        self.frame_table = QTableWidget(0, 3)
        self.frame_table.setHorizontalHeaderLabels(["Timestamp", "Frame", "Preview"])
        self.frame_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.frame_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.frame_table.setSelectionMode(QTableWidget.SingleSelection)
        self.frame_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.frame_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.frame_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        self.detail_area = QTextEdit()
        self.detail_area.setReadOnly(True)
        self.detail_area.setStyleSheet("font-family: monospace;")

        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel("left", "Voltage", "V")
        self.plot_widget.setLabel("bottom", "Time", "ms")
        self.plot_curve = self.plot_widget.plot(pen=pg.mkPen("b", width=2))
        self.plot_widget.setYRange(0, 3.3)  # Default range for 3.3V ADC

        # Layout setup
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Serial Port:"))
        controls_layout.addWidget(self.port_selector)
        controls_layout.addWidget(self.connect_button)
        controls_layout.addWidget(self.disconnect_button)
        controls_layout.addWidget(self.status_label)
        controls_layout.addStretch()

        # Command buttons layout
        commands_layout = QHBoxLayout()
        commands_layout.addWidget(self.start_button)
        commands_layout.addWidget(self.stop_button)
        commands_layout.addWidget(self.reset_button)
        commands_layout.addWidget(self.trgmode_button)
        commands_layout.addWidget(self.intmode_button)

        # Create containers for better layout control
        frame_table_container = QWidget()
        frame_table_layout = QVBoxLayout(frame_table_container)
        frame_table_layout.setContentsMargins(0, 0, 0, 0)
        frame_table_layout.addWidget(QLabel("<b>Received Frames</b>"))
        frame_table_layout.addWidget(self.frame_table)

        detail_area_container = QWidget()
        detail_area_layout = QVBoxLayout(detail_area_container)
        detail_area_layout.setContentsMargins(0, 0, 0, 0)
        detail_area_layout.addWidget(QLabel("<b>Frame Details (Hex)</b>"))
        detail_area_layout.addWidget(self.detail_area)

        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.addWidget(QLabel("<b>ADC Voltage Plot</b>"))
        plot_layout.addWidget(self.plot_widget)

        # Horizontal splitter for details and plot
        h_splitter = QSplitter(Qt.Horizontal)
        h_splitter.addWidget(detail_area_container)
        h_splitter.addWidget(plot_container)
        h_splitter.setStretchFactor(0, 1)
        h_splitter.setStretchFactor(1, 2)

        # Vertical splitter for frames and bottom panel
        splitter1 = QSplitter(Qt.Vertical)
        splitter1.addWidget(frame_table_container)
        splitter1.addWidget(h_splitter)
        splitter1.setStretchFactor(0, 1)
        splitter1.setStretchFactor(1, 2)

        log_area_container = QWidget()
        log_area_layout = QVBoxLayout(log_area_container)
        log_area_layout.setContentsMargins(0, 0, 0, 0)
        log_area_layout.addWidget(QLabel("<b>Log Output</b>"))
        log_area_layout.addWidget(self.log_area)

        # Main vertical splitter
        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.addWidget(splitter1)
        main_splitter.addWidget(log_area_container)
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 1)

        main_layout = QVBoxLayout()
        main_layout.addLayout(controls_layout)
        main_layout.addLayout(commands_layout)
        main_layout.addWidget(main_splitter)

        self.setLayout(main_layout)

        # Application state
        self.serial_reader = None
        self.frames = []  # Stores tuples of (hex_string, voltage_array)
        self.current_frame_index = -1

        # Connect signals
        self.connect_button.clicked.connect(self.setup_serial)
        self.disconnect_button.clicked.connect(self.disconnect_serial)
        self.start_button.clicked.connect(lambda: self.send_command(START_CMD))
        self.stop_button.clicked.connect(lambda: self.send_command(STOP_CMD))
        self.reset_button.clicked.connect(lambda: self.send_command(RESET_CMD))
        self.trgmode_button.clicked.connect(lambda: self.send_command(TRGMODE_CMD))
        self.intmode_button.clicked.connect(lambda: self.send_command(INTMODE_CMD))
        self.frame_table.cellClicked.connect(self.show_frame_detail)

        # Initialize UI state
        self.update_ui_connection_state(False)

    def update_status_style(self, connected):
        """Update the status label style based on connection state"""
        if connected:
            self.status_label.setText("Status: Connected")
            self.status_label.setStyleSheet(
                """
                font-weight: bold;
                color: green;
                background-color: #e8f5e9;
                padding: 2px 5px;
                border-radius: 3px;
            """
            )
        else:
            self.status_label.setText("Status: Disconnected")
            self.status_label.setStyleSheet(
                """
                font-weight: bold;
                color: red;
                background-color: #ffebee;
                padding: 2px 5px;
                border-radius: 3px;
            """
            )

    def update_ui_connection_state(self, connected):
        """Update all UI elements based on connection state"""
        self.connect_button.setEnabled(not connected)
        self.disconnect_button.setEnabled(connected)

        # Enable/disable command buttons
        for btn in [self.start_button, self.stop_button, self.reset_button, self.trgmode_button, self.intmode_button]:
            btn.setEnabled(connected)

        # Update status label
        self.update_status_style(connected)

    def refresh_ports(self):
        self.port_selector.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_selector.addItem(port.device)
        if not ports:
            self.port_selector.addItem("No ports available")

    def setup_serial(self):
        if self.serial_reader:
            self.serial_reader.stop()

        port = self.port_selector.currentText()
        if port == "No ports available":
            self.log_area.append("[ERROR] No serial ports available")
            return

        try:
            self.serial_reader = SerialReader(port)
            self.serial_reader.data_received.connect(self.display_text)
            self.serial_reader.packet_received.connect(self.display_packet)
            self.serial_reader.start()
            self.log_area.append(f"[INFO] Connected to {port}")
            self.update_ui_connection_state(True)

        except Exception as e:
            self.log_area.append(f"[ERROR] Failed to connect: {str(e)}")
            self.update_ui_connection_state(False)

    def disconnect_serial(self):
        if self.serial_reader:
            self.serial_reader.stop()
            self.serial_reader = None
            self.log_area.append("[INFO] Disconnected from serial port")
            self.update_ui_connection_state(False)

    def display_text(self, text):
        text = text.strip()
        if text:
            self.log_area.append(text)

    def display_packet(self, packet_bytes):
        try:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            hex_string = " ".join(f"{b:02X}" for b in packet_bytes)
            preview = hex_string[:60] + ("..." if len(hex_string) > 60 else "")

            # Process the frame to voltage values
            voltages = self.frame_processor.parse_frame(packet_bytes)

            # Store both raw and processed data
            self.frames.append((hex_string, voltages))

            row_position = self.frame_table.rowCount()
            self.frame_table.insertRow(row_position)
            self.frame_table.setItem(row_position, 0, QTableWidgetItem(timestamp))
            self.frame_table.setItem(row_position, 1, QTableWidgetItem(f"Frame #{len(self.frames)}"))
            self.frame_table.setItem(row_position, 2, QTableWidgetItem(preview))

            # Auto-scroll to the new row
            self.frame_table.scrollToBottom()

        except Exception as e:
            self.log_area.append(f"[ERROR] Processing packet: {str(e)}")

    def show_frame_detail(self, row, column):
        if 0 <= row < len(self.frames):
            self.current_frame_index = row
            hex_string, voltages = self.frames[row]
            self.detail_area.setPlainText(hex_string)

            # Update the plot with the selected frame's data
            time_axis = self.frame_processor.generate_time_axis(len(voltages))
            self.plot_curve.setData(time_axis, voltages)

            # Calculate stats
            min_v = np.min(voltages)
            max_v = np.max(voltages)
            avg_v = np.mean(voltages)

            # Update plot title with stats
            self.plot_widget.setTitle(f"Frame #{row+1} | Min: {min_v:.2f}V | Max: {max_v:.2f}V | Avg: {avg_v:.2f}V")

    def send_command(self, command):
        if self.serial_reader:
            try:
                # Ensure the command is exactly 9 bytes
                cmd_bytes = command.ljust(9).encode("ascii")[:9]
                self.serial_reader.send_signal(cmd_bytes)
                self.log_area.append(f"[CMD] Sent: {command.strip()}")
            except Exception as e:
                self.log_area.append(f"[ERROR] Sending command {command}: {str(e)}")

    def closeEvent(self, event):
        if self.serial_reader:
            self.serial_reader.stop()
        event.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
