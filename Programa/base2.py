import time
from datetime import datetime
import csv


class SerialDataHandler:
    def __init__(self, parent):
       
        self.parent = parent
        self.serial_thread = None
        self.update_thread = None

    def read_serial_data(self):
        
        while self.parent.is_running:
            if not self.parent.is_paused and self.parent.serial_port and self.parent.serial_port.in_waiting:
                try:
                    line = self.parent.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self.parent.data_queue.put(line)
                except:
                    pass
            time.sleep(0.01)

    def update_data(self):
       
        while self.parent.is_running:
            try:
                while not self.parent.data_queue.empty():
                    line = self.parent.data_queue.get_nowait()
                    self.process_data(line)
                
               
                self.parent.root.after(100, self.parent.update_display)
            except:
                pass
            time.sleep(0.1)

    def process_data(self, line):

        #Procesa una línea de datos recibida

        try:
            parts = line.strip().split(',')
            if len(parts) == 4:
                sensor_id = int(parts[0])
                temperature_c = float(parts[1])
                humidity = float(parts[2])

                timestamp = datetime.now()

                if self.parent.start_time:
                    rel_time = (timestamp - self.parent.start_time).total_seconds()

                    temperature_f = self.parent.convert_temperature(temperature_c, 'fahrenheit')
                    temperature_k = self.parent.convert_temperature(temperature_c, 'kelvin')

                    sensor_key = f'sensor{sensor_id}'
                    self.parent.data[sensor_key]['temp_c'].append(temperature_c)
                    self.parent.data[sensor_key]['temp_f'].append(temperature_f)
                    self.parent.data[sensor_key]['temp_k'].append(temperature_k)
                    self.parent.data[sensor_key]['hum'].append(humidity)
                    self.parent.data[sensor_key]['rel_time'].append(rel_time)

                    if self.parent.csv_file:
                        with open(self.parent.csv_file, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'),
                                sensor_id,
                                f"{temperature_c:.2f}",
                                f"{humidity:.2f}"
                            ])

                    self.parent.data_count += 1

        except Exception as e:
            print(f"Error procesando datos: {e}")