import serial
import csv
import time
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import sys

class SensorMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Sensores DHT22")
        self.root.geometry("1300x850")
        
        # Variables de control
        self.is_running = False
        self.is_paused = False
        self.serial_port = None
        self.data_queue = queue.Queue()
        
        # Variables de datos
        self.max_points = 200
        self.data = {
            'sensor0': {'temp_c': deque(maxlen=self.max_points), 'temp_f': deque(maxlen=self.max_points), 'temp_k': deque(maxlen=self.max_points), 'hum': deque(maxlen=self.max_points), 
                       'time': deque(maxlen=self.max_points)},
            'sensor1': {'temp_c': deque(maxlen=self.max_points),'temp_f': deque(maxlen=self.max_points), 'temp_k': deque(maxlen=self.max_points), 'hum': deque(maxlen=self.max_points), 
                         'time': deque(maxlen=self.max_points)},
            'sensor2': {'temp_c': deque(maxlen=self.max_points), 'temp_f': deque(maxlen=self.max_points), 'temp_k': deque(maxlen=self.max_points), 'hum': deque(maxlen=self.max_points), 
                          'time': deque(maxlen=self.max_points)},
            'sensor3': {'temp_c': deque(maxlen=self.max_points),  'temp_f': deque(maxlen=self.max_points),  'temp_k': deque(maxlen=self.max_points),  'hum': deque(maxlen=self.max_points), 
                       'time': deque(maxlen=self.max_points)},
        }
        
        # Variables de configuración
        self.port_var = tk.StringVar()
        self.baudrate_var = tk.StringVar(value="9600")
        self.max_points_var = tk.IntVar(value=200)
        self.temp_unit_var = tk.StringVar(value="celsius") 
        self.csv_file = None
        
        self.unit_labels = {
            'celsius': ('°C', 'Temperatura (°C)'),
            'fahrenheit': ('°F', 'Temperatura (°F)'),
            'kelvin': ('K', 'Temperatura (K)')
        }
        
        # Configurar la interfaz
        self.setup_ui()
        # Configurar gráficos
        self.setup_plots()
        # Buscar puertos disponibles al inicio
        self.find_serial_ports()
        
    def setup_ui(self):
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        style = ttk.Style()
        style.configure("My.TLabelframe.Label", font=("Arial", 12, "bold"))


        # Configurar expansión
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="ThermoHumid Tracker", 
                               font=("Arial", 24, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 15))
        
        # Frame de controles principales
        control_frame = ttk.LabelFrame(main_frame, text="Configuración Principal",style="My.TLabelframe", padding="10")
        control_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Puerto serial
        ttk.Label(control_frame, text="Puerto COM:").grid(row=0, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        self.port_combo = ttk.Combobox(control_frame, textvariable=self.port_var, width=15)
        self.port_combo.grid(row=0, column=1, padx=(0, 15), pady=5, sticky=tk.W)
        
        # Botón para buscar puertos
        ttk.Button(control_frame, text="🔍 Buscar Puertos", 
                  command=self.find_serial_ports, width=15).grid(row=0, column=2, padx=(0, 15), pady=5, sticky=tk.W)
        
        # Baudrate
        ttk.Label(control_frame, text="Baudrate:").grid(row=0, column=3, padx=(0, 5), pady=5, sticky=tk.W)
        baudrates = ["9600", "19200", "38400", "57600", "115200"]
        baudrate_combo = ttk.Combobox(control_frame, textvariable=self.baudrate_var, 
                                     values=baudrates, width=10, state="readonly")
        baudrate_combo.grid(row=0, column=4, padx=(0, 15), pady=5, sticky=tk.W)
        
        # Puntos máximos
        ttk.Label(control_frame, text="Puntos a mostrar:").grid(row=0, column=5, padx=(0, 5), pady=5, sticky=tk.W)
        ttk.Spinbox(control_frame, from_=50, to=1000, textvariable=self.max_points_var, 
                   width=10, command=self.update_max_points).grid(row=0, column=6, padx=(0, 15), pady=5, sticky=tk.W)
        
        # Frame de configuración de unidades
        unit_frame = ttk.LabelFrame(main_frame, text="Unidades de Temperatura",style="My.TLabelframe", padding="10")
        unit_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Botones de radio para unidades
        ttk.Radiobutton(unit_frame, text="Celsius (°C)", 
                       variable=self.temp_unit_var, 
                       value="celsius",
                       command=self.update_units).grid(row=0, column=0, padx=10)
        
        ttk.Radiobutton(unit_frame, text="Fahrenheit (°F)", 
                       variable=self.temp_unit_var, 
                       value="fahrenheit",
                       command=self.update_units).grid(row=0, column=1, padx=10)
        
        ttk.Radiobutton(unit_frame, text="Kelvin (K)", 
                       variable=self.temp_unit_var, 
                       value="kelvin",
                       command=self.update_units).grid(row=0, column=2, padx=10)
        
        # Botón de conversión rápida
        ttk.Button(unit_frame, text="Convertir Datos", 
                  command=self.convert_existing_data, width=15).grid(row=0, column=3, padx=20)
        
        # Frame de botones de control
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=(0, 10))
        
        # Botones de control
        self.start_button = ttk.Button(button_frame, text="▶️Comenzar", 
                                      command=self.start_monitoring, width=15)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.pause_button = ttk.Button(button_frame, text="⏸️ Pausar", 
                                      command=self.pause_monitoring, width=15, state=tk.DISABLED)
        self.pause_button.grid(row=0, column=1, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ Detener", 
                                     command=self.stop_monitoring, width=15, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=2, padx=5)

        ttk.Button(button_frame, text="Reiniciar", 
                  command=self.reset_graphs, width=15).grid(row=0, column=3, padx=5)
        
        
        ttk.Button(button_frame, text="💾 Guardar Datos", 
                  command=self.save_data, width=15).grid(row=0, column=4, padx=5)
        
        ttk.Button(button_frame, text="📊 Ver Reporte", 
                  command=self.show_report, width=15).grid(row=0, column=5, padx=5)
        
        
        # Frame de información
        info_frame = ttk.LabelFrame(main_frame, text="Información del Sistema", style="My.TLabelframe", padding="10")
        info_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Labels de información
        self.status_label = ttk.Label(info_frame, text="Estado: Desconectado")
        self.status_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        self.data_count_label = ttk.Label(info_frame, text="Datos recibidos: 0")
        self.data_count_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        self.unit_label = ttk.Label(info_frame, text="Unidad: Celsius (°C)")
        self.unit_label.grid(row=0, column=2, sticky=tk.W, padx=(0, 20))
        
        self.file_label = ttk.Label(info_frame, text="Archivo: No especificado")
        self.file_label.grid(row=0, column=3, sticky=tk.W)
        
        # Frame de valores actuales
        values_frame = ttk.LabelFrame(main_frame, text="Valores Actuales",style="My.TLabelframe", padding="10")
        values_frame.grid(row=5, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Configurar grid para valores (2x2)
        for i in range(4):
            values_frame.columnconfigure(i, weight=4)
        
        # Crear labels para cada sensor
        self.sensor_labels = []
        for i in range(4):
            col = i % 4
            row = i // 4
            
            sensor_frame = ttk.Frame(values_frame, relief=tk.RIDGE, padding="5")
            sensor_frame.grid(row=row, column=col, padx=5, pady=15, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            sensor_name = f"Sensor {i}" if i > 0 else "Sensor Local"
            name_label = ttk.Label(sensor_frame, text=f" {sensor_name}", 
                                  font=("Arial", 12, "bold"))
            name_label.grid(row=0, column=1, sticky=tk.W, pady=(0, 5))
            
            # Frame para temperatura con unidad
            temp_frame = ttk.Frame(sensor_frame)
            temp_frame.grid(row=1, column=0, sticky=tk.W, pady=2)
            
            temp_unit_label = ttk.Label(temp_frame, text="Temp:")
            temp_unit_label.grid(row=0, column=0, sticky=tk.W)
            
            temp_value_label = ttk.Label(temp_frame, text="--", font=("Arial", 10, "bold"))
            temp_value_label.grid(row=0, column=1, sticky=tk.W, padx=(2, 5))
            
            temp_symbol_label = ttk.Label(temp_frame, text="°C")
            temp_symbol_label.grid(row=0, column=2, sticky=tk.W)
            
            # Frame para humedad
            hum_frame = ttk.Frame(sensor_frame)
            hum_frame.grid(row=2, column=0, sticky=tk.W, pady=2)
            
            ttk.Label(hum_frame, text="Hum:").grid(row=0, column=0, sticky=tk.W)
            hum_value_label = ttk.Label(hum_frame, text="--", font=("Arial", 10, "bold"))
            hum_value_label.grid(row=0, column=1, sticky=tk.W, padx=(2, 5))
            ttk.Label(hum_frame, text="%").grid(row=0, column=2, sticky=tk.W)
            
            # Tiempo de última lectura
            time_frame = ttk.Frame(sensor_frame)
            time_frame.grid(row=3, column=0, sticky=tk.W, pady=(8, 0))

            # Etiqueta fija "Última:"
            ttk.Label(time_frame, text="Última:", font=("Arial", 8), foreground="gray").grid(row=0, column=0, sticky=tk.W)

            # Etiqueta para la hora (la guardaremos para actualizarla)
            time_label = ttk.Label(time_frame, text="--:--:--", font=("Arial", 8, "bold"), foreground="gray")
            time_label.grid(row=0, column=1, sticky=tk.W, padx=(2, 5))
            
            # Guardar referencias a los labels
            self.sensor_labels.append({
                'temp_value': temp_value_label,
                'temp_symbol': temp_symbol_label,
                'hum_value': hum_value_label,
                'time': time_label
            })
           
        # Configurar expansión del frame principal
        main_frame.rowconfigure(10, weight=4)
        
    def setup_plots(self):
        # Crear figura con 2 subplots
        self.fig, self.axes = plt.subplots(2, 1, figsize=(12, 5))
        
        # Configurar los gráficos con unidades iniciales
        current_unit = self.temp_unit_var.get()
        unit_symbol = self.unit_labels[current_unit][0]
        unit_title = self.unit_labels[current_unit][1]
        
        self.axes[0].set_title(f'{unit_title}')
        self.axes[0].set_xlabel('Tiempo (s)')
        self.axes[0].set_ylabel(f'Temperatura ({unit_symbol})')
        self.axes[0].grid(True, alpha=0.3)
        
        self.axes[1].set_title('Humedad vs Tiempo')
        self.axes[1].set_xlabel('Tiempo (s)')
        self.axes[1].set_ylabel('Humedad (%)')
        self.axes[1].grid(True, alpha=0.3)
        self.colors = ['#1f77b4', "#0019FC", '#d62728', '#9467bd'] 
        self.lines_temp = []
        self.lines_hum = []
        
        for i in range(4):
            line_temp, = self.axes[0].plot([], [], 
                                         color=self.colors[i],
                                         marker='o', 
                                         markersize=5, 
                                         linewidth=2.5,
                                         alpha=0.8,
                                         label=f'Sensor {i}' if i > 0 else 'Sensor Local')
            line_hum, = self.axes[1].plot([], [], 
                                        color=self.colors[i],
                                        marker='s', 
                                        markersize=5, 
                                        linewidth=2.5,
                                        alpha=0.8,
                                        label=f'Sensor {i}' if i > 0 else 'Sensor Local')
            
            self.lines_temp.append(line_temp)
            self.lines_hum.append(line_hum)
        
        # Agregar leyendas
        self.axes[0].legend(loc='upper right', fontsize=9)
        self.axes[1].legend(loc='upper right', fontsize=9)
        plt.tight_layout()
        
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas_widget = self.canvas.get_tk_widget()
        
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                self.canvas_widget.grid(row=6, column=0, columnspan=4, 
                                       sticky=(tk.W, tk.E, tk.N, tk.S), 
                                       padx=10, pady=(0, 10))
                break
        
        # Configurar expansión para el canvas
        self.root.rowconfigure(6, weight=1)
    
    def convert_temperature(self, temp_c, to_unit):
        
        if pd.isna(temp_c):
            return temp_c
            
        if to_unit == 'celsius':
            return temp_c
        elif to_unit == 'fahrenheit':
            return (temp_c * 9/5) + 32
        elif to_unit == 'kelvin':
            return temp_c + 273.15
        return temp_c
    
    def update_max_points(self):
        self.max_points = self.max_points_var.get()
        # Actualizar todos los deques
        for i in range(4):
            sensor_key = f'sensor{i}'
            for key in ['temp_c', 'temp_f', 'temp_k', 'hum', 'time']:
                old_deque = self.data[sensor_key][key]
                new_deque = deque(maxlen=self.max_points)
                # Copiar datos existentes
                for item in old_deque:
                    new_deque.append(item)
                self.data[sensor_key][key] = new_deque
    
    def update_units(self):
        unit = self.temp_unit_var.get()
        unit_symbol = self.unit_labels[unit][0]
        unit_title = self.unit_labels[unit][1]
        
        # Actualizar etiquetas
        self.unit_label.config(text=f"Unidad: {unit_title}")
        
        # Actualizar gráfico de temperatura
        self.axes[0].set_title(unit_title)
        self.axes[0].set_ylabel(f'Temperatura ({unit_symbol})')
        
        # Actualizar símbolos en los labels de sensores
        for labels in self.sensor_labels:
            labels['temp_symbol'].config(text=unit_symbol)
        
        # Actualizar valores mostrados
        self.update_display()
        
        # Redibujar canvas
        self.canvas.draw()
    
    def convert_existing_data(self):
        if messagebox.askyesno("Convertir Datos", 
                              "¿Convertir todos los datos existentes a la nueva unidad?\n"
                              "Esto afectará solo la visualización, no los datos originales."):
            
            unit = self.temp_unit_var.get()
            for i in range(4):
                sensor_key = f'sensor{i}'
                temp_c_list = list(self.data[sensor_key]['temp_c'])
                
                self.data[sensor_key]['temp_f'].clear()
                self.data[sensor_key]['temp_k'].clear()
                
                for temp_c in temp_c_list:
                    temp_f = self.convert_temperature(temp_c, 'fahrenheit')
                    temp_k = self.convert_temperature(temp_c, 'kelvin')
                    self.data[sensor_key]['temp_f'].append(temp_f)
                    self.data[sensor_key]['temp_k'].append(temp_k)
            
            # Actualizar display y gráficos
            self.update_display()
            self.update_plot(0)
            self.canvas.draw()
            
            messagebox.showinfo("Conversión", "Datos convertidos exitosamente.")
    
    def find_serial_ports(self):
        ports = []
        if sys.platform.startswith('win'):
            # Windows
            for i in range(1, 21):
                port = f'COM{i}'
                try:
                    s = serial.Serial(port)
                    s.close()
                    ports.append(port)
                except:
                    pass
        elif sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
            # Linux y Mac
            import glob
            ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
        
        self.port_combo['values'] = ports
        if ports:
            self.port_var.set(ports[0])
    
    def start_monitoring(self):
        if not self.port_var.get():
            messagebox.showerror("Error", "Selecciona un puerto COM")
            return
        
        if self.is_running:
            return
        
        try:
            # Conectar al puerto serial
            self.serial_port = serial.Serial(
                port=self.port_var.get(),
                baudrate=int(self.baudrate_var.get()),
                timeout=1
            )
            
            # Configurar archivo CSV
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.csv_file = f"sensor_data_{timestamp}.csv"
            
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'sensor_id', 'temperature_c', 
                               'temperature_f', 'temperature_k', 'humidity', 'arduino_time'])
            
            # Limpiar datos anteriores
            for i in range(4):
                sensor_key = f'sensor{i}'
                for key in self.data[sensor_key]:
                    self.data[sensor_key][key].clear()
            
            # Actualizar estado
            self.is_running = True
            self.is_paused = False
            self.data_count = 0
            
            # Actualizar interfaz
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="Estado: Conectado y monitoreando")
            self.file_label.config(text=f"Archivo: {self.csv_file}")
            
            # Actualizar unidades display
            self.update_units()
            
            # Iniciar hilos
            self.serial_thread = threading.Thread(target=self.read_serial_data, daemon=True)
            self.serial_thread.start()
            
            self.update_thread = threading.Thread(target=self.update_data, daemon=True)
            self.update_thread.start()
            
            # Iniciar animación de gráficos
            self.animation = animation.FuncAnimation(
                self.fig, 
                self.update_plot, 
                interval=1000,
                cache_frame_data=False,
                blit=False
            )
            
            self.canvas.draw()
            
            messagebox.showinfo("Éxito", f"Monitoreo iniciado en {self.port_var.get()}\n"
                                      f"Unidad: {self.temp_unit_var.get().title()}")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar: {str(e)}")
    
    def pause_monitoring(self):
        """Pausar/reanudar el monitoreo"""
        if not self.is_running:
            return
        
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.pause_button.config(text="▶️  Reanudar")
            self.status_label.config(text="Estado: Pausado")
        else:
            self.pause_button.config(text="⏸️  Pausar")
            self.status_label.config(text="Estado: Monitoreando")
    
    def stop_monitoring(self):
        """Detener el monitoreo"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.is_paused = False
        
        # Cerrar puerto serial
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        
        # Actualizar interfaz
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        self.pause_button.config(text="⏸️  Pausar")
        self.status_label.config(text="Estado: Detenido")
        
        # Detener animación
        if hasattr(self, 'animation'):
            self.animation.event_source.stop()
        
        messagebox.showinfo("Información", "Monitoreo detenido")
    
    def reset_graphs(self):
        """Reiniciar los gráficos"""
        if messagebox.askyesno("Reiniciar Gráficos", 
                              "¿Estás seguro de que quieres reiniciar los gráficos?\n"
                              "Esto borrará todos los datos visualizados pero no los del archivo CSV."):
            # Limpiar datos
            for i in range(4):
                sensor_key = f'sensor{i}'
                for key in self.data[sensor_key]:
                    self.data[sensor_key][key].clear()
            
            # Resetear contador
            self.data_count = 0
            self.data_count_label.config(text="Datos recibidos: 0")
            
            # Actualizar display
            self.update_display()
            
            # Limpiar gráficos
            for line in self.lines_temp + self.lines_hum:
                line.set_data([], [])
            
            # Redibujar
            self.canvas.draw()
            
            messagebox.showinfo("Reiniciado", "Gráficos reiniciados exitosamente.")
    
    def read_serial_data(self):
        """Leer datos del puerto serial en un hilo separado"""
        while self.is_running:
            if not self.is_paused and self.serial_port and self.serial_port.in_waiting:
                try:
                    line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self.data_queue.put(line)
                except:
                    pass
            time.sleep(0.01)
    
    def update_data(self):
        """Procesar datos recibidos"""
        while self.is_running:
            try:
                # Procesar todos los datos en la cola
                while not self.data_queue.empty():
                    line = self.data_queue.get_nowait()
                    self.process_data(line)
                
                # Actualizar interfaz
                self.root.after(100, self.update_display)
                
            except:
                pass
            
            time.sleep(0.1)
    
    def process_data(self, line):
        """Procesar una línea de datos"""
        try:
            parts = line.strip().split(',')
            if len(parts) == 4:
                sensor_id = int(parts[0])
                temperature_c = float(parts[1])  # El Arduino envía en Celsius
                humidity = float(parts[2])
                arduino_time = int(parts[3])
                
                timestamp = datetime.now()
                
                # Calcular conversiones
                temperature_f = self.convert_temperature(temperature_c, 'fahrenheit')
                temperature_k = self.convert_temperature(temperature_c, 'kelvin')
                
                # Almacenar datos
                sensor_key = f'sensor{sensor_id}'
                self.data[sensor_key]['temp_c'].append(temperature_c)
                self.data[sensor_key]['temp_f'].append(temperature_f)
                self.data[sensor_key]['temp_k'].append(temperature_k)
                self.data[sensor_key]['hum'].append(humidity)
                self.data[sensor_key]['time'].append(timestamp)
                
                # Guardar en CSV (todas las unidades)
                if self.csv_file:
                    with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'),
                            sensor_id,
                            f"{temperature_c:.2f}",
                            f"{temperature_f:.2f}",
                            f"{temperature_k:.2f}",
                            f"{humidity:.2f}",
                            arduino_time
                        ])
                
                # Actualizar contador
                self.data_count += 1
                
        except Exception as e:
            print(f"Error procesando datos: {e}")
    
    def update_plot(self, frame):
        """Actualizar gráficos"""
        if self.is_paused:
            return self.lines_temp + self.lines_hum
        
        try:
            current_unit = self.temp_unit_var.get()
            temp_key = f'temp_{current_unit[0]}'  # 'temp_c', 'temp_f', 'temp_k'
            
            for sensor_idx in range(4):
                sensor_key = f'sensor{sensor_idx}'
                
                if len(self.data[sensor_key]['time']) > 0:
                    times = list(self.data[sensor_key]['time'])
                    temps = list(self.data[sensor_key][temp_key])
                    hums = list(self.data[sensor_key]['hum'])
                    
                    # Tiempo relativo
                    if len(times) > 0:
                        first_time = times[0]
                        rel_times = [(t - first_time).total_seconds() for t in times]
                        
                        # Actualizar líneas
                        self.lines_temp[sensor_idx].set_data(rel_times, temps)
                        self.lines_hum[sensor_idx].set_data(rel_times, hums)
            
            # Autoajustar ejes
            for ax in self.axes:
                ax.relim()
                ax.autoscale_view()
            
        except Exception as e:
            print(f"Error actualizando gráficos: {e}")
        
        return self.lines_temp + self.lines_hum
    
    def update_display(self):
        """Actualizar la interfaz"""
        # Actualizar contador
        self.data_count_label.config(text=f"Datos recibidos: {self.data_count}")
        
        # Obtener unidad actual
        current_unit = self.temp_unit_var.get()
        temp_key = f'temp_{current_unit[0]}'  # 'temp_c', 'temp_f', 'temp_k'
        
        # Actualizar valores de sensores
        for sensor_idx in range(4):
            sensor_key = f'sensor{sensor_idx}'
            labels = self.sensor_labels[sensor_idx]
            
            if len(self.data[sensor_key]['time']) > 0:
                temp = self.data[sensor_key][temp_key][-1]
                hum = self.data[sensor_key]['hum'][-1]
                last_time = self.data[sensor_key]['time'][-1]
                
                if not pd.isna(temp) and not pd.isna(hum):
                    # Actualizar temperatura con formato según unidad
                    if current_unit == 'kelvin':
                        temp_text = f"{temp:.1f}"
                    else:
                        temp_text = f"{temp:.1f}"
                    
                    labels['temp_value'].config(text=temp_text)
                    labels['hum_value'].config(text=f"{hum:.1f}")
                    labels['time'].config(text=f"Última: {last_time.strftime('%H:%M:%S')}")
                else:
                    labels['temp_value'].config(text="--")
                    labels['hum_value'].config(text="--")
                    labels['time'].config(text="Última: --:--:--")
    
    def save_data(self):
        """Guardar datos en un archivo seleccionado por el usuario"""
        if not hasattr(self, 'csv_file') or not self.csv_file:
            messagebox.showwarning("Advertencia", "No hay datos para guardar")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"sensor_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            
            if filename:
                import shutil
                shutil.copy2(self.csv_file, filename)
                messagebox.showinfo("Éxito", f"Datos guardados en:\n{filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {str(e)}")
    
    def show_report(self):
        """Mostrar reporte de datos"""
        try:
            report_window = tk.Toplevel(self.root)
            report_window.title("Reporte de Datos - Multiunidades")
            report_window.geometry("700x500")
            
            # Frame principal del reporte
            report_frame = ttk.Frame(report_window, padding="10")
            report_frame.pack(fill=tk.BOTH, expand=True)
            
            # Notebook para pestañas
            notebook = ttk.Notebook(report_frame)
            notebook.pack(fill=tk.BOTH, expand=True)
            
            # Pestaña de resumen
            summary_frame = ttk.Frame(notebook)
            notebook.add(summary_frame, text="📊 Resumen")
            
            # Text widget para el resumen
            summary_text = tk.Text(summary_frame, wrap=tk.WORD, padx=10, pady=10, font=("Consolas", 10))
            summary_text.pack(fill=tk.BOTH, expand=True)
            
            # Generar reporte de resumen
            report_text = " "*50 + "\n"
            report_text += "REPORTE DE DATOS DE SENSORES - MULTIUNIDADES\n"
            report_text = "-"*50 + "\n"
            
            report_text += f" Fecha del reporte: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report_text += f" Archivo de datos: {self.csv_file if hasattr(self, 'csv_file') else 'No disponible'}\n"
            report_text += f" Datos recibidos: {self.data_count if hasattr(self, 'data_count') else 0}\n"
            report_text += f" Unidad actual: {self.temp_unit_var.get().title()}\n"
            report_text += f" Estado: {'En ejecución' if self.is_running else 'Detenido'}\n"
            
            # Pestaña de datos por sensor
            for sensor_idx in range(4):
                sensor_frame = ttk.Frame(notebook)
                sensor_name = f"Sensor {sensor_idx}" if sensor_idx > 0 else "Sensor Local"
                notebook.add(sensor_frame, text=f"🔹 {sensor_name}")
                
                sensor_text = tk.Text(sensor_frame, wrap=tk.WORD, padx=10, pady=10, font=("Consolas", 9))
                sensor_text.pack(fill=tk.BOTH, expand=True)
                
                sensor_key = f'sensor{sensor_idx}'
                temps_c = list(self.data[sensor_key]['temp_c'])
                temps_f = list(self.data[sensor_key]['temp_f'])
                temps_k = list(self.data[sensor_key]['temp_k'])
                hums = list(self.data[sensor_key]['hum'])
                
                # Filtrar valores válidos
                valid_temps_c = [t for t in temps_c if not pd.isna(t)]
                valid_hums = [h for h in hums if not pd.isna(h)]
                
                sensor_report = f"{sensor_name}\n"
                sensor_report += "-"*50 + "\n\n"
                
                if valid_temps_c:
                    # Estadísticas en Celsius
                    sensor_report += " ESTADÍSTICAS EN CELSIUS:\n"
                    sensor_report += f"   Mínima: {min(valid_temps_c):.1f} °C\n"
                    sensor_report += f"   Máxima: {max(valid_temps_c):.1f} °C\n"
                    sensor_report += f"   Promedio: {sum(valid_temps_c)/len(valid_temps_c):.1f} °C\n\n"
                    
                    # Conversiones
                    if valid_temps_c:
                        temp_c_avg = sum(valid_temps_c)/len(valid_temps_c)
                        temp_f_avg = self.convert_temperature(temp_c_avg, 'fahrenheit')
                        temp_k_avg = self.convert_temperature(temp_c_avg, 'kelvin')
                        
                        sensor_report += " CONVERSIONES DEL PROMEDIO:\n"
                        sensor_report += f"   Fahrenheit: {temp_f_avg:.1f} °F\n"
                        sensor_report += f"   Kelvin: {temp_k_avg:.1f} K\n\n"
                    
                    # Humedad
                    sensor_report += " HUMEDAD:\n"
                    sensor_report += f"   Mínima: {min(valid_hums):.1f} %\n"
                    sensor_report += f"   Máxima: {max(valid_hums):.1f} %\n"
                    sensor_report += f"   Promedio: {sum(valid_hums)/len(valid_hums):.1f} %\n\n"
                    
                    sensor_report += f" Lecturas válidas: {len(valid_temps_c)}\n"
                else:
                    sensor_report += "Sin datos válidos\n"
                
                sensor_text.insert(1.0, sensor_report)
                sensor_text.config(state=tk.DISABLED)
            
            # Insertar texto en el widget de resumen
            summary_text.insert(1.0, report_text)
            summary_text.config(state=tk.DISABLED)
            
            # Frame para botones
            button_frame = ttk.Frame(report_frame)
            button_frame.pack(pady=10)
            
            # Botón para exportar
            ttk.Button(button_frame, text=" Exportar Reporte", 
                      command=lambda: self.export_report(report_window)).pack(side=tk.LEFT, padx=5)
            
            # Botón para cerrar
            ttk.Button(button_frame, text="Cerrar", 
                      command=report_window.destroy).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el reporte: {str(e)}")
    
    def export_report(self, parent_window):
        
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=f"reporte_sensores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("REPORTE DE DATOS DE SENSORES - MULTIUNIDADES\n")
                    f.write("="*60 + "\n\n")
                    f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Archivo CSV: {self.csv_file if hasattr(self, 'csv_file') else 'N/A'}\n")
                    f.write(f"Datos recibidos: {self.data_count}\n")
                    f.write(f"Unidad actual: {self.temp_unit_var.get().title()}\n\n")
                    
                    for i in range(4):
                        sensor_key = f'sensor{i}'
                        sensor_name = f"Sensor {i}" if i > 0 else "Sensor Local"
                        
                        temps_c = list(self.data[sensor_key]['temp_c'])
                        hums = list(self.data[sensor_key]['hum'])
                        
                        valid_temps_c = [t for t in temps_c if not pd.isna(t)]
                        valid_hums = [h for h in hums if not pd.isna(h)]
                        
                        f.write(f"\n{sensor_name}\n")
                        f.write("-"*40 + "\n")
                        
                        if valid_temps_c:
                            f.write(f"Celsius: Min={min(valid_temps_c):.1f}°C, "
                                   f"Max={max(valid_temps_c):.1f}°C, "
                                   f"Avg={sum(valid_temps_c)/len(valid_temps_c):.1f}°C\n")
                            f.write(f"Humedad: Min={min(valid_hums):.1f}%, "
                                   f"Max={max(valid_hums):.1f}%, "
                                   f"Avg={sum(valid_hums)/len(valid_hums):.1f}%\n")
                            f.write(f"Lecturas: {len(valid_temps_c)}\n")
                        else:
                            f.write("Sin datos válidos\n")
                
                messagebox.showinfo("Éxito", f"Reporte exportado a:\n{filename}")
                parent_window.destroy()
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {str(e)}")
   
if __name__ == "__main__":
    root = tk.Tk()
    app = SensorMonitorGUI(root)
    root.mainloop()