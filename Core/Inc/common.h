#ifndef __COMMON_H__
#define __COMMON_H__

#include "config.h"
#include <stdio.h>
#include <string.h>

// Function prototypes
void UART_Transmit(uint8_t *data, uint16_t size);
void Print(const char *msg);

// System control prototypes
void init_ring_buffers(void);
void deinit_ring_buffers(void);


#endif /* __COMMON_H__ */
