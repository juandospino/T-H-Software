from PySide6.QtCore import QThread, Signal
from datetime import datetime
import serial
import time

class SerialReader(QThread):

    data_received = Signal(dict)   #señal para mandar los datos a la GUI
    error_signal = Signal(str)     #señal para mandar errores a la GUI

    def __init__(self, port):
        super().__init__()
        self.running = False
        self.port = port

    def start(self):
        try:
            ser = serial.Serial(self.port, 9600)
            time.sleep(2)
            self.running = True

            while self.running:

                try:
                    new_data = ser.readline().decode("utf-8").strip()
                    if not new_data:
                        continue

                    parts = new_data.split(",")

                    if len(parts) == 3:

                        try:
                            n = int(parts[0])
                            temp = float(parts[1])
                            hum = float(parts[2])

                            result = {"id": n, "temp": temp, "hum": hum, "time": datetime.now()} #Guarda los datos en un diccionario
                            self.data_received.emit(result) #Emite los datos del hilo a la GUI
                        except:
                            self.error_signal.emit("Error de formato en los datos recibidos.")

                except Exception as e:
                    self.error_signal.emit(f"Error durante la lectura: {str(e)}") 
                    break

        except serial.SerialException as error:
             print(f"Error: {error}")

        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()

    def stop(self):
        self.running = False
        self.wait(1000)