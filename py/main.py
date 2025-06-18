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
RESET_CMD = "RESET____"


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
        self.gpio_binary_data = []

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
        self.plot_widget.setYRange(-2.0, 2.0)  # Adjusted for centered signal

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
        self.reset_btn = QPushButton("Reset")

        self.start_btn.clicked.connect(self.start_plotting)
        self.stop_btn.clicked.connect(self.stop_plotting)
        self.trgmode_btn.clicked.connect(lambda: self.send_command(TRGMODE_CMD))
        self.intmode_btn.clicked.connect(lambda: self.send_command(INTMODE_CMD))
        self.reset_btn.clicked.connect(lambda: self.send_command(RESET_CMD))

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.port_selector)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.trgmode_btn)
        btn_layout.addWidget(self.intmode_btn)
        btn_layout.addWidget(self.reset_btn)

        # --- Bottom Widgets ---
        # Left widget for hex data
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(100)
        
        # Middle widget for system information
        self.system_info_widget = QTextEdit()
        self.system_info_widget.setReadOnly(True)
        self.system_info_widget.setMinimumHeight(100)
        
        # Right widget for phase angle analysis
        self.phase_angle_widget = QTextEdit()
        self.phase_angle_widget.setReadOnly(True)
        self.phase_angle_widget.setMinimumHeight(100)
        
        # Create bottom layout to hold the three widgets
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.log_output)
        bottom_layout.addWidget(self.system_info_widget)
        bottom_layout.addWidget(self.phase_angle_widget)

        # --- Final Layout ---
        layout = QVBoxLayout()
        layout.addLayout(btn_layout)
        layout.addWidget(self.plot_widget)
        layout.addLayout(bottom_layout)  # Add the bottom layout instead of just log_output

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
            self.gpio_binary_data.clear()
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
        self.reset_btn.setEnabled(enabled)

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
        # print(f"Packet header: 0x{packet[0]:02X}")

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
                self.gpio_binary_data.clear()

                # Initialize digital signal with a starting point at time 0
                self.gpio_time_data.append(0)
                self.gpio_signal_data.append(0)  # Assume starting at LOW
                self.gpio_binary_data.append(0)
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
                    # print("Adding ADC data to plot")
                    self.adc_curve.setData(self.adc_time_data, self.adc_signal_data)
                else:
                    print("No ADC data found")
                    return

        elif header == 0xB0 and self.start_time_us is not None:
            # print(f"[DEBUG] GPIO packet received! Data length: {len(data)} bytes")
            # print(f"[DEBUG] Raw GPIO data: {' '.join([f'{b:02X}' for b in data])}")

            if len(data) % 5 == 0:  # GPIO event format (timestamp + level)
                new_time_data, new_display_data, new_binary_data = self.handle_gpio_data(data)
                self.gpio_time_data.extend(new_time_data)
                self.gpio_signal_data.extend(new_display_data)
                self.gpio_binary_data.extend(new_binary_data)
                # print("Adding GPIO data to plot")
                self.gpio_curve.setData(self.gpio_time_data, self.gpio_signal_data)
                
                # Process arc analysis when GPIO events are detected
                self.process_arc_analysis()
                
                # Log packet
                self.log_packet(packet)

    def detect_arc_start_time(self, gpio_times, gpio_levels):
        """
        Detect the arc start time (first rising edge of GPIO signal).
        
        Args:
            gpio_times: List of GPIO event timestamps
            gpio_levels: List of GPIO signal levels (0 or 1)
            
        Returns:
            Arc start time in ms, or None if not found
        """
        if not gpio_times or len(gpio_times) < 2:
            return None
            
        # Find the first rising edge (transition from 0 to 1)
        for i in range(1, len(gpio_levels)):
            if gpio_levels[i-1] == 0 and gpio_levels[i] == 1:
                return gpio_times[i]
                
        return None
        
    def detect_arc_end_time(self, gpio_times, gpio_levels):
        """
        Detect the raw arc end time (falling edge after which signal stays LOW for ≥5ms).
        
        Args:
            gpio_times: List of GPIO event timestamps
            gpio_levels: List of GPIO signal levels (0 or 1)
            
        Returns:
            Tuple of (raw_end_time, last_pair_duration) in ms, or (None, None) if not found
        """
        if not gpio_times or len(gpio_times) < 2:
            return None, None
            
        # Find falling edges
        falling_edges = []
        for i in range(1, len(gpio_levels)):
            if gpio_levels[i-1] == 1 and gpio_levels[i] == 0:
                falling_edges.append((i, gpio_times[i]))
                
        # Check each falling edge to see if signal stays LOW for at least 5ms
        for idx, (i, time) in enumerate(falling_edges):
            # Check if this is the last falling edge
            if idx == len(falling_edges) - 1:
                if i < len(gpio_times) - 1 and gpio_times[-1] - time >= 5.0:
                    # If we're at the last falling edge and there's 5ms of data after it
                    # Find the last pulse pair duration
                    last_pair_duration = self.find_last_pulse_pair_duration(gpio_times, gpio_levels, i)
                    return time, last_pair_duration
            else:
                # Check if signal stays LOW until next rising edge
                next_rising_idx = None
                for j in range(i+1, len(gpio_levels)):
                    if gpio_levels[j] == 1:
                        next_rising_idx = j
                        break
                        
                if next_rising_idx is None:
                    # No more rising edges, check if we have 5ms of data after this falling edge
                    if gpio_times[-1] - time >= 5.0:
                        last_pair_duration = self.find_last_pulse_pair_duration(gpio_times, gpio_levels, i)
                        return time, last_pair_duration
                elif gpio_times[next_rising_idx] - time >= 5.0:
                    # Next rising edge is more than 5ms away
                    last_pair_duration = self.find_last_pulse_pair_duration(gpio_times, gpio_levels, i)
                    return time, last_pair_duration
                    
        return None, None
        
    def find_last_pulse_pair_duration(self, gpio_times, gpio_levels, end_idx):
        """
        Find the duration of the first pulse pair AFTER the arc end.
        
        Args:
            gpio_times: List of GPIO event timestamps
            gpio_levels: List of GPIO signal levels (0 or 1)
            end_idx: Index of the falling edge that marks the end of the arc
            
        Returns:
            Duration of the pulse pair in ms, or 0 if not found
        """
        # Look forward from end_idx to find the first complete pulse pair after the arc end
        if end_idx >= len(gpio_times) - 1:
            return 0  # Not enough data after end_idx
            
        # Find the first two rising edges and two falling edges after end_idx
        rising_edges = []
        falling_edges = []
        
        # Start searching from the index after end_idx
        i = end_idx + 1
        while i < len(gpio_levels) and (len(rising_edges) < 2 or len(falling_edges) < 2):
            if i > 0:
                # Detect rising edge
                if gpio_levels[i-1] == 0 and gpio_levels[i] == 1:
                    rising_edges.append(i)
                # Detect falling edge
                elif gpio_levels[i-1] == 1 and gpio_levels[i] == 0:
                    falling_edges.append(i)
            i += 1
        
        # If we found at least 2 rising edges and 2 falling edges, we can calculate the pulse pair duration
        if len(rising_edges) >= 2 and len(falling_edges) >= 2:
            # First rising edge to second falling edge
            t_rising1 = gpio_times[rising_edges[0]]
            t_falling2 = gpio_times[falling_edges[1]]
            
            # Calculate the duration from first rising edge to second falling edge
            return t_falling2 - t_rising1
                
        return 0  # Default if we can't find a valid pulse pair

    def find_zero_crossings(self, gpio_times, gpio_levels, raw_end_time=None):
        """
        Find all voltage zero-crossing timestamps from GPIO double-pulses.
        If raw_end_time is provided, only include zero-crossings after this time.
        
        Args:
            gpio_times: List of GPIO event timestamps
            gpio_levels: List of GPIO signal levels (0 or 1)
            raw_end_time: Optional, only include zero-crossings after this time
            
        Returns:
            List of zero-crossing timestamps in ms
        """
        zero_crossings = []
        
        # We need to identify double-pulse patterns
        # A double-pulse consists of two closely spaced pulses
        i = 0
        while i < len(gpio_times) - 3:  # Need at least 4 points for a complete double-pulse
            # Check for rising edge
            if i > 0 and gpio_levels[i-1] == 0 and gpio_levels[i] == 1:
                # Found first rising edge (t1)
                t1 = gpio_times[i]
                
                # Skip if this is before the raw end time
                if raw_end_time is not None and t1 < raw_end_time:
                    i += 1
                    continue
                
                # Look for the second falling edge within a reasonable timeframe
                # Double-pulses should be close together (e.g., within 2ms)
                j = i + 1
                found_second_falling = False
                
                while j < len(gpio_times) and gpio_times[j] - t1 < 2.0:
                    # Check for second falling edge
                    if j > 0 and gpio_levels[j-1] == 1 and gpio_levels[j] == 0:
                        # This could be our second falling edge
                        # Check if there's a rising edge between i and j
                        has_rising_edge = False
                        for k in range(i+1, j):
                            if gpio_levels[k-1] == 0 and gpio_levels[k] == 1:
                                has_rising_edge = True
                                break
                                 
                        if has_rising_edge:
                            # Found a complete double-pulse pattern
                            t2 = gpio_times[j]
                            zero_crossing = (t1 + t2) / 2.0
                            zero_crossings.append(zero_crossing)
                            found_second_falling = True
                            i = j  # Skip ahead
                            break
                    j += 1
                    
                if not found_second_falling:
                    i += 1
            else:
                i += 1
                
        return zero_crossings

    def detect_current_zero_crossings(self, adc_times, adc_values, end_time=None):
        """
        Detect zero-crossings in the ADC current signal.
        If end_time is provided, only include zero-crossings up to this time.
        
        Args:
            adc_times: List of ADC timestamps
            adc_values: List of ADC voltage values
            end_time: Optional, only include zero-crossings up to this time
            
        Returns:
            List of zero-crossing timestamps in ms
        """
        if not adc_times or len(adc_times) < 2:
            return []
            
        zero_crossings = []
        
        # Find zero-crossings (where signal crosses 0V)
        for i in range(1, len(adc_values)):
            # Check if the signal crossed zero between these two points
            if (adc_values[i-1] < 0 and adc_values[i] >= 0) or (adc_values[i-1] >= 0 and adc_values[i] < 0):
                # Linear interpolation to find the exact zero-crossing time
                if adc_values[i] != adc_values[i-1]:  # Avoid division by zero
                    t_ratio = -adc_values[i-1] / (adc_values[i] - adc_values[i-1])
                    t_zero = adc_times[i-1] + t_ratio * (adc_times[i] - adc_times[i-1])
                    
                    # Only include if before end_time (if specified)
                    if end_time is None or t_zero <= end_time:
                        zero_crossings.append(t_zero)
        
        return zero_crossings

    def process_arc_analysis(self):
        """
        Process all arc analysis when GPIO events are detected.
        Updates the middle widget with the results.
        """
        if not self.gpio_time_data or not self.gpio_signal_data:
            return
            
        # Use binary data for analysis if available, otherwise convert display data
        if hasattr(self, 'gpio_binary_data') and len(self.gpio_binary_data) == len(self.gpio_time_data):
            gpio_levels = self.gpio_binary_data
        else:
            # Convert display levels to binary (0/1) for analysis
            gpio_levels = [1 if level > 0 else 0 for level in self.gpio_signal_data]
        
        # Get arc start time
        t_start = self.detect_arc_start_time(self.gpio_time_data, gpio_levels)
        
        # Get arc end time
        raw_end_time, pulse_pair_duration = self.detect_arc_end_time(self.gpio_time_data, gpio_levels)
        
        # Find voltage zero-crossings (GPIO) after the raw end time
        voltage_zero_crossings = self.find_zero_crossings(self.gpio_time_data, gpio_levels, raw_end_time)
        
        # Calculate the corrected end time
        t_end = None
        if raw_end_time is not None:
            if pulse_pair_duration is not None:
                t_end = raw_end_time - (pulse_pair_duration / 2.0)
            else:
                t_end = raw_end_time
        
        # Calculate arc duration
        t_arc = None
        if t_start is not None and raw_end_time is not None:
            # Original formula: raw_end_time - t_start - (pulse_pair_duration / 2.0)
            if pulse_pair_duration is not None:
                t_arc = raw_end_time - t_start - (pulse_pair_duration / 2.0)
            else:
                t_arc = raw_end_time - t_start
        
        # Find current zero-crossings from ADC data
        current_zero_crossings = []
        if self.adc_time_data and self.adc_signal_data:
            # Find the last GPIO pulse pair time if available
            last_pulse_time = None
            if voltage_zero_crossings:
                last_pulse_time = voltage_zero_crossings[-1]
            
            # Detect current zero-crossings up to the last pulse time
            current_zero_crossings = self.detect_current_zero_crossings(
                self.adc_time_data, 
                self.adc_signal_data,
                last_pulse_time
            )
            
        # Update the middle widget with the results
        self.update_arc_analysis_display(
            t_start, raw_end_time, t_end, t_arc, 
            pulse_pair_duration, voltage_zero_crossings, current_zero_crossings
        )

    def update_arc_analysis_display(self, t_start, raw_end_time, t_end, t_arc, pulse_pair_duration, voltage_zero_crossings, current_zero_crossings=None):
        """
        Update the middle widget with arc analysis results.
        """
        # Clear previous content
        self.system_info_widget.clear()
        
        # Add title with timestamp
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.system_info_widget.append(f"<h3>⚡ Arc Analysis Results ({current_time})</h3>")
        
        # Add system information section
        self.system_info_widget.append("<h4>System Information</h4>")
        if hasattr(self, 'frame_processor'):
            self.system_info_widget.append(f"<b>ADC Resolution:</b> {self.frame_processor.adc_resolution} bits")
            self.system_info_widget.append(f"<b>Reference Voltage:</b> {self.frame_processor.vref:.2f} V")
            self.system_info_widget.append(f"<b>Sampling Rate:</b> {self.frame_processor.sampling_rate_hz} Hz")
            self.system_info_widget.append(f"<b>Sample Period:</b> {self.frame_processor.sample_period*1000:.3f} ms")
        
        # Calculate and display signal information
        if self.adc_signal_data:
            signal_min = min(self.adc_signal_data)
            signal_max = max(self.adc_signal_data)
            signal_amplitude = signal_max - signal_min
            self.system_info_widget.append(f"<b>Current Signal Amplitude:</b> {signal_amplitude:.3f} V")
        
        # Add arc timing information section
        self.system_info_widget.append("<h4>Arc Timing Analysis</h4>")
        if t_start is not None:
            self.system_info_widget.append(f"<b>Arc Start Time:</b> {t_start:.3f} ms")
        else:
            self.system_info_widget.append("<b>Arc Start Time:</b> Not detected")
            
        if raw_end_time is not None:
            self.system_info_widget.append(f"<b>Raw End Time:</b> {raw_end_time:.3f} ms")
        else:
            self.system_info_widget.append("<b>Raw End Time:</b> Not detected")
            
        if pulse_pair_duration is not None:
            self.system_info_widget.append(f"<b>Pulse Pair Duration:</b> {pulse_pair_duration:.3f} ms")
            
        if t_end is not None:
            self.system_info_widget.append(f"<b>Corrected End Time:</b> {t_end:.3f} ms")
        else:
            self.system_info_widget.append("<b>Corrected End Time:</b> Not detected")
            
        if t_arc is not None:
            self.system_info_widget.append(f"<b>Arc Duration:</b> {t_arc:.3f} ms")
        else:
            self.system_info_widget.append("<b>Arc Duration:</b> Not detected")
        
        # Add voltage zero-crossing information
        self.system_info_widget.append("<h4>Voltage Zero-Crossings</h4>")
        self.system_info_widget.append(f"<b>Number of Voltage Zero-Crossings:</b> {len(voltage_zero_crossings)}")
        if voltage_zero_crossings:
            self.system_info_widget.append("<b>Voltage Zero-Crossing Timestamps (ms):</b>")
            for i, zc in enumerate(voltage_zero_crossings[:10]):  # Show first 10 only to avoid cluttering
                self.system_info_widget.append(f"  {i+1}. {zc:.3f}")
            if len(voltage_zero_crossings) > 10:
                self.system_info_widget.append(f"  ... and {len(voltage_zero_crossings) - 10} more")
        
        # Add current zero-crossing information
        if current_zero_crossings is not None:
            self.system_info_widget.append("<h4>Current Zero-Crossings</h4>")
            self.system_info_widget.append(f"<b>Number of Current Zero-Crossings:</b> {len(current_zero_crossings)}")
            if current_zero_crossings:
                self.system_info_widget.append("<b>Current Zero-Crossing Timestamps (ms):</b>")
                for i, zc in enumerate(current_zero_crossings[:10]):  # Show first 10 only
                    self.system_info_widget.append(f"  {i+1}. {zc:.3f}")
                if len(current_zero_crossings) > 10:
                    self.system_info_widget.append(f"  ... and {len(current_zero_crossings) - 10} more")

    def handle_gpio_data(self, data):
        # Initialize with safe defaults if no previous data exists
        timestamps = [self.gpio_time_data[-1]] if self.gpio_time_data else [0.0]
        display_levels = [self.gpio_signal_data[-1]] if self.gpio_signal_data else [0.0]
        binary_levels = [1 if display_levels[0] > 0 else 0]  # Binary version for analysis
        
        for i in range(0, len(data), 5):
            ts_ms = int.from_bytes(data[i : i + 4], byteorder="little") * 2 / 1000.0
            if ts_ms == 0:
                continue

            # Get the binary level (0 or 1)
            is_high = bool(data[i + 4])
            
            # For display: use 0 for LOW and 1.0 for HIGH (better visibility than 0.5)
            display_level = 0 if not is_high else 1.0
            
            # For analysis: use binary 0/1
            binary_level = 0 if not is_high else 1

            # Draw a vertical edge only if level changed (for display)
            if display_levels[-1] != display_level:
                timestamps.append(ts_ms)
                display_levels.append(display_levels[-1])  # Previous level
                binary_levels.append(binary_levels[-1])    # Previous binary level
                
            # Add the new point
            timestamps.append(ts_ms)
            display_levels.append(display_level)
            binary_levels.append(binary_level)

        # Skip the first point which was just for continuity
        return timestamps[1:], display_levels[1:], binary_levels[1:]


    def closeEvent(self, event):
        # Stop the serial reader first
        if self.serial_reader:
            self.serial_reader.stop()

        # Save GPIO data arrays if available
        try:
            if self.gpio_time_data and self.gpio_signal_data:
                # Create a timestamp for the filename
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"adc_data_{timestamp}.csv"

                # Save data as CSV file with time,value pairs
                with open(filename, "w") as f:
                    f.write("Time_ms,Signal_Level\n")  # Header
                    for t, v in zip(self.adc_time_data, self.adc_signal_data):
                        f.write(f"{t:.6f},{v:.6f}\n")
                print(f"[INFO] ADC data saved to {filename}")
        except Exception as e:
            print(f"[ERROR] Failed to save ADC data: {str(e)}")

        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LivePlotter()
    win.show()
    sys.exit(app.exec_())
