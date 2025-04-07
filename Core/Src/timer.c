#include "timer.h"

void Timer2_Start(void) {
    HAL_TIM_Base_Start_IT(&htim2);
}

void Timer2_Stop(void) {
    HAL_TIM_Base_Stop_IT(&htim2);
}


void Timer3_Start(void) {
    HAL_TIM_Base_Start_IT(&htim3);
}

void Timer3_Stop(void) {
    HAL_TIM_Base_Stop_IT(&htim3);
}



