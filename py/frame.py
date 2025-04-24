import numpy as np


class FrameProcessor:
    def __init__(self, adc_resolution=12, vref=3.3, sampling_rate_hz=2500):
        self.adc_resolution = adc_resolution
        self.vref = vref
        self.sampling_rate_hz = sampling_rate_hz
        self.sample_period = 1.0 / sampling_rate_hz  # 0.0002s (200μs)
        print(
            f"Sampling rate: {sampling_rate_hz} Hz, Sample period: {self.sample_period}s"
        )

    def parse_frame(self, packet_bytes):
        """
        Convert raw ADC frame bytes to a list of voltage values.
        Assumes little-endian 16-bit samples.
        """
        voltages = []
        for i in range(0, len(packet_bytes), 2):
            raw = int.from_bytes(packet_bytes[i : i + 2], byteorder="little")
            voltage = (raw / (2**self.adc_resolution - 1)) * self.vref
            voltages.append(voltage - 1.65)
        return np.array(voltages)

    def generate_time_axis(self, num_samples):
        """Generate time axis in seconds based on sampling rate"""
        # print(f"Generating time axis for {num_samples} samples")
        return np.linspace(
            0, num_samples * self.sample_period, num_samples, endpoint=False
        )
