#include "common.h"
#include "muart.h"
#include "madc.h"



void UART_Transmit(uint8_t *data, uint16_t size) {
    uartTxCompleteFlag = 0;  // Reset the flag before starting transmission

    // Start UART transmission via DMA
    HAL_UART_Transmit_DMA(ACTIVE_UART, data, size);
}


// Print function (always uses UART1)
void Print(const char *msg) {
    // Wait until UART TX via DMA is complete (check global flag)
    while (!uartTxCompleteFlag) {
        // Optionally, you can add a timeout here if needed
        // E.g., check if a timeout occurs and break the loop
    }
    // Once transmission is complete, send the message via DMA
    uartTxCompleteFlag = 0;
    HAL_UART_Transmit_DMA(&huart2, (uint8_t *)msg, strlen(msg));
}


void init_ring_buffers(void){
    ring_buffer_init(&adc_ring_buffer,adc_ring_buffer_raw,RING_BUFFER_SIZE);
    ring_buffer_init(&gpio_ring_buffer,gpio_ring_buffer_raw,RING_BUFFER_SIZE);
}



void deinit_ring_buffers(void) {
    // Clear the raw buffer contents to zero
    memset(adc_ring_buffer_raw, 0, RING_BUFFER_SIZE);
    memset(gpio_ring_buffer_raw, 0, RING_BUFFER_SIZE);

    // Reset the ring buffer structures (head, tail, count)
    ring_buffer_clear(&adc_ring_buffer);
    ring_buffer_clear(&gpio_ring_buffer);

    // Optionally, set the raw buffer pointers to NULL (if dynamically allocated)
    // In your case, since they are statically allocated, this isn't necessary
    adc_ring_buffer.buffer = NULL;
    gpio_ring_buffer.buffer = NULL;
}

void ring_buffer_clear(ring_buffer_t *buffer) {
    // Reset the ring buffer pointers and count
    buffer->head = 0;
    buffer->tail = 0;
    buffer->count = 0;
    // If you track buffer size, you can reset it here
    buffer->size = 0;  // Optional, depends on your design
}



