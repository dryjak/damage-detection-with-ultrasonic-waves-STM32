/*
 * data_acquisition_fsm.c
 *
 *  Created on: Mar 31, 2026
 *      Author: dryla
 */

#include "data_acquisition_fsm.h"

void DAQ_Init(DAQ_t *DAQ, uint16_t *DataTable, uint16_t TableSize, UART_HandleTypeDef *huart,
							ADC_HandleTypeDef *hadc,TIM_HandleTypeDef *htim_trigger, TIM_HandleTypeDef *htim, uint16_t TimerChannel)
{
	DAQ->DataTable = DataTable;
	DAQ->TableSize = TableSize;
	DAQ->huart = huart;
	DAQ->hadc = hadc;
	DAQ->htim = htim;
	DAQ->TimerChannel = TimerChannel;
	DAQ->htim_trigger = htim_trigger;

	DAQ->TimeMeasure = HAL_GetTick();
	DAQ->AdcReadyFlag 	 = 0;
	DAQ->UartTxReadyFlag = 0;

	DAQ->DAQ_STATE = DAQ_STATE_IDLE;
}

void DAQ_Task_Idle(DAQ_t *DAQ)
{
    if(HAL_GetTick() - DAQ->TimeMeasure >= DAQ_TIME_TO_WAIT)
    {
        DAQ->TimeMeasure = HAL_GetTick();
        DAQ->AdcReadyFlag    = 0;
        DAQ->UartTxReadyFlag = 0;

        // 1. Uzbrajamy ADC (czeka na trigger)
        HAL_ADC_Start_DMA(DAQ->hadc, (uint32_t*) DAQ->DataTable, DAQ->TableSize);

        // 2. NOWE: Uruchamiamy bazę czasu (TIM6), która zacznie taktować ADC (2 MSps)
        HAL_TIM_Base_Start(DAQ->htim_trigger);

        // 3. Uruchamiamy sekwencję PWM (Toneburst)
        HAL_TIM_PWM_Start(DAQ->htim, DAQ->TimerChannel);

        DAQ->DAQ_STATE = DAQ_STATE_ACQUIRING;
    }
}

void DAQ_Task_Acquiring(DAQ_t *DAQ)
{
    if(DAQ->AdcReadyFlag == 1)
    {
        DAQ->AdcReadyFlag = 0;

        // NOWE: Wyłączamy TIM6, aby nie strzelał niepotrzebnie do ADC podczas transferu UART
        HAL_TIM_Base_Stop(DAQ->htim_trigger);

        HAL_TIM_PWM_Stop(DAQ->htim, DAQ->TimerChannel);//aby wyłączyć stan wysoki po zakończeniu 5 imulsu


        // Transfer danych po DMA
        HAL_UART_Transmit_DMA(DAQ->huart, (uint8_t*) DAQ->DataTable, 2 * (DAQ->TableSize));

        DAQ->DAQ_STATE = DAQ_STATE_TRANSFER_PENDING;
    }
}

void DAQ_Task_TRANSFER_PENDING(DAQ_t *DAQ)
{
    // Czekamy na flagę z przerwania UART TX Complete
    if(DAQ->UartTxReadyFlag == 1)
    {
        DAQ->UartTxReadyFlag = 0;

        // Dopiero teraz układ jest gotowy na kolejny "ping" ultradźwiękowy
        DAQ->DAQ_STATE = DAQ_STATE_IDLE;
    }


}


void DAQ_Task_Error(DAQ_t *DAQ)
{
	//error something
}

//place this function in HAL_uart_thansfer cplt
void DAQ_Transfer_Complete_Callback(DAQ_t *DAQ)
{
	//change transfer flag
	DAQ->UartTxReadyFlag = 1;
}

//place this function in HAL_adc_thansfer cplt
void DAQ_ADC_Conv_Complete_Callback(DAQ_t *DAQ)
{
	//change ADC flag
	DAQ->AdcReadyFlag = 1;
}

void DAQ_Task(DAQ_t *DAQ)
{
	switch(DAQ->DAQ_STATE){
	case DAQ_STATE_IDLE:
			//do state idle
		DAQ_Task_Idle(DAQ);
	break;
	case DAQ_STATE_ACQUIRING:
			//do state idle
		DAQ_Task_Acquiring(DAQ);
	break;
	case DAQ_STATE_TRANSFER_PENDING:
			//do state idle
		DAQ_Task_TRANSFER_PENDING(DAQ);

	break;
	case DAQ_STATE_ERROR:
			//do state idle
	break;
	}
}

