import pandas as pd
import matplotlib.pyplot as plt

# Reload the file after code execution state reset
adc_file_path = "../adc_data_20250417_152029.csv"
adc_df = pd.read_csv(adc_file_path)

# Get only the first 100 samples
adc_df_100 = adc_df.iloc[:100]

plt.figure(figsize=(12, 4))
plt.plot(adc_df_100["Time_ms"], adc_df_100["Signal_Level"], color="blue")
plt.xlabel("Time (ms)")
plt.ylabel("Voltage (V)")
plt.title("First 100 ADC Signal Samples")
plt.grid(True)
plt.tight_layout()
plt.show()
