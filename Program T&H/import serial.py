import serial
import threading
import pandas as pd
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource
from bokeh.layouts import column
from datetime import datetime

# --- CONFIGURA TU PUERTO SERIAL ---
PORT = "COM3"   # cambia si es otro (ej: '/dev/ttyUSB0' en Linux)
BAUD = 9600

# Crear la conexión serial
ser = serial.Serial(PORT, BAUD, timeout=1)

# --- FUENTE DE DATOS PARA GRAFICAR ---
data = {
    'time': [],
    'temperature': [],
    'humidity': [],
    'sensor': []
}
source = ColumnDataSource(data=data)

# --- FIGURAS DE BOKEH ---
p_temp = figure(title="Temperatura (°C)", x_axis_type="datetime", height=250)
p_temp.line('time', 'temperature', source=source, line_width=2, color='red', legend_label="Temperatura")
p_temp.legend.location = "top_left"

p_hum = figure(title="Humedad (%)", x_axis_type="datetime", height=250)
p_hum.line('time', 'humidity', source=source, line_width=2, color='blue', legend_label="Humedad")
p_hum.legend.location = "top_left"

layout = column(p_temp, p_hum)
curdoc().add_root(layout)
curdoc().title = "Datos DHT22 - Arduino"

# --- FUNCIÓN DE LECTURA SERIAL ---
def read_serial():
    while True:
        try:
            line = ser.readline().decode().strip()
            if not line:
                continue

            parts = line.split(',')
            if len(parts) != 4:
                continue

            sensor_id, temp, hum, t = parts
            temp = float(temp)
            hum = float(hum)
            timestamp = datetime.now()

            new_data = {
                'time': [timestamp],
                'temperature': [temp],
                'humidity': [hum],
                'sensor': [int(sensor_id)]
            }

            # Agregar datos al gráfico
            source.stream(new_data, rollover=200)

        except Exception as e:
            print("Error:", e)

# --- HILO PARA LEER EL SERIAL EN PARALELO ---
thread = threading.Thread(target=read_serial)
thread.daemon = True
thread.start()
