#ifndef __ADC_H__
#define __ADC_H__

#include "config.h"
#include "common.h"

void handle_start_system(void);
void handle_stop_system(void);
void handle_reset_system(void);
void handle_command();
void handle_sample();
void handle_transmitt();

void init(void);




#endif