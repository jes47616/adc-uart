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
from PyQt5.QtWidgets import QListWidget, QListWidgetItem


# Define the command constants
START_CMD = "START____"
STOP_CMD = "STOP_____"
TRGMODE_CMD = "TRGMODE__"
INTMODE_CMD = "INTMODE__"
RESET_CMD = "RESET____"


class LivePlotter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time ADC/GPIO Plot")
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
        self.reset_btn = QPushButton("Reset")

        self.start_btn.clicked.connect(self.start_plotting)
        self.stop_btn.clicked.connect(self.stop_plotting)
        self.trgmode_btn.clicked.connect(lambda: self.send_command(TRGMODE_CMD))
        self.intmode_btn.clicked.connect(lambda: self.send_command(INTMODE_CMD))
        # self.reset_btn.clicked.connect(lambda: self.send_command(RESET_CMD))
        self.reset_btn.clicked.connect(self.reset_plotting)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.port_selector)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.trgmode_btn)
        btn_layout.addWidget(self.intmode_btn)
        btn_layout.addWidget(self.reset_btn)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(100)

        # --- Final Layout ---
        self.zero_crossing_results_list = QListWidget()
        self.zero_crossing_results_list.setMinimumHeight(150)

        self.phase_angle_results_list = QListWidget()
        self.phase_angle_results_list.setMinimumHeight(150)

        self.log_output_results_layout = QHBoxLayout()
        self.log_output_results_layout.addWidget(self.log_output)
        self.log_output_results_layout.addWidget(self.zero_crossing_results_list)
        self.log_output_results_layout.addWidget(self.phase_angle_results_list)

        layout = QVBoxLayout()
        layout.addLayout(btn_layout)
        layout.addWidget(self.plot_widget)
        layout.addLayout(self.log_output_results_layout)

        self.setLayout(layout)
        self.set_controls_enabled(True)

    def clear_plot(self):
        self.adc_time_data.clear()
        self.adc_signal_data.clear()
        self.gpio_time_data.clear()
        self.gpio_signal_data.clear()
        self.adc_curve.setData([], [])
        self.gpio_curve.setData([], [])
        self.start_time_us = None

    def start_plotting(self):
        if not self.is_running:
            self.is_running = True
            self.set_controls_enabled(False)  # Disable other controls
            self.clear_plot()
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
            self.process_analysis()

    def reset_plotting(self):
        if self.is_running:
            self.is_running = False
            self.set_controls_enabled(True)  # Re-enable other controls
            print("[INFO] Plotting stopped.")
            self.send_command(RESET_CMD)
            self.reset_log_output()
            self.clear_plot()
            self.zero_crossing_results_list.clear()
            self.phase_angle_results_list.clear()
        else:
            print("[INFO] Plotting is not running.")
            self.reset_log_output()
            self.clear_plot()

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

    def reset_log_output(self):
        self.log_output.clear()

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
                    # print("Adding ADC data to plot")
                    self.adc_curve.setData(self.adc_time_data, self.adc_signal_data)
                else:
                    print("No ADC data found")
                    return

        elif header == 0xB0 and self.start_time_us is not None:
            # print(f"[DEBUG] GPIO packet received! Data length: {len(data)} bytes")
            # print(f"[DEBUG] Raw GPIO data: {' '.join([f'{b:02X}' for b in data])}")

            if len(data) % 5 == 0:  # GPIO event format (timestamp + level)
                new_time_data, new_signal_data = self.handle_gpio_data(data)
                self.gpio_time_data.extend(new_time_data)
                self.gpio_signal_data.extend(new_signal_data)
                # print("Adding GPIO data to plot")
                self.gpio_curve.setData(self.gpio_time_data, self.gpio_signal_data)
            else:
                print(f"Invalid GPIO data size: {len(data)} bytes")
                return

    def handle_gpio_data(self, data):
        # keep last known point so the first transition is drawn correctly
        timestamps = [self.gpio_time_data[-1]]
        levels = [self.gpio_signal_data[-1]]

        for i in range(0, len(data), 5):
            ts_ms = (int.from_bytes(data[i : i + 4], byteorder="little") * 2) / 1000.0
            if ts_ms == 0:
                continue

            level = 0 if not data[i + 4] else 1  # already 0 or 1

            # draw a vertical edge only if level changed
            if levels[-1] != level:
                timestamps.append(ts_ms)
                levels.append(levels[-1])  # drop to previous level first
            timestamps.append(ts_ms)
            levels.append(level)  # then new level

        return timestamps[1:], levels[1:]

    def find_zero_crossings(self, time_data, signal_data, gpio_last_midpoint):
        zero_crossings = []
        for i in range(1, len(signal_data)):
            if time_data[i] > gpio_last_midpoint + 20:
                break
            if (signal_data[i - 1] < 0 and signal_data[i] >= 0) or (
                signal_data[i - 1] >= 0 and signal_data[i] < 0
            ):
                t1, v1 = time_data[i - 1], signal_data[i - 1]
                t2, v2 = time_data[i], signal_data[i]
                if v2 != v1:
                    t_zero = t1 + (0 - v1) * (t2 - t1) / (v2 - v1)
                    zero_crossings.append(t_zero)
        return zero_crossings

    def find_gpio_zero_midpoints(self, time_data, signal_data, arc_end_time):
        raw_midpoints = []
        pulse_rises = []
        pulse_falls = []

        pulse_start = None

        # Step 1: Detect all single pulse midpoints
        for i in range(1, len(signal_data)):
            if time_data[i] < arc_end_time:
                continue
            if signal_data[i - 1] == 0 and signal_data[i] == 1:
                pulse_start = time_data[i]
                pulse_rises.append(pulse_start)
            elif (
                signal_data[i - 1] == 1
                and signal_data[i] == 0
                and pulse_start is not None
            ):
                pulse_end = time_data[i]
                raw_midpoints.append((pulse_start + pulse_end) / 2)
                pulse_falls.append(pulse_end)
                pulse_start = None

        # Step 2: Pair up midpoints and calculate center of pair
        pair_midpoints = []
        first_half_duration = None

        for i in range(0, len(raw_midpoints) - 1, 2):
            mid = (raw_midpoints[i] + raw_midpoints[i + 1]) / 2
            pair_midpoints.append(mid)

            # Calculate half duration of first pulse pair only
            if i == 0 and len(pulse_rises) >= 1 and len(pulse_falls) >= 2:
                t_rise1 = pulse_rises[-2]
                t_fall2 = pulse_falls[-1]
                first_half_duration = (t_fall2 - t_rise1) / 2

        return pair_midpoints, first_half_duration

    def detect_arc_duration(self, time_data, signal_data):
        arc_start = None
        arc_end = None
        arc_min_duration_ms = 0.05
        off_threshold_ms = 5.0

        for i in range(1, len(signal_data)):
            if signal_data[i - 1] == 0 and signal_data[i] == 1:
                t_high_start = time_data[i]
            elif signal_data[i - 1] == 1 and signal_data[i] == 0:
                t_high_end = time_data[i]
                if (t_high_end - t_high_start) >= arc_min_duration_ms:
                    arc_start = t_high_start
                    break

        for i in range(len(signal_data)):
            if arc_start is not None and signal_data[i] == 0:
                t_low_start = time_data[i]
                j = i
                while j < len(signal_data) and signal_data[j] == 0:
                    j += 1
                if (
                    j < len(signal_data)
                    and (time_data[j - 1] - t_low_start) >= off_threshold_ms
                ):
                    arc_end = t_low_start
                    break

        return arc_start, arc_end

    def berechne_phasenwinkel(self, strom_zero, spannung_zero, periode_ms=20.0):
        delta_t = spannung_zero - strom_zero  # in ms
        phi = (delta_t / periode_ms) * 360.0  # in degrees
        return phi

    def berechne_mehrere_phasenwinkel(self, strom_zeros, spannung_zeros, periode_ms=20.0):
        phasenwinkel = []
        # Pair each voltage zero with the NEXT adc zero (skip first adc zero)
        n = min(len(spannung_zeros), len(strom_zeros) - 1)
        for i in range(n):
            sz = strom_zeros[i+1]  # skip first adc zero
            vz = spannung_zeros[i]
            phi = self.berechne_phasenwinkel(sz, vz, periode_ms)
            phasenwinkel.append((sz, vz, phi))
        return phasenwinkel

    def berechne_adc_frequenz(self, adc_zeros):
        if len(adc_zeros) < 3:
            return None
        periods = [adc_zeros[i+2] - adc_zeros[i] for i in range(len(adc_zeros)-2)]
        mean_period = sum(periods) / len(periods)
        frequency = 1000.0 / mean_period  # ms to Hz
        return frequency

    def berechne_adc_amplitude(self, adc_signal_data):
        if not adc_signal_data:
            return None
        amplitude = (max(adc_signal_data) - min(adc_signal_data)) / 2.0
        return amplitude

    def process_analysis(self):
        arc_start, arc_end = self.detect_arc_duration(
            self.gpio_time_data, self.gpio_signal_data
        )
        gpio_midpoints, gpio_first_half_duration = self.find_gpio_zero_midpoints(
            self.gpio_time_data, self.gpio_signal_data, arc_end
        )

        adc_zeros = self.find_zero_crossings(
            self.adc_time_data, self.adc_signal_data, gpio_midpoints[-1]
        )
        duration = (
            arc_end - arc_start - gpio_first_half_duration
            if arc_start and arc_end
            else None
        )

        # --- Frequency and amplitude calculation ---
        adc_freq = self.berechne_adc_frequenz(adc_zeros)
        adc_amp = self.berechne_adc_amplitude(self.adc_signal_data)

        # --- Zero-Crossing & Arc Analysis Widget (Middle) ---
        self.zero_crossing_results_list.clear()
        self.zero_crossing_results_list.addItem("🟦 System Overview & Events")
        self.zero_crossing_results_list.addItem("")
        # Section 1: System Info
        self.zero_crossing_results_list.addItem("🖥️ AD-Converter")
        self.zero_crossing_results_list.addItem("  🕒 Sampling Rate: 10 kHz")  # Adjust as needed
        self.zero_crossing_results_list.addItem("  📏 Resolution: 12-bit, ±1.65V")
        self.zero_crossing_results_list.addItem("")
        # Section 2: Signal Metrics
        self.zero_crossing_results_list.addItem("⚡ Current Signal (ADC)")
        self.zero_crossing_results_list.addItem(f"  🔉 Amplitude: {adc_amp:.2f} V, Rogowski-Coil [100mV/kA]" if adc_amp else "  🔉 Amplitude: n/a")
        self.zero_crossing_results_list.addItem(f"  🧭 Frequency: {adc_freq:.2f} Hz" if adc_freq else "  🧭 Frequency: n/a")
        self.zero_crossing_results_list.addItem("")
        # Section 3: Zero-Crossings
        self.zero_crossing_results_list.addItem("🔄 Current Zero-Crossings")
        for t in adc_zeros:
            self.zero_crossing_results_list.addItem(f"  • {t:.3f} ms")
        self.zero_crossing_results_list.addItem("")
        self.zero_crossing_results_list.addItem("🔆 Voltage Zero-Crossings (LED Midpoints)")
        for t in gpio_midpoints:
            self.zero_crossing_results_list.addItem(f"  • {t:.3f} ms")
        self.zero_crossing_results_list.addItem("")
        # Section 4: Arc Event
        self.zero_crossing_results_list.addItem("🔥 Arc Event")
        self.zero_crossing_results_list.addItem(f"  🟢 Start: {arc_start:.3f} ms" if arc_start else "  🟢 Start: n/a")
        arc_end_corrected = arc_end - gpio_first_half_duration if arc_end and gpio_first_half_duration else None
        self.zero_crossing_results_list.addItem(f"  🔴 End: {arc_end_corrected:.3f} ms" if arc_end_corrected else "  🔴 End: n/a")
        self.zero_crossing_results_list.addItem(f"  ⏱️ Duration: {duration:.3f} ms" if duration else "  ⏱️ Duration: n/a")

        # --- Phase Angle Calculation Widget (Right) ---
        # Only consider pulse pairs after arc duration
        gpio_midpoints_after_arc = [t for t in gpio_midpoints if t > arc_end]
        phasenwinkel_liste = self.berechne_mehrere_phasenwinkel(adc_zeros, gpio_midpoints_after_arc, 20.0)
        self.phase_angle_results_list.clear()
        self.phase_angle_results_list.addItem("🟩 Phase Analysis & Insights")
        self.phase_angle_results_list.addItem("")
        # Section 1: Phase Angle Calculation
        self.phase_angle_results_list.addItem("🧮 Phase Angle Calculation")
        for sz, vz, phi in phasenwinkel_liste:
            self.phase_angle_results_list.addItem(
                f"  • Current @ {sz:.3f} ms \u2194 Voltage @ {vz:.3f} ms \u21D2 \u03A6 = {phi:+.1f}\u00B0"
            )
        self.phase_angle_results_list.addItem("")
        # Section 2: Summary/Insights
        if phasenwinkel_liste:
            angles = [phi for _, _, phi in phasenwinkel_liste]
            mean_phi = sum(angles) / len(angles)
            min_phi = min(angles)
            max_phi = max(angles)
            self.phase_angle_results_list.addItem(f"📊 Mean Phase Angle: {mean_phi:+.1f}\u00B0")
            self.phase_angle_results_list.addItem(f"📉 Min: {min_phi:+.1f}\u00B0, 📈 Max: {max_phi:+.1f}\u00B0")
            self.phase_angle_results_list.addItem(f"🏷️ Pairs Analyzed: {len(angles)}")
        else:
            self.phase_angle_results_list.addItem("No phase angles calculated.")
        self.phase_angle_results_list.addItem("")
        # Section 3: Legend
        self.phase_angle_results_list.addItem("ℹ️ Legend:")
        self.phase_angle_results_list.addItem("  ⚡: Current, 🔆: Voltage, 🔄: Zero-Crossing, 🔥: Arc, 🧮: Phase, ⏱️: Duration")

    def closeEvent(self, event):
        # Stop the serial reader first
        if self.serial_reader:
            self.serial_reader.stop()

        event.accept()


def main():
    app = QApplication(sys.argv)
    win = LivePlotter()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
