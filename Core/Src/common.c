#include "common.h"
#include "uart.h"
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






