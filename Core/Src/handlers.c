
#include "handlers.h"
void handle_start_system(void)
{   
	handle_reset_system();
    if(current_mode == ADC_TRIGGER_MODE){
        ADC_Start();
        Timer3_Start(&htim3);
    }
}


void handle_stop_system(void)
{
    // Stop ADC DMA if it's currently running
    if (HAL_ADC_GetState(&hadc1) & HAL_ADC_STATE_REG_BUSY)
    {
        HAL_ADC_Stop_DMA(&hadc1);
    }

    // Stop Timer 2 if it's running
    if (HAL_TIM_Base_GetState(&htim2) != HAL_TIM_STATE_READY)
    {
        HAL_TIM_Base_Stop(&htim2);
    }

    // Stop Timer 3 if it's running (optional)
    if (HAL_TIM_Base_GetState(&htim3) != HAL_TIM_STATE_READY)
    {
        HAL_TIM_Base_Stop(&htim3);
    }

    // Optionally clear buffers, disable watchdogs, etc.
}


void handle_reset_system(void)
{
    handle_stop_system();
    // Clear flags, buffers, state variables if needed
    memset(adcBuffer, 0, sizeof(adcBuffer));
    memset(burstBuffer, 0, sizeof(burstBuffer));
    // Re-initialize anything if necessary
}


void handle_command()
{
    // Temporary command buffer with null termination
    char cmd_buffer[CMD_STR_LEN + 1];
    memcpy(cmd_buffer, uart_rx_buffer, CMD_STR_LEN);
    cmd_buffer[CMD_STR_LEN] = '\0'; // Null terminate

    if (strcmp(cmd_buffer, START____) == 0)
    {
        handle_start_system();
    }
    else if (strcmp(cmd_buffer, STOP_____) == 0)
    {
        handle_stop_system();
    }
    else if (strcmp(cmd_buffer, RESET____) == 0)
    {
        handle_reset_system();
    }
    else if (strcmp(cmd_buffer, TRGMODE__) == 0)
    {
        current_mode = ADC_TRIGGER_MODE;
    }
    else if (strcmp(cmd_buffer, INTMODE__) == 0)
    {
        current_mode = ADC_INTERRUPT_MODE;
    }
    // Re-arm UART DMA receive
    memcpy(uart_rx_buffer, "", CMD_STR_LEN);
    HAL_UART_Receive_DMA(ACTIVE_UART, uart_rx_buffer, CMD_STR_LEN);
}

void handle_sample()
{
    if(adcReadyToSend){
        ADC_Start();
    }
}

void handle_transmitt()
{
    // Check if the system is in Interrupt Mode
    if (current_mode == ADC_INTERRUPT_MODE)
    {
        // Define a temporary buffer to hold both ADC data and burst data
        uint8_t txBuffer[ADC_BUFFER_SIZE * 2 + BURST_SIZE];

        // Copy ADC data (16-bit) into the txBuffer
        memcpy(txBuffer, adcBuffer, ADC_BUFFER_SIZE * 2);

        // Append burst data (8-bit) to the txBuffer
        memcpy(txBuffer + (ADC_BUFFER_SIZE * 2), burstBuffer, BURST_SIZE);

        // Start UART DMA transmission of the combined data
        HAL_UART_Transmit_DMA(ACTIVE_UART, txBuffer, ADC_BUFFER_SIZE * 2 + BURST_SIZE);
        burstIndex = 0;
        handle_start_system();
    }
    else
    {
        // If not in Interrupt Mode, just send the ADC data (16-bit)
        HAL_UART_Transmit_DMA(ACTIVE_UART, (uint8_t *)adcBuffer, ADC_BUFFER_SIZE * 2);
    }

}



void handle_gpio_events()
{
    if (burstIndex + 5 <= BURST_BUFFER_SIZE)
    {
        // Capture the current timer value as the timestamp
        uint32_t timestamp = __HAL_TIM_GET_COUNTER(&htim2);

        // Capture the GPIO state of PA0 (0 for LOW, 1 for HIGH)
        uint8_t state = (uint8_t)HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_0);

        // Store the timestamp (split into 4 bytes) in the burst buffer
        burstBuffer[burstIndex++] = (uint8_t)(timestamp & 0xFF);         // Least significant byte of timestamp
        burstBuffer[burstIndex++] = (uint8_t)((timestamp >> 8) & 0xFF);  // 2nd byte of timestamp
        burstBuffer[burstIndex++] = (uint8_t)((timestamp >> 16) & 0xFF); // 3rd byte of timestamp
        burstBuffer[burstIndex++] = (uint8_t)((timestamp >> 24) & 0xFF); // Most significant byte of timestamp

        // Store the GPIO state in the burst buffer
        burstBuffer[burstIndex++] = state; // GPIO state (0 or 1)

        // Increment burstIndex for next data point
    }
    else
    {
        // Optional: Handle buffer overflow if necessary (e.g., reset or stop capturing)
        // For example, reset burstIndex to 0 if you want to overwrite old data
        burstIndex = 0; // This would overwrite older data
        // Or you can add an error handling mechanism if you want to stop or log the issue
    }
}
