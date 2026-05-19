/*
 * data_acquisition_fsm.h
 *
 *  Created on: Mar 31, 2026
 *      Author: dryla
 */


#ifndef INC_DATA_ACQUISITION_FSM_H_
#define INC_DATA_ACQUISITION_FSM_H_

#include "main.h"
#define DAQ_TIME_TO_WAIT 6000

//definicja stanów
typedef enum {
    DAQ_STATE_IDLE = 0,
    DAQ_STATE_ACQUIRING,
    DAQ_STATE_TRANSFER_PENDING,
    DAQ_STATE_ERROR
} DAQ_STATE_t;

typedef struct{
	uint16_t *DataTable; 	//pointer to table for storing data
	uint16_t TableSize;		//size of table

	UART_HandleTypeDef 	*huart;
	ADC_HandleTypeDef 	*hadc;
	TIM_HandleTypeDef 	*htim;
	TIM_HandleTypeDef 	*htim_trigger;
	uint16_t 			TimerChannel;

	volatile DAQ_STATE_t DAQ_STATE;
	volatile uint8_t AdcReadyFlag;  // Flaga ustawiana w callbacku ADC
	volatile uint8_t UartTxReadyFlag; // Flaga ustawiana w callbacku UART

	uint32_t TimeMeasure;
}DAQ_t;


void DAQ_Init(DAQ_t *DAQ, uint16_t *DataTable, uint16_t TableSize, UART_HandleTypeDef *huart,
							ADC_HandleTypeDef *hadc,TIM_HandleTypeDef *htim_trigger, TIM_HandleTypeDef *htim, uint16_t TimerChannel);

void DAQ_Task(DAQ_t *DAQ);
void DAQ_ADC_Conv_Complete_Callback(DAQ_t *DAQ);
void DAQ_Transfer_Complete_Callback(DAQ_t *DAQ);

#endif /* INC_DATA_ACQUISITION_FSM_H_ */
