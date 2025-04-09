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
        ring_buffer_queue_arr(&adc_ring_buffer,(uint8_t*) adcBuffer,ADC_BUFFER_SIZE * 2);
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
    // Remove the mode check to process GPIO events in all modes
    // Check if the interrupt is from PA0
    if (HAL_TIM_Base_GetState(&htim3) == HAL_TIM_STATE_READY && current_mode == ADC_INTERRUPT_MODE)
    {
        init();
    }
    if (GPIO_Pin == GPIO_PIN_1) // This checks if the interrupt is triggered by PA1
    {
        handle_gpio_events();
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



void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart == ACTIVE_UART)
    {
        if(!uartTxCompleteFlag) uartTxCompleteFlag = 1; // Set the flag indicating that UART TX via DMA is complete
        else handle_transmitt();
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
