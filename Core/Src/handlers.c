#include "handlers.h"

void init(void) {
    init_ring_buffers();
    ADC_Start();
    Timer2_Start(&htim2);
    Timer3_Start(&htim3);
    send_start_time();
}

void handle_start_system(void)
{   
	handle_reset_system();
    if(current_mode == ADC_TRIGGER_MODE){
        init();
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

    deinit_ring_buffers();

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
        handle_reset_system();
    }
    else if (strcmp(cmd_buffer, TRGMODE__) == 0)
    {
        current_mode = ADC_TRIGGER_MODE;
        handle_reset_system();
    }
    else if (strcmp(cmd_buffer, INTMODE__) == 0)
    {
        current_mode = ADC_INTERRUPT_MODE;
        handle_reset_system();
    }
    // Re-arm UART DMA receive
    memcpy(uart_rx_buffer, 0, CMD_STR_LEN);
    HAL_UART_Receive_DMA(ACTIVE_UART, uart_rx_buffer, CMD_STR_LEN);
}

void handle_sample()
{
        ADC_Start();
}

void handle_transmitt()
{
    static uint8_t tx_buffer_gpio[21];
    static uint8_t tx_buffer_adc[21];
    uint8_t adc_values[20] = {0};
    uint8_t gpio_values[20] = {0};

    uint8_t adc_ok = ring_buffer_dequeue_arr(&adc_ring_buffer, adc_values, 20);
    uint8_t gpio_ok = ring_buffer_dequeue_arr(&gpio_ring_buffer, gpio_values, 20);

    // Use separate buffers for GPIO and ADC data to avoid conflicts
    
    // First check for GPIO data
    if (gpio_ok) {
        tx_buffer_gpio[0] = 0xB0;  // GPIO header
        memcpy(&tx_buffer_gpio[1], gpio_values, 20);
        
        // Wait for any ongoing transmission to complete
        while (HAL_UART_GetState(ACTIVE_UART) == HAL_UART_STATE_BUSY_TX) {
            // Small delay to prevent tight loop
            for (volatile int i = 0; i < 100; i++);
        }
        
        // Send GPIO data
        HAL_UART_Transmit_DMA(ACTIVE_UART, tx_buffer_gpio, 21);
        
        // Wait for completion before sending ADC data
        while (HAL_UART_GetState(ACTIVE_UART) == HAL_UART_STATE_BUSY_TX) {
            // Small delay to prevent tight loop
            for (volatile int i = 0; i < 100; i++);
        }
    }
    
    // Then check for ADC data
    if (adc_ok) {
        tx_buffer_adc[0] = 0xA0;  // ADC header
        memcpy(&tx_buffer_adc[1], adc_values, 20);
        HAL_UART_Transmit_DMA(ACTIVE_UART, tx_buffer_adc, 21);
    }
    else if (HAL_ADC_GetState(&hadc1) & HAL_ADC_STATE_REG_BUSY)
    {
        tx_buffer_adc[0] = 0xD0;
        memcpy(&tx_buffer_adc[1], adc_values, 20);
        HAL_UART_Transmit_DMA(ACTIVE_UART, tx_buffer_adc, 21);
    }
}

void handle_gpio_events()
{
        // Capture the current timer value as the timestamp
        uint32_t timestamp = __HAL_TIM_GET_COUNTER(&htim2);

        // Capture the GPIO state of PA0 (0 for LOW, 1 for HIGH)
        uint8_t state = (uint8_t)HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_1);

        // Store the timestamp (split into 4 bytes) in the burst buffer
        burstBuffer[0] = (uint8_t)(timestamp & 0xFF);         // Least significant byte of timestamp
        burstBuffer[1] = (uint8_t)((timestamp >> 8) & 0xFF);  // 2nd byte of timestamp
        burstBuffer[2] = (uint8_t)((timestamp >> 16) & 0xFF); // 3rd byte of timestamp
        burstBuffer[3] = (uint8_t)((timestamp >> 24) & 0xFF); // Most significant byte of timestamp

        // Store the GPIO state in the burst buffer
        burstBuffer[4] = state; // GPIO state (0 or 1)
        ring_buffer_queue_arr(&gpio_ring_buffer, burstBuffer,5);

}
