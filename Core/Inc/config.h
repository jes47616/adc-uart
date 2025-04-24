#ifndef __CONFIG_H__
#define __CONFIG_H__

#include "main.h"
#include "ringbuffer.h"

// Debug mode flag
#define DEBUG_MODE 1

#if DEBUG_MODE
    #define ACTIVE_UART &huart2

    //#define TEST_TIMER
    #define TEST_UART 
    #define TEST_ADC  

#else
    #define ACTIVE_UART &huart1
#endif


// CubeMX-generated peripheral handles
extern ADC_HandleTypeDef hadc1;
extern DMA_HandleTypeDef hdma_adc1;

extern TIM_HandleTypeDef htim2;
extern TIM_HandleTypeDef htim3;

extern UART_HandleTypeDef huart1;
extern UART_HandleTypeDef huart2;
extern DMA_HandleTypeDef hdma_usart1_tx;
extern DMA_HandleTypeDef hdma_usart2_tx;

// ADC Configuration
#define ADC_BUFFER_SIZE 1000 //war 10
extern uint16_t adcBuffer[ADC_BUFFER_SIZE];
extern volatile uint8_t adcReadyToSend;

// UART Configuration
#define CMD_STR_LEN 9
typedef enum {
    ADC_CONTINUOUS_MODE,
    ADC_INTERRUPT_MODE
} TriggerMode_t;

extern volatile TriggerMode_t current_mode;
extern uint8_t uart_rx_buffer[CMD_STR_LEN];
extern uint8_t uartTxCompleteFlag;

// Command strings
#define START____ "START____"
#define STOP_____ "STOP_____"
#define TRGMODE__ "TRGMODE__"
#define INTMODE__ "INTMODE__"
#define RESET____ "RESET____"

// GPIO Burst Settings
#define BURST_BUFFER_SIZE 5
extern uint8_t burstBuffer[BURST_BUFFER_SIZE];



// Ring Buffers

#define RING_BUFFER_SIZE 10000
extern uint8_t adc_ring_buffer_raw[RING_BUFFER_SIZE];
extern ring_buffer_t adc_ring_buffer;
extern uint8_t gpio_ring_buffer_raw[RING_BUFFER_SIZE];
extern ring_buffer_t gpio_ring_buffer;

extern uint16_t times_index;
extern uint32_t times[5000];




#endif // __CONFIG_H__
