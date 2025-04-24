import matplotlib.pyplot as plt
import numpy as np


def parse_and_plot_uart_packets(
    data_str, adc_resolution=12, vref=3.3, sample_interval_ms=0.2
):
    lines = data_str.strip().splitlines()
    voltages = []

    for line in lines:
        hex_strs = line.strip().split()
        if not hex_strs or hex_strs[0] != "A0":
            continue  # skip if no A0 header
        hex_strs = hex_strs[1:]  # remove header

        # Convert to bytearray
        try:
            packet_bytes = bytearray(int(h, 16) for h in hex_strs)
        except ValueError:
            continue  # skip invalid lines

        # Convert each 2 bytes (little endian) to ADC voltage
        for i in range(0, len(packet_bytes), 2):
            if i + 1 >= len(packet_bytes):
                break  # skip incomplete pair
            raw = int.from_bytes(packet_bytes[i : i + 2], byteorder="little")
            voltage = (raw / (2**adc_resolution - 1)) * vref
            voltages.append(voltage)

    # Time axis
    time = np.arange(0, len(voltages)) * sample_interval_ms  # in ms

    # Plot
    plt.plot(time, voltages)
    plt.xlabel("Time (ms)")
    plt.ylabel("Voltage (V)")
    plt.title("ADC Voltage vs Time")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


with open("py/adc_hex_data.txt", "r") as f:
    data_str = f.read()
    parse_and_plot_uart_packets(data_str)
