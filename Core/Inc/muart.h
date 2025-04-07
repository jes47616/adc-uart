#ifndef __UART__H
#define __UART__H

#include "common.h"
#include "config.h"

#ifdef TEST_UART
void UART_Test_Start(void);
void send_start_time(void);
#endif

#endif
