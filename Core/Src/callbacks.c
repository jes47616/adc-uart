#include "config.h"
#include "common.h"

/*
################################################################
                    ADC CALLBACKs
################################################################
*/

void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *hadc)
{
    if (hadc->Instance == ADC1)
    {
        adcReadyToSend = 1;
        handle_transmitt();
    }
}

/*
################################################################
                    ADC CALLBACKs
################################################################
*/

/*
################################################################
                    GPIO CALLBACKs
################################################################
*/

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
    if (current_mode == ADC_INTERRUPT_MODE)
    {
        if (burstIndex == 0) Timer3_Start();
        // Check if the interrupt is from PA0
        if (GPIO_Pin == GPIO_PIN_0) // This checks if the interrupt is triggered by PA0
        {
            handle_gpio_events();
        }
    }
}

/*
################################################################
                    GPIO CALLBACKs
################################################################
*/

/*
################################################################
                    UART CALLBACKs
################################################################
*/

#ifdef TEST_UART

// Function to start UART test
void UART_Test_Start(void)
{
    uint8_t msg[] = "\n";
    UART_Transmit(msg, 1); // Start transmission on the active UART
}

#endif

void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart == ACTIVE_UART)
    {
        uartTxCompleteFlag = 1; // Set the flag indicating that UART TX via DMA is complete
        handle_sample();
    }
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart == ACTIVE_UART)
    {
        handle_command();
    }
}

/*
################################################################
                    UART CALLBACKs
################################################################
*/

/*
################################################################
                    TIMER CALLBACKs
################################################################
*/

#ifdef TEST_TIMER

static uint32_t tickCount = 0;

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance == TIM2)
    {
        tickCount++;

        // Print every 10000 ticks (1s @ 10kHz)
        if (tickCount % 10000 == 0)
        {
            Print("Timer tick 1000\r\n");
        }
    }
}
#endif

/*
################################################################
                    TIMER CALLBACKs
################################################################
*/
