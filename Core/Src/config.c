#include "config.h"

// ADC global variables
uint16_t adcBuffer[ADC_BUFFER_SIZE];
volatile uint8_t adcReadyToSend = 0;

// UART global variables
volatile TriggerMode_t current_mode = ADC_TRIGGER_MODE;
uint8_t uart_rx_buffer[CMD_STR_LEN];
uint8_t uartTxCompleteFlag = 1;

uint8_t burstBuffer[BURST_BUFFER_SIZE];
uint8_t burstIndex = 0;

