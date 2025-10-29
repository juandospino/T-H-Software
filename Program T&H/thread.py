# serial_thread.py
from PySide6.QtCore import QThread, Signal
import serial
import time
import csv
import os
from datetime import datetime

class SerialReader(QThread):
    data_received = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, port, baudrate=9600, csv_file="datos_sensores.csv"):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.is_running = True
        self.ser = None
        self.csv_file = csv_file


        if not os.path.exists(self.csv_file):
            try:
                with open(self.csv_file, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["SensorID", "Temperatura", "Humedad", "TiempoArduino", "FechaLectura"])
            except Exception as e:
                print(f" Error creando CSV: {e}")

    def run(self):
        try:
            print(f"🔌 Conectando a {self.port} a {self.baudrate} baudios...")
            self.ser = serial.Serial(self.port, self.baudrate, timeout=2)
            time.sleep(2)
           

            buffer = ""
            while self.is_running:
                try:
                    if self.ser.in_waiting:
                        raw_bytes = self.ser.read(self.ser.in_waiting)
                        chunk = raw_bytes.decode("utf-8", errors='ignore')
                        buffer += chunk

                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()

                            if not line or not any(c.isdigit() for c in line):
                                continue

                            parts = line.split(',')
                            if len(parts) == 4:
                                try:
                                    data = {
                                        "id": int(parts[0]),
                                        "temp": float(parts[1]),
                                        "hum": float(parts[2]),
                                        "time": parts[3]
                                    }
                                    # emitir señal a la GUI
                                    self.data_received.emit(data)
                                    print(f" {data}")

                                    # Guardar en CSV (con fecha/hora local)
                                    with open(self.csv_file, "a", newline="") as f:
                                        writer = csv.writer(f)
                                        writer.writerow([
                                            data["id"],
                                            data["temp"],
                                            data["hum"],
                                            data["time"],
                                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        ])
                                except ValueError as ve:
                                    print(f"⚠️ Conversión fallida en línea '{line}': {ve}")
                            else:
                                print(f"⚠️ Formato incorrecto (esperado 4 campos): '{line}'")
                    else:
                        time.sleep(0.05)
                except Exception as e:
                    
                    time.sleep(0.5)

        except serial.SerialException as e:
            msg = f"Error serial: {e}"
            
            self.error_signal.emit(msg)
        except Exception as e:
            msg = f"Error inesperado en SerialReader: {e}"
            self.error_signal.emit(msg)
        finally:
            try:
                if self.ser and self.ser.is_open:
                    self.ser.close()
                    print(" Conexión serial cerrada")
            except Exception:
                pass

    def stop(self):
        print(" Deteniendo hilo serial...")
        self.is_running = False
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass
        self.quit()
        self.wait(2000)
