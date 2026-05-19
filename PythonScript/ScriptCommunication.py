import serial
import struct
import numpy as np
import matplotlib.pyplot as plt

# --- KONFIGURACJA ---
PORT = 'COM3' # Zmień na port ST-Link z Menedżera Urządzeń
BAUDRATE = 115200
SAMPLES_PER_PING = 2000
BYTES_PER_PING = SAMPLES_PER_PING * 2

def main():
    print(f"Oczekiwanie na dane z {PORT} (Baud: {BAUDRATE})...")
    
    try:
        with serial.Serial(PORT, BAUDRATE, timeout=1) as ser:
            ser.reset_input_buffer()
            
            while True: # Nieskończona pętla nasłuchująca
                # 1. Czytamy jedną linię tekstu
                line = ser.readline()
                
                if line:
                    try:
                        # Ignorujemy błędy dekodowania, na wypadek gdybyśmy złapali ucięty bajt binarny
                        text = line.decode('utf-8', errors='ignore').strip()
                        if text:
                            print(f"> Log STM32: {text}")
                            
                        # 2. Jeśli to nasza flaga pomiarowa...
                        if text.startswith("T="):
                            temp = text.split("=")[1]
                            print(f"-> Rozpoznano komendę pomiaru dla {temp}°C! Czekam na 4000 bajtów...")
                            
                            # Czekamy na pobranie dokładnie 4000 bajtów
                            ser.timeout = 3 # Dajemy chwilę więcej na transfer DMA
                            raw_data = ser.read(BYTES_PER_PING)
                            ser.timeout = 1
                            
                            if len(raw_data) == BYTES_PER_PING:
                                print("-> Paczka binarne odebrana poprawnie! Rysuję wykres...")
                                
                                format_string = f'<{SAMPLES_PER_PING}H'
                                decoded_samples = struct.unpack(format_string, raw_data)
                                time_axis = np.arange(SAMPLES_PER_PING) * 0.5 
                                
                                plt.figure(figsize=(12, 6))
                                plt.plot(time_axis, decoded_samples, label=f'Echo Ultradźwiękowe ({temp}°C)', color='blue')
                                plt.title(f"Akwizycja STM32G474RE - Temperatura: {temp} °C")
                                plt.xlabel("Czas [μs]")
                                plt.ylabel("Amplituda ADC (0-4095)")
                                plt.grid(True)
                                plt.show()
                                
                            else:
                                print(f"Błąd: Odebrano tylko {len(raw_data)} bajtów.")
                    except Exception as e:
                        print(f"Błąd przetwarzania: {e}")
                        
    except Exception as e:
        print(f"Błąd krytyczny portu COM: {e}")

if __name__ == '__main__':
    main()