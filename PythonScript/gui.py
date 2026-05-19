import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import struct
import numpy as np
import pandas as pd

# Importy niezbędne do osadzenia Matplotlib w Tkinterze
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# --- KONFIGURACJA SPRZĘTOWA ---
BAUDRATE = 115200
SAMPLES_PER_PING = 2000
BYTES_PER_PING = SAMPLES_PER_PING * 2
SAMPLE_RATE_MHZ = 2.0  # MSps



class DAQ_Dashboard(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("STM32G474RE - Akwizycja Sygnałów Ultradźwiękowych")
        self.geometry("1000x700")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Zmienne stanowe
        self.serial_port = None
        self.is_connected = False
        self.time_axis = np.arange(SAMPLES_PER_PING) / SAMPLE_RATE_MHZ # Czas w us

        self.waiting_for_binary = False
        self.current_temp = "Brak"

        self.create_widgets()
        self.update_com_ports()

    def create_widgets(self):
        # --- PANEL STEROWANIA (Góra) ---
        control_frame = ttk.LabelFrame(self, text="Konfiguracja Połączenia")
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        ttk.Label(control_frame, text="Port COM:").pack(side=tk.LEFT, padx=5, pady=5)
        self.cb_ports = ttk.Combobox(control_frame, width=30)
        self.cb_ports.pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(control_frame, text="Odśwież", command=self.update_com_ports).pack(side=tk.LEFT, padx=5)

        self.btn_connect = ttk.Button(control_frame, text="Połącz", command=self.toggle_connection)
        self.btn_connect.pack(side=tk.LEFT, padx=15, pady=5)

        self.lbl_status = ttk.Label(control_frame, text="Status: Rozłączono", foreground="red", font=("Arial", 10, "bold"))
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        # --- PANEL WYKRESU (Środek) ---
        plot_frame = ttk.Frame(self)
        plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.fig.patch.set_facecolor('#f0f0f0') # Dopasowanie do tła GUI
        
        # Inicjalizacja pustego wykresu
        self.line, = self.ax.plot(self.time_axis, np.zeros(SAMPLES_PER_PING), color='blue')
        self.ax.set_title("Odbierane echo ultradźwiękowe (ADC)")
        self.ax.set_xlabel("Czas [μs]")
        self.ax.set_ylabel("Amplituda ADC (0-4095)")
        self.ax.set_ylim(0, 4200) # Rezerwa ponad 4095
        self.ax.grid(True)

        # Osadzenie wykresu w Tkinterze
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- PANEL LOGÓW (Dół) ---
        log_frame = ttk.LabelFrame(self, text="Logi systemowe")
        log_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        self.txt_logs = tk.Text(log_frame, height=5, state=tk.DISABLED, bg="black", fg="lime")
        self.txt_logs.pack(fill=tk.BOTH, padx=5, pady=5)

    def log_msg(self, msg):
        """Dodaje wiadomość do konsoli w GUI"""
        self.txt_logs.config(state=tk.NORMAL)
        self.txt_logs.insert(tk.END, msg + "\n")
        self.txt_logs.see(tk.END) # Auto-scroll
        self.txt_logs.config(state=tk.DISABLED)

    def update_com_ports(self):
        """Wyszukuje dostępne porty COM (szuka urządzeń ST-Link)"""
        ports = serial.tools.list_ports.comports()
        port_list = [f"{port.device} - {port.description}" for port in ports]
        self.cb_ports['values'] = port_list
        if port_list:
            self.cb_ports.current(0)
            self.log_msg("Znaleziono porty COM.")
        else:
            self.cb_ports.set('')
            self.log_msg("Brak portów COM. Sprawdź podłączenie Nucleo.")

    def toggle_connection(self):
        """Obsługuje przycisk Połącz/Rozłącz"""
        if not self.is_connected:
            selection = self.cb_ports.get()
            if not selection:
                messagebox.showwarning("Błąd", "Wybierz port COM!")
                return
            
            port_name = selection.split(" - ")[0] # Wyciągnięcie samego np. 'COM3'
            
            try:
                self.serial_port = serial.Serial(port_name, BAUDRATE, timeout=0)
                self.serial_port.reset_input_buffer() # Czyścimy śmieci
                
                self.is_connected = True
                self.btn_connect.config(text="Rozłącz")
                self.lbl_status.config(text="Status: POŁĄCZONO (Oczekuję na dane...)", foreground="green")
                self.log_msg(f"Połączono z {port_name} ({BAUDRATE} bps).")
                
                # Uruchomienie pętli nasłuchującej w tle
                self.poll_serial_data()
                
            except Exception as e:
                messagebox.showerror("Błąd portu", f"Nie można otworzyć portu:\n{e}")
                self.log_msg(f"Błąd połączenia: {e}")
        else:
            self.disconnect()

    def disconnect(self):
        """Bezpieczne zamknięcie portu"""
        self.is_connected = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.log_msg("Rozłączono port COM.")
            
        self.btn_connect.config(text="Połącz")
        self.lbl_status.config(text="Status: Rozłączono", foreground="red")

    def poll_serial_data(self):
        """Asynchroniczna pętla z Maszyną Stanów (Tekst -> Binarka)"""
        if not self.is_connected:
            return

        try:
            # STAN 2: Czekamy na dane binarne z przetwornika ADC
            if getattr(self, 'waiting_for_binary', False):
                if self.serial_port.in_waiting >= BYTES_PER_PING:
                    raw_data = self.serial_port.read(BYTES_PER_PING)
                    
                    self.log_msg(f"Odebrano dane ADC dla {self.current_temp}°C. Rysuję...")
                    self.serial_port.reset_input_buffer() # Czyścimy ewentualne śmieci
                    
                    self.waiting_for_binary = False # Wracamy do nasłuchu tekstu
                    self.process_and_plot(raw_data)
                    
            # STAN 1: Nasłuchujemy wiadomości tekstowych (Nadzorca)
            else:
                if self.serial_port.in_waiting > 0:
                    self.serial_port.timeout = 0.05
                    line_bytes = self.serial_port.readline()
                    
                    if line_bytes:
                        try:
                            text = line_bytes.decode('utf-8').strip()
                            if text:
                                self.log_msg(f"STM32: {text}")
                                
                                # Jeśli wykryto start pomiaru, zapamiętujemy temperaturę i zmieniamy stan!
                                if text.startswith("T="):
                                    self.current_temp = text.split("=")[1]
                                    self.waiting_for_binary = True
                        except UnicodeDecodeError:
                            pass # To były resztki danych binarnych, ignorujemy

        except Exception as e:
            self.log_msg(f"Błąd odczytu: {e}")
            self.disconnect()

        # Wywołanie zwrotne pętli GUI
        if self.is_connected:
            self.after(50, self.poll_serial_data)

    def process_and_plot(self, raw_data):
        """Dekoduje surowe bajty i odświeża wykres"""
        # Odpakowanie do uint16_t
        format_string = f'<{SAMPLES_PER_PING}H'
        decoded_samples = struct.unpack(format_string, raw_data)
        
        # Aktualizacja wykresu
        self.line.set_ydata(decoded_samples)
        self.ax.set_title(f"Odbierane echo ultradźwiękowe (ADC) - Temp: {self.current_temp} °C")
        self.canvas.draw()
        
        # --- NOWE: Automatyczny zapis do Excela ---
        try:
            # Tworzymy nazwę pliku z aktualnej temperatury (np. "35stopni.xlsx")
            filename = f"{self.current_temp}stopni.xlsx"
            
            # Tworzymy strukturę danych (DataFrame) z jedną kolumną
            df = pd.DataFrame({'Odczyt_ADC': decoded_samples})
            
            # Zapisujemy do formatu Excel (bez dodatkowej kolumny indeksowania)
            df.to_excel(filename, index=False)
            
            self.log_msg(f"Zapisano pomiar do pliku: {filename}")
        except Exception as e:
            self.log_msg(f"Błąd zapisu do pliku Excel: {e}")

    def on_closing(self):
        """Sprzątanie przy zamykaniu okna"""
        self.disconnect()
        self.quit()
        self.destroy()

if __name__ == "__main__":
    app = DAQ_Dashboard()
    app.mainloop()