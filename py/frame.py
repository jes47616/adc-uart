import numpy as np

class FrameProcessor:
    def __init__(self, adc_resolution=12, vref=3.3, sample_rate_ms=1):
        self.adc_resolution = adc_resolution
        self.vref = vref
        self.sample_rate_ms = sample_rate_ms

    def parse_frame(self, packet_bytes):
        """
        Convert raw ADC frame bytes to a list of voltage values.
        Assumes little-endian 16-bit samples.
        """
        voltages = []
        for i in range(0, len(packet_bytes), 2):
            raw = int.from_bytes(packet_bytes[i:i+2], byteorder='little')
            voltage = (raw / (2**self.adc_resolution - 1)) * self.vref
            voltages.append(voltage)
        return np.array(voltages)

    def generate_time_axis(self, num_samples):
        return np.array([i * self.sample_rate_ms for i in range(num_samples)])