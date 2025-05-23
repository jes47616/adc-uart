#include "config.h"

// ADC global variables
uint16_t adcBuffer[ADC_BUFFER_SIZE];
volatile uint8_t adcReadyToSend = 0;

// UART global variables
volatile TriggerMode_t current_mode = ADC_CONTINUOUS_MODE;
uint8_t uart_rx_buffer[CMD_STR_LEN];
uint8_t uartTxCompleteFlag = 1;

uint8_t burstBuffer[BURST_BUFFER_SIZE];
uint8_t burstIndex = 0;


uint8_t adc_ring_buffer_raw[RING_BUFFER_SIZE];
ring_buffer_t adc_ring_buffer;
uint8_t gpio_ring_buffer_raw[RING_BUFFER_SIZE];
ring_buffer_t gpio_ring_buffer;

uint32_t times[5000] = {0};
uint16_t times_index = 0;