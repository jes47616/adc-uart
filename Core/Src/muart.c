#include "muart.h"

#ifdef TEST_UART

// Function to start UART test
void UART_Test_Start(void)
{
    uint8_t msg[] = "\n";
    UART_Transmit(msg, 1); // Start transmission on the active UART
}

#endif


void send_start_time(void)
{
    uint8_t packet[21];  // Create a 21-byte packet
    
    // Set the start header (0xC0)
    packet[0] = 0xC0;
    
    // Get the TIM2 count value (using HAL)
    uint32_t tim2_count = __HAL_TIM_GetCounter(&htim2);
    
    // Fill the next 4 bytes with the TIM2 count (little-endian format)
    packet[1] = (uint8_t)(tim2_count & 0xFF);  // Least significant byte
    packet[2] = (uint8_t)((tim2_count >> 8) & 0xFF);
    packet[3] = (uint8_t)((tim2_count >> 16) & 0xFF);
    packet[4] = (uint8_t)((tim2_count >> 24) & 0xFF);  // Most significant byte
    
    // Fill the rest of the packet with 0x00 or any value you'd like
    for (int i = 5; i < 21; i++) {
        packet[i] = 0xFF;  // Padding bytes (could also use any other value)
    }
    
    // Transmit the 21-byte packet via UART
    HAL_UART_Transmit_DMA(ACTIVE_UART, packet, 21);

    int a = 0;
    // handle_transmitt();
}
