#ifndef __COMMON_H__
#define __COMMON_H__

#include "config.h"
#include <stdio.h>
#include <string.h>

// Function prototypes
void UART_Transmit(uint8_t *data, uint16_t size);
void Print(const char *msg);

// System control prototypes
void start_system(void);
void stop_system(void);
void reset_system(void);
void restart_system(void);
void change_trigger_level(uint16_t newLevel);
void capture_burst(void); // Optional for interrupt mode
void set_default_trigger_level(void);

#endif /* __COMMON_H__ */
