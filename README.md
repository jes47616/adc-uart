# ADC-UART Data Acquisition System

## Project Overview
This project implements a high-performance data acquisition system using an STM32 microcontroller, featuring:
- 10kHz ADC sampling of analog signals
- GPIO event detection with precise timestamping
- UART communication for data transmission to a PC
- Real-time visualization with a PyQt-based GUI

## System Architecture

### STM32 Firmware
The STM32 microcontroller firmware handles:

1. **ADC Sampling**
   - 10kHz sampling rate for 3.3V amplitude signals
   - Uses DMA for efficient data transfer without CPU intervention
   - 12-bit resolution with samples stored in 2 bytes
   - Ring buffer implementation (1024 bytes) for efficient operations
   - Supports both continuous (timer-triggered) and event-triggered sampling modes

2. **GPIO Monitoring**
   - PA1 configured as external interrupt on rising edge
   - Precise timestamping of GPIO events using TIM2
   - GPIO state changes stored with 4-byte timestamps
   - Supports interrupt-driven event detection

3. **Data Transmission**
   - UART transmission in interrupt mode with DMA support
   - Frame format with header (0xAA55) and footer (0x55AA)
   - 400 bytes of ADC data (200 samples) per frame
   - Support for both debug and data UART interfaces
   - Packet-based communication protocol with different packet types:
     - 0xA0: ADC data packets
     - 0xB0: GPIO event packets
     - 0xC0: Timestamp synchronization packets
     - 0xD0: Status/debug packets

4. **DMA Management**
   - Efficient DMA transfers for both ADC data acquisition and UART transmission
   - Error handling and state monitoring for reliable operation
   - Automatic recovery from DMA transfer failures

### Python GUI Application
The Python application provides:

1. **Serial Communication**
   - Automatic COM port detection and selection
   - Support for both endianness formats
   - Frame validation and statistics reporting
   - Packet processing with header-based protocol identification

2. **Data Visualization**
   - Real-time plotting of ADC data using PyQtGraph
   - GPIO event visualization with timestamp correlation
   - Signal analysis capabilities
   - Adjustable time axis and voltage scaling

3. **User Interface**
   - Intuitive controls for starting/stopping data acquisition
   - Mode selection (Continuous vs. Interrupt)
   - Serial port selection and connection management
   - Debug logging with packet inspection capabilities

## Hardware Requirements
- STM32G4 series microcontroller (STM32G431K8 recommended)
- USB-to-UART converter for PC communication
- Analog signal source for ADC input (0-3.3V range)
- Digital signal source for GPIO event triggering
- Power supply (USB or external 3.3V)

## Software Requirements
- STM32CubeIDE for firmware development and flashing
- Python 3.6+ with the following packages:
  - PyQt5 for the GUI framework
  - PyQtGraph for real-time plotting
  - NumPy for data processing
  - pySerial for serial communication

## Getting Started

### Prerequisites
- STM32 development board (STM32G4 series)
- Python 3.6+ with required packages (see `py/requirements.txt`)
- STM32CubeIDE or similar for firmware compilation and flashing

### Firmware Installation
1. Clone this repository
2. Open the project in STM32CubeIDE
3. Configure the project for your specific STM32 board if needed
4. Build and flash the firmware to your STM32 device

### Python Application Setup
1. Install Python dependencies:
   ```
   cd py
   pip install -r requirements.txt
   ```

### Running the Application
1. Connect the STM32 board to your computer via USB-to-UART
2. Run the Python application:
   ```
   cd py
   python main.py
   ```
3. Select the appropriate COM port from the dropdown menu
4. Choose the desired operation mode (Continuous or Interrupt)
5. Click "Start" to begin data acquisition and visualization

## Operation Modes

### Continuous Mode (Timer-Triggered)
- ADC samples are taken at a fixed rate of 10kHz
- Timer3 is used to trigger ADC conversions
- Data is continuously transmitted when 200 samples are collected
- Ideal for periodic signal monitoring and analysis

### Interrupt Mode (Event-Triggered)
- ADC sampling begins when a rising edge is detected on PA1
- Precise timestamping of the trigger event
- Sampling continues until the specified number of samples is collected
- Ideal for capturing transient events and analyzing signals in response to external triggers

## Data Protocol
- Each UART packet is 21 bytes:
  - 1 byte header (0xA0, 0xB0, 0xC0, or 0xD0)
  - 20 bytes of payload data
- ADC data is transmitted in frames of 200 samples (400 bytes)
- Each ADC sample is 12-bit resolution stored in 2 bytes
- GPIO events include a 4-byte timestamp for precise timing analysis

## Troubleshooting

### DMA Issues
- If DMA transfers fail, check the system's debug output for detailed state information
- Verify that DMA channels are properly configured and not conflicting
- Check the `IsDMABusy()` function output to diagnose transfer problems

### Communication Issues
- Verify the correct COM port is selected
- Ensure the baud rate is set to 115200 with EVEN parity
- Check that the STM32 is properly powered and programmed
- Inspect the UART configuration on both the STM32 and PC sides

### ADC Sampling Issues
- Verify the input signal is within the 0-3.3V range
- Check ADC channel configuration and pin connections
- Ensure the sampling rate is appropriate for your signal frequency
- Verify the ring buffer is not overflowing during operation

## Advanced Configuration
- Edit `config.h` to modify system parameters:
  - ADC sampling rate
  - UART baud rate
  - Buffer sizes
  - Debug mode settings
- Modify `py/main.py` to adjust visualization parameters:
  - Plot ranges
  - Update rates
  - Display options

## Performance Considerations
- The system can reliably sample at 10kHz with 12-bit resolution
- DMA transfers minimize CPU overhead during data acquisition
- Ring buffer implementation prevents data loss during processing
- The Python application is optimized for real-time visualization with minimal latency

## License
This project is open-source and available under the MIT License.

## Acknowledgments
- STM32 HAL library for hardware abstraction
- PyQt and PyQtGraph for the visualization framework
- Contributors and testers who helped improve the system