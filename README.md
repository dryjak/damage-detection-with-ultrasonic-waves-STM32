# damage-detection-with-ultrasonic-waves-STM32
Data acquisition  (DAQ) system for studying ultrasonic waves and phase shift due to temperature or damage. Build with STM32G4 (DMA, 2MSps) and python gui with real time plotting and exel export

Markdown

# ThermoSonic-DAQ: Ultrasonic Data Acquisition System

A comprehensive Data Acquisition (DAQ) system designed to study the effect of temperature on the propagation of ultrasonic waves in solid materials (e.g., aluminum). This project consists of embedded firmware (C/HAL) for the STM32G4 microcontroller and a desktop GUI application (Python) for real-time data visualization and automated logging.

## 🚀 Key Features

* **Hardware Triggering:** The ADC samples the signal at a rigorous 2 MSps using a hardware timer (TIM6), completely eliminating software jitter.
* **Non-Blocking Architecture & DMA:** Large data payloads (4000 bytes per ping) are transferred in the background using the DMA controller and LPUART, keeping the main CPU core free.
* **Finite State Machine (FSM):** The acquisition logic is implemented as a clean, non-blocking state machine with built-in hardware error handling (e.g., ADC Overrun protection and timeouts).
* **Precision Temperature Sensing:** Integrates a MAX31865 RTD-to-Digital Converter via SPI with a PT100 sensor (3-wire compensation) to trigger acoustic measurements at strictly defined temperature thresholds.
* **Python GUI Dashboard:** A multithreaded (asynchronous) desktop application that reads the serial port, plots echograms in real-time, and automatically exports data vectors to `.xlsx` (Excel) files for further DSP analysis.

---

## 🛠️ Hardware Architecture

The system was designed with hardware-level crosstalk minimization in mind, isolating the high-current driving signal from the highly sensitive receiving path.

* **MCU:** STM32G474RE (Cortex-M4, 170 MHz)
* **Transmitter Path (TX):** A PWM signal (200 kHz) amplified by a dedicated **TC4427** MOSFET driver (logic level shifted from 3.3V to 12V), driving the transmitting piezoelectric transducer.
* **Receiver Path (RX):** The signal from the receiving piezo is filtered (passive high-pass filter) and amplified by a wideband **MCP6022** operational amplifier (10 MHz GBWP), biased with a 1.65V virtual ground.
* **Temperature Measurement:** An industrial-grade PT100 RTD sensor coupled with an external MAX31865 module.
* **Aluminum sheet (200mm x 100mm x 2mm )**
---

## 🔧 Measurement Station 
<img width="3694" height="2550" alt="MeasurementStation" src="https://github.com/user-attachments/assets/531198e9-0007-4ad8-9227-856bf160208e" />


## 💻 Software Architecture

### 1. Firmware (`STM32_Code` directory)
Written in C using the STM32 HAL libraries.
* `data_acquisition_fsm.c / .h`: The core of the system, handling hardware initialization, DMA triggering, timer management, and PC communication.
* `MAX31865.c / .h`: A custom library for handling the temperature sensor via SPI.
* `main.c`: The Supervisor that manages measurement intervals, temperature drop logic, and overall system state.

### 2. PC Application (`Python_GUI` directory)
Built using: `tkinter`, `pyserial`, `matplotlib`, `numpy`, and `pandas`.
Solves the data stream desynchronization problem by implementing a serial port state machine capable of distinguishing between ASCII status messages and raw, binary ADC memory dumps.
<img width="1002" height="737" alt="GUI: 2026-05-18 203613" src="https://github.com/user-attachments/assets/2964e5b0-c12b-496e-9523-d168354554f6" />

---

## 🔧 Measurement Station 
