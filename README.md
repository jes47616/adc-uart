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
   - Uses DMA for efficient data transfer
   - 12-bit resolution with samples stored in 2 bytes
   - Ring buffer implementation (1024 bytes) for efficient operations

2. **GPIO Monitoring**
   - PA1 configured as external interrupt on rising edge
   - Precise timestamping of GPIO events using TIM2
   - GPIO state changes stored with 4-byte timestamps

3. **Data Transmission**
   - UART transmission in interrupt mode
   - Frame format with header (0xAA55) and footer (0x55AA)
   - 400 bytes of ADC data (200 samples) per frame
   - Support for both debug and data UART interfaces

### Python GUI Application
The Python application provides:

1. **Serial Communication**
   - Automatic COM port detection
   - Support for both endianness formats
   - Frame validation and statistics reporting

2. **Data Visualization**
   - Real-time plotting of ADC data
   - GPIO event visualization
   - Signal analysis capabilities

## Getting Started

### Prerequisites
- STM32 development board (STM32G4 series)
- Python 3.6+ with required packages (see `py/requirements.txt`)

### Installation
1. Flash the STM32 firmware using ST-Link and your preferred IDE
2. Install Python dependencies:
   ```
   cd py
   pip install -r requirements.txt
   ```

### Running the Application
1. Connect the STM32 board to your computer
2. Run the Python application:
   ```
   cd py
   python main.py
   ```

## Operation Modes
- **Interrupt Mode**: GPIO events trigger data acquisition
- **Timer Mode**: Continuous sampling at 10kHz

## Troubleshooting
- If DMA transfers fail, check the system's debug output for detailed state information
- For communication issues, verify the correct COM port is selected