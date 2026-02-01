import serial
import csv
import time
from datetime import datetime, timedelta
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
        self.root.title("ThermoHumid Tracker")
        
        # Variables de control
        self.is_running = False
        self.is_paused = False
        self.serial_port = None
        self.data_queue = queue.Queue()
        self.fullscreen_window = None  
        self.fullscreen_animation = None  
        
        # Variables de datos
        self.time_window = 3600  
        self.monitoring_duration = 3600  
        self.start_time = None 
        self.elapsed_time = 0  
        
        self.window_mode = 'auto'  
        
        self.data = {
            'sensor0': {'temp_c': deque(), 'temp_f': deque(), 'temp_k': deque(), 'hum': deque(), 
                       'rel_time': deque()},
            'sensor1': {'temp_c': deque(), 'temp_f': deque(), 'temp_k': deque(), 'hum': deque(), 
                         'rel_time': deque()},
            'sensor2': {'temp_c': deque(), 'temp_f': deque(), 'temp_k': deque(), 'hum': deque(), 
                          'rel_time': deque()},
            'sensor3': {'temp_c': deque(),  'temp_f': deque(),  'temp_k': deque(),  'hum': deque(), 
                       'rel_time': deque()},
        }
        
        # Variables de configuración
        self.port_var = tk.StringVar()
        self.baudrate_var = tk.StringVar(value="9600")
        
        # Variables para tiempo de visualización
        self.time_window_hours = tk.IntVar(value=1)
        self.time_window_minutes = tk.IntVar(value=0)
        self.time_window_seconds = tk.IntVar(value=0)
        
        # Variables para duración del monitoreo
        self.monitor_hours = tk.IntVar(value=1)
        self.monitor_minutes = tk.IntVar(value=0)
        self.monitor_seconds = tk.IntVar(value=0)
        
        # Variable para modo de ventana
        self.window_mode_var = tk.StringVar(value="auto")  
        
        self.temp_unit_var = tk.StringVar(value="celsius") 
        self.csv_file = None
        
        # Variables para control de gráficos
        self.selected_sensors = [tk.BooleanVar(value=True) for _ in range(4)]
        
        self.fullscreen_selected_sensors = None
        
        self.unit_labels = {
            'celsius': ('°C', 'Temperatura (°C)'),
            'fahrenheit': ('°F', 'Temperatura (°F)'),
            'kelvin': ('K', 'Temperatura (K)')
        }
        
        # Contador de datos
        self.data_count = 0
        
        self.monitor_timer = None
        self.elapsed_timer = None
        
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
                  command=self.find_serial_ports, width=15,cursor="hand2").grid(row=0, column=2, padx=(0, 15), pady=5, sticky=tk.W)
        
        # Baudrate
        ttk.Label(control_frame, text="Baudrate:").grid(row=0, column=3, padx=(0, 5), pady=5, sticky=tk.W)
        baudrates = ["9600", "19200", "38400", "57600", "115200"]
        baudrate_combo = ttk.Combobox(control_frame, textvariable=self.baudrate_var, 
                                     values=baudrates, width=10, state="readonly")
        baudrate_combo.grid(row=0, column=4, padx=(0, 15), pady=5, sticky=tk.W)
        
        # Frame para controles de tiempo de visualización
        time_frame = ttk.Frame(control_frame)
        time_frame.grid(row=1, column=1, columnspan=7, sticky=tk.W, pady=5)

        
        self.time_window_label = ttk.Label(control_frame, text="")
        self.time_window_label.grid(row=1, column=5, padx=(15, 0), pady=5, sticky=tk.W)
        

        
        # Duración del monitoreo
        ttk.Label(control_frame, text="Duración monitoreo:").grid(row=1, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        
        # Frame para controles de duración de monitoreo
        monitor_frame = ttk.Frame(control_frame)
        monitor_frame.grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=5)
        
        # Horas
        ttk.Label(monitor_frame, text="H:").grid(row=0, column=0, padx=(0, 2))
        self.monitor_hours_spin = ttk.Spinbox(monitor_frame, from_=0, to=24, textvariable=self.monitor_hours, 
                                        width=4)
        self.monitor_hours_spin.grid(row=0, column=1, padx=(0, 5))
        
        # Minutos
        ttk.Label(monitor_frame, text="M:").grid(row=0, column=2, padx=(0, 2))
        self.monitor_minutes_spin = ttk.Spinbox(monitor_frame, from_=0, to=59, textvariable=self.monitor_minutes, 
                                          width=4)
        self.monitor_minutes_spin.grid(row=0, column=3, padx=(0, 5))
        
        # Segundos
        ttk.Label(monitor_frame, text="S:").grid(row=0, column=4, padx=(0, 2))
        self.monitor_seconds_spin = ttk.Spinbox(monitor_frame, from_=0, to=59, textvariable=self.monitor_seconds, 
                                          width=4)
        self.monitor_seconds_spin.grid(row=0, column=5, padx=(0, 5))
        
        # Etiqueta que muestra la duración total del monitoreo
        self.monitor_duration_label = ttk.Label(control_frame, text="Duración: 1 hora")
        self.monitor_duration_label.grid(row=0, column=5, padx=(15, 0), pady=5, sticky=tk.W)
        
        # Botón para aplicar duración del monitoreo
        self.apply_duration_btn = ttk.Button(control_frame, text="Aplicar Duración", 
                  command=self.update_monitor_duration, width=15)
        self.apply_duration_btn.grid(row=0, column=6, padx=(5, 0), pady=5)
        
        # Frame de configuración de unidades
        unit_frame = ttk.LabelFrame(main_frame, text="Unidades de Temperatura",style="My.TLabelframe", padding="10")
        unit_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Botones de radio para unidades
        ttk.Radiobutton(unit_frame, text="Celsius (°C)", 
                       variable=self.temp_unit_var, 
                       value="celsius",
                       command=self.update_units,cursor="hand2").grid(row=0, column=0, padx=10)
        
        ttk.Radiobutton(unit_frame, text="Fahrenheit (°F)", 
                       variable=self.temp_unit_var, 
                       value="fahrenheit",
                       command=self.update_units,cursor="hand2").grid(row=0, column=1, padx=10)
        
        ttk.Radiobutton(unit_frame, text="Kelvin (K)", 
                       variable=self.temp_unit_var, 
                       value="kelvin",
                       command=self.update_units,cursor="hand2").grid(row=0, column=2, padx=10)
        
        # Frame de botones de control
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=4, pady=(0, 10))
        
        # Botones de control
        self.start_button = ttk.Button(button_frame, text="▶️ Comenzar", 
                                      command=self.start_monitoring, width=15,cursor="hand2")
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.pause_button = ttk.Button(button_frame, text="⏸️ Pausar", 
                                      command=self.pause_monitoring, width=15, state=tk.DISABLED,cursor="hand2")
        self.pause_button.grid(row=0, column=1, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ Detener", 
                                     command=self.stop_monitoring, width=15, state=tk.DISABLED,cursor="hand2")
        self.stop_button.grid(row=0, column=2, padx=5)

        ttk.Button(button_frame, text="↺ Reiniciar Gráficos", 
                  command=self.reset_graphs, width=15,cursor="hand2").grid(row=0, column=3, padx=5)
        
        ttk.Button(button_frame, text="🔄 Reiniciar Todo", 
                  command=self.restart_all, width=15,cursor="hand2").grid(row=0, column=7, padx=5)
        
        ttk.Button(button_frame, text="💾 Guardar Datos", 
                  command=self.save_data, width=15,cursor="hand2").grid(row=0, column=4, padx=5)
        
        ttk.Button(button_frame, text="📊 Ver Reporte", 
                  command=self.show_report, width=15,cursor="hand2").grid(row=0, column=5, padx=5)
        
        # Botón pantalla completa
        self.fullscreen_btn = ttk.Button(button_frame, text="⛶ Pantalla Completa", 
                                        command=self.toggle_fullscreen, width=15,cursor="hand2")
        self.fullscreen_btn.grid(row=0, column=6, padx=5)
        
        # Frame de información
        info_frame = ttk.LabelFrame(main_frame, text="Información del Sistema", style="My.TLabelframe", padding="10")
        info_frame.grid(row=6, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Labels de información
        self.status_label = ttk.Label(info_frame, text="Estado: Desconectado")
        self.status_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        self.data_count_label = ttk.Label(info_frame, text="Datos recibidos: 0")
        self.data_count_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        self.unit_label = ttk.Label(info_frame, text="Unidad: Celsius (°C)")
        self.unit_label.grid(row=0, column=2, sticky=tk.W, padx=(0, 20))
    
        # Tiempo transcurrido
        self.elapsed_time_label = ttk.Label(info_frame, text="Tiempo: 00:00:00")
        self.elapsed_time_label.grid(row=0, column=4, sticky=tk.W, padx=(0, 20))
        
        # Frame de valores actuales
        values_frame = ttk.LabelFrame(main_frame, text="Valores Actuales",style="My.TLabelframe", padding="10")
        values_frame.grid(row=7, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
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
            
            # Frame para header con checkbox y nombre
            header_frame = ttk.Frame(sensor_frame)
            header_frame.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
            
            # Checkbox para seleccionar sensor
            sensor_check = ttk.Checkbutton(header_frame, 
                                          variable=self.selected_sensors[i],
                                          command=self.update_sensor_display)
            sensor_check.grid(row=0, column=0, padx=(0, 5))
            
            sensor_name = f"Sensor {i}" if i > 0 else "Sensor Local"
            name_label = ttk.Label(header_frame, text=f" {sensor_name}", 
                                  font=("Arial", 12, "bold"))
            name_label.grid(row=0, column=1, sticky=tk.W)
            
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
        
        # Frame de controles de gráficos
        graph_controls_frame = ttk.LabelFrame(main_frame, text="Controles de Gráficos", style="My.TLabelframe", padding="10")
        graph_controls_frame.grid(row=8, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Controles rápidos de sensores
        sensor_controls_frame = ttk.Frame(graph_controls_frame)
        sensor_controls_frame.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        
        # Botones de control de matplotlib
        toolbar_frame = ttk.Frame(graph_controls_frame)
        toolbar_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # Botones personalizados para controles de matplotlib
        ttk.Button(toolbar_frame, text="📐 Zoom", 
                  command=self.toggle_zoom_mode, width=10).grid(row=0, column=0, padx=(0, 5))
        
        ttk.Button(toolbar_frame, text="✋ Pan", 
                  command=self.toggle_pan_mode, width=10).grid(row=0, column=1, padx=(0, 5))
        
        ttk.Button(toolbar_frame, text="🏠 Restaurar Vista", 
                  command=self.reset_view, width=15).grid(row=0, column=2, padx=(0, 5))
        
        ttk.Button(toolbar_frame, text="💾 Guardar Gráfico", 
                  command=self.save_figure, width=15).grid(row=0, column=3, padx=(0, 5))
        
        ttk.Button(toolbar_frame, text="🔄 Actualizar Gráficos", 
                  command=self.refresh_plots, width=15).grid(row=0, column=4, padx=(0, 5))
           
        # Configurar expansión del frame principal
        main_frame.rowconfigure(9, weight=1)
        
    def setup_plots(self):
        # Crear figura con 2 subplots
        self.fig, self.axes = plt.subplots(2, 1, figsize=(12, 6))
        
        # Configurar los gráficos con unidades iniciales
        current_unit = self.temp_unit_var.get()
        unit_symbol = self.unit_labels[current_unit][0]
        unit_title = self.unit_labels[current_unit][1]
        
        self.axes[0].set_title(f'{unit_title} vs Tiempo')
        self.axes[0].set_ylabel(f'Temperatura ({unit_symbol}) ')
        self.axes[0].grid(True, alpha=0.3)
        
        self.axes[1].set_title('Humedad vs Tiempo')
        self.axes[1].set_xlabel('Tiempo (s)',fontsize=10)
        self.axes[1].set_ylabel('Humedad (%)')
        self.axes[1].grid(True, alpha=0.3)
        
        self.colors = ['#1f77b4', "#0019FC", '#d62728', '#9467bd'] 
        self.lines_temp = []
        self.lines_hum = []
        
        # Crear líneas para cada sensor (inicialmente todas visibles)
        for i in range(4):
            line_temp, = self.axes[0].plot([], [], 
                                         color=self.colors[i],
                                         marker='o', 
                                         markersize=5, 
                                         linewidth=2.5,
                                         alpha=0.8,
                                         label=f'Sensor {i}' if i > 0 else 'Sensor Local',
                                         visible=self.selected_sensors[i].get())
            
            line_hum, = self.axes[1].plot([], [], 
                                        color=self.colors[i],
                                        marker='s', 
                                        markersize=5, 
                                        linewidth=2.5,
                                        alpha=0.8,
                                        label=f'Sensor {i}' if i > 0 else 'Sensor Local',
                                        visible=self.selected_sensors[i].get())
            
            self.lines_temp.append(line_temp)
            self.lines_hum.append(line_hum)
        
        # Agregar leyendas
        self.axes[0].legend(loc='upper right', fontsize=9)
        self.axes[1].legend(loc='upper right', fontsize=9)
        
        # Configurar límites iniciales del eje X
        self.axes[0].set_xlim(0, self.time_window)
        self.axes[1].set_xlim(0, self.time_window)
        
        plt.tight_layout()
        
        # Integrar matplotlib con tkinter
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas_widget = self.canvas.get_tk_widget()
        
        # Agregar toolbar de matplotlib
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.root, pack_toolbar=False)
        self.toolbar.update()
        
        # Buscar el main_frame para insertar el canvas
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                # Colocar toolbar y canvas
                self.toolbar.grid(row=12, column=0, columnspan=4, sticky=(tk.W, tk.E), padx=10)
                self.canvas_widget.grid(row=11, column=0, columnspan=4, 
                                       sticky=(tk.W, tk.E, tk.N, tk.S), 
                                       padx=10, pady=(0, 10))
                break
        
        # Configurar expansión para el canvas
        self.root.rowconfigure(11, weight=1)
    
    def update_window_mode(self):
        
        self.window_mode = self.window_mode_var.get()
        
        if self.window_mode == 'auto':
            self.window_mode_label.config(text="Modo: Auto (se expande)")
            # Si estamos monitoreando, actualizar la ventana al tiempo actual
            if self.is_running and not self.is_paused:
                self.update_time_window_from_elapsed()
        else:
            self.window_mode_label.config(text="Modo: Fija")
        
        messagebox.showinfo("Modo de Ventana", f"Modo de ventana cambiado a: {self.window_mode}")
    
    def update_time_window_from_elapsed(self):
        if not self.is_running or self.is_paused or not self.start_time:
            return
        
        current_time = datetime.now()
        elapsed = (current_time - self.start_time).total_seconds()
        
        # En modo auto, la ventana es igual al tiempo transcurrido (sin exceder la duración del monitoreo)
        if self.window_mode == 'auto':
            new_window = min(elapsed, self.monitoring_duration)
            
            # Solo actualizar si ha cambiado significativamente
            if abs(new_window - self.time_window) > 1:
                self.time_window = new_window
                
                # Actualizar spinboxes
                hours = int(new_window // 3600)
                minutes = int((new_window % 3600) // 60)
                seconds = int(new_window % 60)
                
                self.time_window_hours.set(hours)
                self.time_window_minutes.set(minutes)
                self.time_window_seconds.set(seconds)
                
               
                # Actualizar límites de los gráficos
                self.axes[0].set_xlim(0, self.time_window)
                self.axes[1].set_xlim(0, self.time_window)
                
                self.canvas.draw()
                
                # Actualizar gráficos en pantalla completa si están activos
                if hasattr(self, 'fullscreen_canvas') and self.fullscreen_canvas:
                    if hasattr(self, 'fullscreen_axes'):
                        self.fullscreen_axes[0].set_xlim(0, self.time_window)
                        self.fullscreen_axes[1].set_xlim(0, self.time_window)
                        self.fullscreen_canvas.draw()
    
    def update_monitor_duration(self):
        
        hours = self.monitor_hours.get()
        minutes = self.monitor_minutes.get()
        seconds = self.monitor_seconds.get()
        
        # Calcular tiempo total en segundos
        total_seconds = (hours * 3600) + (minutes * 60) + seconds
        
        if total_seconds <= 0:
            messagebox.showwarning("Advertencia", "La duración del monitoreo debe ser mayor a 0 segundos")
            return
        
        self.monitoring_duration = total_seconds
        
        # Actualizar etiqueta con formato legible
        if hours > 0:
            time_text = f"Duración: {hours}h"
            if minutes > 0:
                time_text += f" {minutes}m"
            if seconds > 0 and hours == 0:
                time_text += f" {seconds}s"
        elif minutes > 0:
            time_text = f"Duración: {minutes}m"
            if seconds > 0:
                time_text += f" {seconds}s"
        else:
            time_text = f"Duración: {seconds}s"
        
        self.monitor_duration_label.config(text=time_text)
        messagebox.showinfo("Duración del Monitoreo", f"Duración actualizada: {time_text}")
    
    def update_time_window(self):
       
        # En modo fijo, permitir cambiar la ventana manualmente
        if self.window_mode == 'fixed':
            hours = self.time_window_hours.get()
            minutes = self.time_window_minutes.get()
            seconds = self.time_window_seconds.get()
            
            # Calcular tiempo total en segundos
            total_seconds = (hours * 3600) + (minutes * 60) + seconds
            
            if total_seconds <= 0:
                messagebox.showwarning("Advertencia", "El tiempo debe ser mayor a 0 segundos")
                return
            
            self.time_window = total_seconds
            
            # Actualizar etiqueta con formato legible
            if hours > 0:
                time_text = f"Ventana: {hours}h"
                if minutes > 0:
                    time_text += f" {minutes}m"
                if seconds > 0 and hours == 0:
                    time_text += f" {seconds}s"
            elif minutes > 0:
                time_text = f"Ventana: {minutes}m"
                if seconds > 0:
                    time_text += f" {seconds}s"
            else:
                time_text = f"Ventana: {seconds}s"
            
            self.time_window_label.config(text=time_text)
            
            # Actualizar límites de los gráficos
            self.axes[0].set_xlim(0, self.time_window)
            self.axes[1].set_xlim(0, self.time_window)
            
            self.canvas.draw()
            
            # Actualizar gráficos en pantalla completa si están activos
            if hasattr(self, 'fullscreen_canvas') and self.fullscreen_canvas:
                if hasattr(self, 'fullscreen_axes'):
                    self.fullscreen_axes[0].set_xlim(0, self.time_window)
                    self.fullscreen_axes[1].set_xlim(0, self.time_window)
                    self.fullscreen_canvas.draw()
            
            messagebox.showinfo("Ventana de Tiempo", f"Ventana de visualización actualizada: {time_text}")
        else:
            messagebox.showwarning("Modo Auto", "En modo Auto, la ventana se ajusta automáticamente. Cambia a modo Fijo para ajustar manualmente.")
    
    def update_elapsed_time(self):
        if self.is_running and not self.is_paused and self.start_time:
            current_time = datetime.now()
            elapsed = (current_time - self.start_time).total_seconds()
            self.elapsed_time = elapsed
            
            # Formatear tiempo transcurrido
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            
            self.elapsed_time_label.config(text=f"Tiempo: {hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # En modo auto, actualizar la ventana de tiempo
            if self.window_mode == 'auto':
                self.update_time_window_from_elapsed()
            
            # Verificar si se ha superado el tiempo de monitoreo
            if elapsed >= self.monitoring_duration:
                self.auto_stop_monitoring()
                return
            
            # Programar próxima actualización en 1 segundo
            self.elapsed_timer = self.root.after(1000, self.update_elapsed_time)
    
    def start_monitor_timer(self):
        if self.monitor_timer:
            self.monitor_timer.cancel()
        
        # Programar la detención automática basada en la duración del monitoreo
        self.monitor_timer = threading.Timer(self.monitoring_duration, self.auto_stop_monitoring)
        self.monitor_timer.daemon = True
        self.monitor_timer.start()
        
        # Iniciar actualización del tiempo transcurrido
        self.update_elapsed_time()
    
    def auto_stop_monitoring(self):
        if self.is_running:
            # Usar after para ejecutar en el hilo principal de tkinter
            self.root.after(0, self.stop_monitoring)
            self.root.after(0, lambda: messagebox.showinfo("Monitoreo Completado", 
                              f"El monitoreo se ha completado automáticamente después de {self.get_time_text(self.monitoring_duration)}\n\n"
                              f"Puedes:\n"
                              f"1. Ver el reporte de datos\n"
                              f"2. Guardar los datos\n"
                              f"3. Reiniciar todo para una nueva configuración"))
            
            # Habilitar controles para nueva configuración
            self.root.after(100, self.enable_configuration_controls)
    
    def enable_configuration_controls(self):
        """Habilita los controles de configuración después de detener el monitoreo"""
        self.monitor_hours_spin.config(state='normal')
        self.monitor_minutes_spin.config(state='normal')
        self.monitor_seconds_spin.config(state='normal')
        self.apply_duration_btn.config(state='normal')
        self.port_combo.config(state='readonly')
    
    def get_time_text(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    
    def update_sensor_display(self):
        # Actualizar visibilidad de las líneas en los gráficos
        for i in range(4):
            visible = self.selected_sensors[i].get()
            self.lines_temp[i].set_visible(visible)
            self.lines_hum[i].set_visible(visible)
        
        # Actualizar leyendas para mostrar solo sensores visibles
        self.update_legends()
        
        # Redibujar
        self.canvas.draw()
        
        # Si hay ventana de pantalla completa, actualizar también
        if hasattr(self, 'fullscreen_canvas') and self.fullscreen_canvas:
            # Sincronizar selección con pantalla completa
            if hasattr(self, 'fullscreen_selected_sensors') and self.fullscreen_selected_sensors:
                for i in range(4):
                    self.fullscreen_selected_sensors[i].set(self.selected_sensors[i].get())
            self.fullscreen_canvas.draw()
    
    def update_legends(self):
        handles_temp, labels_temp = self.axes[0].get_legend_handles_labels()
        visible_handles_temp = [h for h, selected in zip(handles_temp, self.selected_sensors) if selected.get()]
        visible_labels_temp = [l for l, selected in zip(labels_temp, self.selected_sensors) if selected.get()]
        
        handles_hum, labels_hum = self.axes[1].get_legend_handles_labels()
        visible_handles_hum = [h for h, selected in zip(handles_hum, self.selected_sensors) if selected.get()]
        visible_labels_hum = [l for l, selected in zip(labels_hum, self.selected_sensors) if selected.get()]
        
        self.axes[0].legend(visible_handles_temp, visible_labels_temp, loc='upper right', fontsize=9)
        self.axes[1].legend(visible_handles_hum, visible_labels_hum, loc='upper right', fontsize=9)
    
    def toggle_fullscreen(self):
        if self.fullscreen_window is None or not self.fullscreen_window.winfo_exists():
            self.create_fullscreen_window()
            self.fullscreen_btn.config(text="✖ Salir Pantalla Completa")
        else:
            self.close_fullscreen_window()
            self.fullscreen_btn.config(text="⛶ Pantalla Completa")
    
    def create_fullscreen_window(self):
        self.fullscreen_window = tk.Toplevel(self.root)
        self.fullscreen_window.title("ThermoHumid Tracker")
        
        # Obtener dimensiones de la pantalla
        screen_width = self.fullscreen_window.winfo_screenwidth()
        screen_height = self.fullscreen_window.winfo_screenheight()
        
        # Configurar ventana a pantalla completa
        self.fullscreen_window.geometry(f"{screen_width}x{screen_height}")
        self.fullscreen_window.state('zoomed')  # Maximizar ventana
        
        # Frame principal
        fullscreen_frame = ttk.Frame(self.fullscreen_window)
        fullscreen_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Barra de controles superior
        controls_frame = ttk.Frame(fullscreen_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Título
        title_label = ttk.Label(controls_frame, text="📈  ThermoHumid Tracker", 
                               font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # Botón para cerrar
        close_btn = ttk.Button(controls_frame, text="✖ Cerrar", 
                              command=self.close_fullscreen_window, width=15)
        close_btn.pack(side=tk.RIGHT)
        
        # Controles de sensores
        sensors_frame = ttk.Frame(controls_frame)
        sensors_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(sensors_frame, text="Sensores:").pack(side=tk.LEFT, padx=(0, 10))
        
        # Crear checkboxes para pantalla completa (sincronizados con los principales)
        self.fullscreen_selected_sensors = [tk.BooleanVar(value=self.selected_sensors[i].get()) 
                                           for i in range(4)]
        
        for i in range(4):
            sensor_name = f"S{i}" if i > 0 else "Local"
            check = ttk.Checkbutton(sensors_frame, 
                                   text=sensor_name,
                                   variable=self.fullscreen_selected_sensors[i],
                                   command=self.update_fullscreen_sensor_display)
            check.pack(side=tk.LEFT, padx=(0, 5))
        
        # Crear figura más grande para pantalla completa
        self.fullscreen_fig, self.fullscreen_axes = plt.subplots(2, 1, figsize=(16, 10))
        
        # Configurar los gráficos con unidades actuales
        current_unit = self.temp_unit_var.get()
        unit_symbol = self.unit_labels[current_unit][0]
        unit_title = self.unit_labels[current_unit][1]
        
        self.fullscreen_axes[0].set_title(f'{unit_title} vs Tiempo', fontsize=14)
        self.fullscreen_axes[0].set_xlabel('')
        self.fullscreen_axes[0].set_ylabel(f'Temperatura ({unit_symbol})', fontsize=12)
        self.fullscreen_axes[0].grid(True, alpha=0.3)
        self.fullscreen_axes[0].tick_params(axis='both', which='major', labelsize=10)
        self.fullscreen_axes[0].set_xlim(0, self.time_window)  # Límite inicial
        
        self.fullscreen_axes[1].set_title('Humedad vs Tiempo', fontsize=14)
        self.fullscreen_axes[1].set_xlabel('Tiempo (s)', fontsize=12)
        self.fullscreen_axes[1].set_ylabel('Humedad (%)', fontsize=12)
        self.fullscreen_axes[1].grid(True, alpha=0.3)
        self.fullscreen_axes[1].tick_params(axis='both', which='major', labelsize=10)
        self.fullscreen_axes[1].set_xlim(0, self.time_window)  # Límite inicial
        
        # Crear líneas para pantalla completa (con datos actuales si existen)
        self.fullscreen_lines_temp = []
        self.fullscreen_lines_hum = []
        
        # Obtener datos actuales para inicializar las líneas
        temp_key = f'temp_{current_unit[0]}'
        
        for i in range(4):
            sensor_key = f'sensor{i}'
            times = list(self.data[sensor_key]['rel_time'])
            temps = list(self.data[sensor_key][temp_key])
            hums = list(self.data[sensor_key]['hum'])
            
            # Crear líneas con datos actuales
            line_temp, = self.fullscreen_axes[0].plot(
                times, temps,
                color=self.colors[i],
                marker='o', 
                markersize=6,
                linewidth=3,
                alpha=0.8,
                label=f'Sensor {i}' if i > 0 else 'Sensor Local',
                visible=self.fullscreen_selected_sensors[i].get()
            )
            
            line_hum, = self.fullscreen_axes[1].plot(
                times, hums,
                color=self.colors[i],
                marker='s', 
                markersize=6,
                linewidth=3,
                alpha=0.8,
                label=f'Sensor {i}' if i > 0 else 'Sensor Local',
                visible=self.fullscreen_selected_sensors[i].get()
            )
            
            self.fullscreen_lines_temp.append(line_temp)
            self.fullscreen_lines_hum.append(line_hum)
        
        # Agregar leyendas
        self.fullscreen_axes[0].legend(loc='upper right', fontsize=11)
        self.fullscreen_axes[1].legend(loc='upper right', fontsize=11)
        
        plt.tight_layout()
        
        # Integrar matplotlib con tkinter
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        
        self.fullscreen_canvas = FigureCanvasTkAgg(self.fullscreen_fig, master=fullscreen_frame)
        self.fullscreen_canvas_widget = self.fullscreen_canvas.get_tk_widget()
        
        # Agregar toolbar de matplotlib para pantalla completa
        self.fullscreen_toolbar = NavigationToolbar2Tk(self.fullscreen_canvas, fullscreen_frame, pack_toolbar=False)
        self.fullscreen_toolbar.update()
        
        # Colocar toolbar y canvas
        self.fullscreen_toolbar.pack(side=tk.TOP, fill=tk.X)
        self.fullscreen_canvas_widget.pack(fill=tk.BOTH, expand=True)
        
        # Configurar evento de cierre
        self.fullscreen_window.protocol("WM_DELETE_WINDOW", self.close_fullscreen_window)
        
        # Iniciar animación para pantalla completa
        self.fullscreen_animation = animation.FuncAnimation(
            self.fullscreen_fig, 
            self.update_fullscreen_plot, 
            interval=1000,
            cache_frame_data=False,
            blit=False
        )
        
        # Dibujar canvas inicialmente
        self.fullscreen_canvas.draw()
    
    def update_fullscreen_sensor_display(self):
        if not hasattr(self, 'fullscreen_lines_temp'):
            return
        
        # Actualizar visibilidad de las líneas
        for i in range(4):
            visible = self.fullscreen_selected_sensors[i].get()
            if i < len(self.fullscreen_lines_temp):
                self.fullscreen_lines_temp[i].set_visible(visible)
                self.fullscreen_lines_hum[i].set_visible(visible)
        
        # Actualizar leyendas
        self.update_fullscreen_legends()
        
        # Redibujar
        if hasattr(self, 'fullscreen_canvas') and self.fullscreen_canvas:
            self.fullscreen_canvas.draw()
    
    def update_fullscreen_plot(self, frame=None):
        if not hasattr(self, 'fullscreen_lines_temp') or not hasattr(self, 'fullscreen_canvas'):
            return
        
        try:
            current_unit = self.temp_unit_var.get()
            temp_key = f'temp_{current_unit[0]}'
            
            for sensor_idx in range(4):
                sensor_key = f'sensor{sensor_idx}'
                
                if len(self.data[sensor_key]['rel_time']) > 0:
                    times = list(self.data[sensor_key]['rel_time'])
                    temps = list(self.data[sensor_key][temp_key])
                    hums = list(self.data[sensor_key]['hum'])
                    
                    # Actualizar líneas solo si existen
                    if (sensor_idx < len(self.fullscreen_lines_temp) and 
                        sensor_idx < len(self.fullscreen_lines_hum)):
                        
                        if (hasattr(self, 'fullscreen_selected_sensors') and 
                            self.fullscreen_selected_sensors[sensor_idx].get()):
                            self.fullscreen_lines_temp[sensor_idx].set_data(times, temps)
                            self.fullscreen_lines_hum[sensor_idx].set_data(times, hums)
                        else:
                            self.fullscreen_lines_temp[sensor_idx].set_data([], [])
                            self.fullscreen_lines_hum[sensor_idx].set_data([], [])
            
            # Actualizar límites del eje X en modo auto
            if self.window_mode == 'auto' and hasattr(self, 'fullscreen_axes'):
                self.fullscreen_axes[0].set_xlim(0, self.time_window)
                self.fullscreen_axes[1].set_xlim(0, self.time_window)
            
            # Autoajustar ejes Y
            for ax in self.fullscreen_axes:
                ax.relim()
                ax.autoscale_view(scaley=True)
            
            # Actualizar leyendas
            self.update_fullscreen_legends()
            
            # Redibujar
            self.fullscreen_canvas.draw_idle()
            
        except Exception as e:
            print(f"Error actualizando gráficos en pantalla completa: {e}")
    
    def update_fullscreen_legends(self):
        if not hasattr(self, 'fullscreen_axes'):
            return
        
        handles_temp, labels_temp = self.fullscreen_axes[0].get_legend_handles_labels()
        handles_hum, labels_hum = self.fullscreen_axes[1].get_legend_handles_labels()
        
        # Filtrar según sensores seleccionados en pantalla completa
        if hasattr(self, 'fullscreen_selected_sensors'):
            visible_handles_temp = [h for h, selected in zip(handles_temp, self.fullscreen_selected_sensors) 
                                   if selected.get()]
            visible_labels_temp = [l for l, selected in zip(labels_temp, self.fullscreen_selected_sensors) 
                                  if selected.get()]
            
            visible_handles_hum = [h for h, selected in zip(handles_hum, self.fullscreen_selected_sensors) 
                                  if selected.get()]
            visible_labels_hum = [l for l, selected in zip(labels_hum, self.fullscreen_selected_sensors) 
                                 if selected.get()]
        else:
            visible_handles_temp = handles_temp
            visible_labels_temp = labels_temp
            visible_handles_hum = handles_hum
            visible_labels_hum = labels_hum
        
        self.fullscreen_axes[0].legend(visible_handles_temp, visible_labels_temp, 
                                      loc='upper right', fontsize=11)
        self.fullscreen_axes[1].legend(visible_handles_hum, visible_labels_hum, 
                                      loc='upper right', fontsize=11)
    
    def close_fullscreen_window(self):
        if hasattr(self, 'fullscreen_animation'):
            try:
                self.fullscreen_animation.event_source.stop()
            except:
                pass
        
        if self.fullscreen_window:
            try:
                self.fullscreen_window.destroy()
            except:
                pass
            self.fullscreen_window = None
            
        # Limpiar referencias
        if hasattr(self, 'fullscreen_fig'):
            plt.close(self.fullscreen_fig)
        
        # Limpiar atributos
        for attr in ['fullscreen_fig', 'fullscreen_axes', 'fullscreen_lines_temp', 
                     'fullscreen_lines_hum', 'fullscreen_canvas', 'fullscreen_canvas_widget',
                     'fullscreen_toolbar', 'fullscreen_selected_sensors', 'fullscreen_animation']:
            if hasattr(self, attr):
                try:
                    delattr(self, attr)
                except:
                    pass
        
        self.fullscreen_btn.config(text="⛶ Pantalla Completa")
    
    def toggle_zoom_mode(self):
        if hasattr(self, 'toolbar'):
            if 'zoom' in self.toolbar.mode:
                self.toolbar.zoom()
            else:
                self.toolbar.zoom()
    
    def toggle_pan_mode(self):
        if hasattr(self, 'toolbar'):
            if 'pan' in self.toolbar.mode:
                self.toolbar.pan()
            else:
                self.toolbar.pan()
    
    def reset_view(self):
        for ax in self.axes:
            # Mantener límites del eje X según el modo
            ax.set_xlim(0, self.time_window)
            ax.relim()
            ax.autoscale_view(scaley=True)
        self.canvas.draw()
        
        # También restaurar vista en pantalla completa si está activa
        if hasattr(self, 'fullscreen_axes') and self.fullscreen_axes:
            for ax in self.fullscreen_axes:
                ax.set_xlim(0, self.time_window)
                ax.relim()
                ax.autoscale_view(scaley=True)
            if hasattr(self, 'fullscreen_canvas'):
                self.fullscreen_canvas.draw()
    
    def save_figure(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg"),
                    ("PDF files", "*.pdf"),
                    ("SVG files", "*.svg"),
                    ("All files", "*.*")
                ],
                initialfile=f"graficos_sensores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            
            if filename:
                self.fig.savefig(filename, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Éxito", f"Gráfico guardado en:\n{filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el gráfico: {str(e)}")
    
    def refresh_plots(self):
        if hasattr(self, 'animation'):
            self.update_plot(0)
            self.canvas.draw()
            if hasattr(self, 'fullscreen_canvas') and self.fullscreen_canvas:
                self.update_fullscreen_plot()
            messagebox.showinfo("Actualizado", "Gráficos actualizados")
    
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
    
    def update_units(self):
        unit = self.temp_unit_var.get()
        unit_symbol = self.unit_labels[unit][0]
        unit_title = self.unit_labels[unit][1]
        
        # Actualizar etiquetas
        self.unit_label.config(text=f"Unidad: {unit_title}")
        
        # Actualizar gráfico de temperatura principal
        self.axes[0].set_title(unit_title)
        self.axes[0].set_ylabel(f'Temperatura ({unit_symbol})')
        
        # Actualizar gráficos en pantalla completa si están activos
        if hasattr(self, 'fullscreen_axes') and self.fullscreen_axes:
            self.fullscreen_axes[0].set_title(unit_title)
            self.fullscreen_axes[0].set_ylabel(f'Temperatura ({unit_symbol})')
        
        # Actualizar símbolos en los labels de sensores
        for labels in self.sensor_labels:
            labels['temp_symbol'].config(text=unit_symbol)
        
        # Actualizar valores mostrados
        self.update_display()
        
        # Redibujar canvas
        self.canvas.draw()
        if hasattr(self, 'fullscreen_canvas') and self.fullscreen_canvas:
            self.fullscreen_canvas.draw()
    
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
            
            # SIEMPRE crear un nuevo archivo CSV con timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.csv_file = f"sensor_data_{timestamp}.csv"
            
            # Escribir encabezados
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'sensor_id', 'temperature_c', 'humidity'])
            
            # Limpiar datos anteriores (por si no se reinició antes)
            for i in range(4):
                sensor_key = f'sensor{i}'
                for key in self.data[sensor_key]:
                    self.data[sensor_key][key].clear()
            
            # Actualizar estado
            self.is_running = True
            self.is_paused = False
            self.data_count = 0
            self.start_time = datetime.now()
            self.elapsed_time = 0
            
            # Deshabilitar controles de configuración durante el monitoreo
            self.monitor_hours_spin.config(state='disabled')
            self.monitor_minutes_spin.config(state='disabled')
            self.monitor_seconds_spin.config(state='disabled')
            self.apply_duration_btn.config(state='disabled')
            
            # Actualizar interfaz
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="Estado: Conectado y monitoreando")
            self.data_count_label.config(text="Datos recibidos: 0")
            self.elapsed_time_label.config(text="Tiempo: 00:00:00")
            
            # Actualizar unidades display
            self.update_units()
            
            # Iniciar temporizador para detención automática
            self.start_monitor_timer()
            
            # Iniciar hilos
            self.serial_thread = threading.Thread(target=self.read_serial_data, daemon=True)
            self.serial_thread.start()
            
            self.update_thread = threading.Thread(target=self.update_data, daemon=True)
            self.update_thread.start()
            
            # Iniciar animación de gráficos
            if hasattr(self, 'animation'):
                self.animation.event_source.stop()
            
            self.animation = animation.FuncAnimation(
                self.fig, 
                self.update_plot, 
                interval=1000,
                cache_frame_data=False,
                blit=False
            )
            
            self.canvas.draw()
            
            messagebox.showinfo("Éxito", f"✅ Monitoreo iniciado\n\n"
                                      f"Puerto: {self.port_var.get()}\n"
                                      f"Unidad: {self.temp_unit_var.get().title()}\n"
                                      f"Duración: {self.get_monitor_duration_text()}\n"
                                      f"Archivo: {self.csv_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar: {str(e)}")
    
    def get_time_window_text(self):
        hours = int(self.time_window // 3600)
        minutes = int((self.time_window % 3600) // 60)
        seconds = int(self.time_window % 60)
        
        if hours > 0:
            text = f"{hours}h"
            if minutes > 0:
                text += f" {minutes}m"
            if seconds > 0 and hours == 0:
                text += f" {seconds}s"
        elif minutes > 0:
            text = f"{minutes}m"
            if seconds > 0:
                text += f" {seconds}s"
        else:
            text = f"{seconds}s"
        
        return text
    
    def get_monitor_duration_text(self):
        hours = self.monitor_hours.get()
        minutes = self.monitor_minutes.get()
        seconds = self.monitor_seconds.get()
        
        if hours > 0:
            text = f"{hours}h"
            if minutes > 0:
                text += f" {minutes}m"
            if seconds > 0 and hours == 0:
                text += f" {seconds}s"
        elif minutes > 0:
            text = f"{minutes}m"
            if seconds > 0:
                text += f" {seconds}s"
        else:
            text = f"{seconds}s"
        
        return text
    
    def pause_monitoring(self):
        if not self.is_running:
            return
        
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.pause_button.config(text="▶️ Reanudar")
            self.status_label.config(text="Estado: Pausado")
            # Cancelar el temporizador de tiempo transcurrido
            if self.elapsed_timer:
                self.root.after_cancel(self.elapsed_timer)
                self.elapsed_timer = None
            # Pausar el temporizador de monitoreo
            if self.monitor_timer:
                self.monitor_timer.cancel()
                self.monitor_timer = None
        else:
            self.pause_button.config(text="⏸️ Pausar")
            self.status_label.config(text="Estado: Monitoreando")
            # Reanudar el temporizador de tiempo transcurrido
            self.update_elapsed_time()
            # Reanudar el temporizador de monitoreo con el tiempo restante
            remaining_time = self.monitoring_duration - self.elapsed_time
            if remaining_time > 0:
                self.monitor_timer = threading.Timer(remaining_time, self.auto_stop_monitoring)
                self.monitor_timer.daemon = True
                self.monitor_timer.start()
    
    def stop_monitoring(self):
        if not self.is_running:
            return
        
        self.is_running = False
        self.is_paused = False
        
        # Cancelar temporizador
        if self.monitor_timer:
            self.monitor_timer.cancel()
            self.monitor_timer = None
        
        # Cancelar temporizador de tiempo transcurrido
        if self.elapsed_timer:
            self.root.after_cancel(self.elapsed_timer)
            self.elapsed_timer = None
        
        # Habilitar controles de configuración
        self.monitor_hours_spin.config(state='normal')
        self.monitor_minutes_spin.config(state='normal')
        self.monitor_seconds_spin.config(state='normal')
        self.apply_duration_btn.config(state='normal')
        
        # Cerrar puerto serial
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        
        # Actualizar interfaz
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        self.pause_button.config(text="⏸️ Pausar")
        self.status_label.config(text="Estado: Detenido")
        
        # Detener animación principal
        if hasattr(self, 'animation'):
            self.animation.event_source.stop()
        
        # Detener animación de pantalla completa
        if hasattr(self, 'fullscreen_animation'):
            try:
                self.fullscreen_animation.event_source.stop()
            except:
                pass
        
        # Limpiar cola de datos
        while not self.data_queue.empty():
            try:
                self.data_queue.get_nowait()
            except:
                pass
        
        if hasattr(self, 'csv_file') and self.csv_file:
            messagebox.showinfo("Información", 
                              f"✅ Monitoreo detenido\n\n"
                              f"Datos guardados en:\n{self.csv_file}\n"
                              f"Datos recibidos: {self.data_count}")
        else:
            messagebox.showinfo("Información", "Monitoreo detenido")
    
    def reset_graphs(self):
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
            
            # Limpiar gráficos principales
            for line in self.lines_temp + self.lines_hum:
                line.set_data([], [])
            
            # Limpiar gráficos en pantalla completa si existen
            if hasattr(self, 'fullscreen_lines_temp'):
                for line in self.fullscreen_lines_temp + self.fullscreen_lines_hum:
                    line.set_data([], [])
            
            # Redibujar
            self.canvas.draw()
            if hasattr(self, 'fullscreen_canvas') and self.fullscreen_canvas:
                self.fullscreen_canvas.draw()
            
            messagebox.showinfo("Reiniciado", "Gráficos reiniciados exitosamente.")
    
    def restart_all(self):
        """Reinicia completamente el sistema: detiene, limpia todo y prepara para nueva sesión"""
        if messagebox.askyesno("Reiniciar Todo", 
                              "¿Estás seguro de que quieres reiniciar completamente?\n"
                              "Se detendrá el monitoreo actual y se borrarán todos los datos.\n"
                              "Se creará un nuevo archivo CSV para la próxima sesión."):
            
            # 1. Detener el monitoreo si está activo
            if self.is_running:
                self.stop_monitoring()
            
            # 2. Cerrar ventana de pantalla completa si está abierta
            if self.fullscreen_window is not None:
                self.close_fullscreen_window()
            
            # 3. Limpiar TODOS los datos
            for i in range(4):
                sensor_key = f'sensor{i}'
                for key in self.data[sensor_key]:
                    self.data[sensor_key][key].clear()
            
            # 4. Resetear todas las variables de control
            self.data_count = 0
            self.start_time = None
            self.elapsed_time = 0
            self.csv_file = None  # Esto asegura que se creará un nuevo archivo
            self.is_running = False
            self.is_paused = False
            
            # 5. Resetear la interfaz
            self.status_label.config(text="Estado: Desconectado")
            self.data_count_label.config(text="Datos recibidos: 0")
            self.elapsed_time_label.config(text="Tiempo: 00:00:00")
            
            # 6. Limpiar gráficos principales
            for line in self.lines_temp + self.lines_hum:
                line.set_data([], [])
            
            # 7. Resetear límites de gráficos
            self.time_window = 3600  # Resetear a 1 hora por defecto
            self.axes[0].set_xlim(0, self.time_window)
            self.axes[1].set_xlim(0, self.time_window)
            
            # 8. Limpiar valores de sensores en la interfaz
            for labels in self.sensor_labels:
                labels['temp_value'].config(text="--")
                labels['hum_value'].config(text="--")
                labels['time'].config(text="--")
            
            # 9. Actualizar símbolos de unidades (por si cambiaron)
            current_unit = self.temp_unit_var.get()
            unit_symbol = self.unit_labels[current_unit][0]
            for labels in self.sensor_labels:
                labels['temp_symbol'].config(text=unit_symbol)
            
            # 10. Resetear controles de botones
            self.start_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.DISABLED)
            self.pause_button.config(text="⏸️ Pausar")
            
            # 11. Habilitar todos los controles de configuración
            self.monitor_hours_spin.config(state='normal')
            self.monitor_minutes_spin.config(state='normal')
            self.monitor_seconds_spin.config(state='normal')
            self.apply_duration_btn.config(state='normal')
            
            # 12. Redibujar canvas
            self.canvas.draw()
            
            # 13. Buscar puertos disponibles nuevamente
            self.find_serial_ports()
            
            # 14. Limpiar cola de datos
            while not self.data_queue.empty():
                try:
                    self.data_queue.get_nowait()
                except:
                    pass
            
            messagebox.showinfo("Reiniciado", "✅ Sistema reiniciado completamente.\n\n"
                                            "Se ha preparado todo para una nueva sesión:\n"
                                            "• Datos anteriores borrados\n"
                                            "• Gráficos reseteados\n"
                                            "• Nuevo archivo CSV se creará al iniciar\n"
                                            "• Controles habilitados para nueva configuración")
    
    def read_serial_data(self):
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
        try:
            parts = line.strip().split(',')
            if len(parts) == 4:
                sensor_id = int(parts[0])
                temperature_c = float(parts[1]) 
                humidity = float(parts[2])
                arduino_time = int(parts[3])
                
                timestamp = datetime.now()
                
                # Calcular tiempo relativo desde el inicio
                if self.start_time:
                    rel_time = (timestamp - self.start_time).total_seconds()
                    
                    # Solo almacenar si estamos dentro del tiempo de monitoreo
                    if rel_time <= self.monitoring_duration:
                        # Calcular conversiones
                        temperature_f = self.convert_temperature(temperature_c, 'fahrenheit')
                        temperature_k = self.convert_temperature(temperature_c, 'kelvin')
                        
                        # Almacenar datos
                        sensor_key = f'sensor{sensor_id}'
                        self.data[sensor_key]['temp_c'].append(temperature_c)
                        self.data[sensor_key]['temp_f'].append(temperature_f)
                        self.data[sensor_key]['temp_k'].append(temperature_k)
                        self.data[sensor_key]['hum'].append(humidity)
                        self.data[sensor_key]['rel_time'].append(rel_time)
                        
                        # Guardar en CSV (todas las unidades)
                        if self.csv_file:
                            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                                writer = csv.writer(f)
                                writer.writerow([
                                    timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'),
                                    sensor_id,
                                    f"{temperature_c:.2f}",
                                    f"{humidity:.2f}"
                                ])
                        
                        # Actualizar contador
                        self.data_count += 1
                
        except Exception as e:
            print(f"Error procesando datos: {e}")
    
    def update_plot(self, frame):
        if self.is_paused:
            return self.lines_temp + self.lines_hum
        
        try:
            current_unit = self.temp_unit_var.get()
            temp_key = f'temp_{current_unit[0]}'  # 'temp_c', 'temp_f', 'temp_k'
            
            for sensor_idx in range(4):
                sensor_key = f'sensor{sensor_idx}'
                
                if len(self.data[sensor_key]['rel_time']) > 0:
                    times = list(self.data[sensor_key]['rel_time'])
                    temps = list(self.data[sensor_key][temp_key])
                    hums = list(self.data[sensor_key]['hum'])
                    
                    # Actualizar líneas (solo si están visibles)
                    if self.selected_sensors[sensor_idx].get():
                        self.lines_temp[sensor_idx].set_data(times, temps)
                        self.lines_hum[sensor_idx].set_data(times, hums)
                    else:
                        # Ocultar datos si el sensor no está seleccionado
                        self.lines_temp[sensor_idx].set_data([], [])
                        self.lines_hum[sensor_idx].set_data([], [])
            
            # Autoajustar ejes Y (el eje X se ajusta según el modo)
            for ax in self.axes:
                ax.relim()
                ax.autoscale_view(scaley=True)
            
            # Actualizar leyendas
            self.update_legends()
            
        except Exception as e:
            print(f"Error actualizando gráficos: {e}")
        
        return self.lines_temp + self.lines_hum
    
    def update_display(self):
        # Actualizar contador
        self.data_count_label.config(text=f"Datos recibidos: {self.data_count}")
        
        # Obtener unidad actual
        current_unit = self.temp_unit_var.get()
        temp_key = f'temp_{current_unit[0]}'  # 'temp_c', 'temp_f', 'temp_k'
        
        # Actualizar valores de sensores
        for sensor_idx in range(4):
            sensor_key = f'sensor{sensor_idx}'
            labels = self.sensor_labels[sensor_idx]
            
            if len(self.data[sensor_key]['rel_time']) > 0:
                temp = self.data[sensor_key][temp_key][-1]
                hum = self.data[sensor_key]['hum'][-1]
                last_time = self.data[sensor_key]['rel_time'][-1]
                
                if not pd.isna(temp) and not pd.isna(hum):
                    # Actualizar temperatura con formato según unidad
                    if current_unit == 'kelvin':
                        temp_text = f"{temp:.1f}"
                    else:
                        temp_text = f"{temp:.1f}"
                    
                    labels['temp_value'].config(text=temp_text)
                    labels['hum_value'].config(text=f"{hum:.1f}")
                    
                    # Mostrar tiempo relativo
                    if last_time >= 3600:
                        time_text = f"{last_time/3600:.1f}h"
                    elif last_time >= 60:
                        time_text = f"{last_time/60:.1f}m"
                    else:
                        time_text = f"{last_time:.0f}s"
                    
                    labels['time'].config(text=time_text)
                else:
                    labels['temp_value'].config(text="--")
                    labels['hum_value'].config(text="--")
                    labels['time'].config(text="--")
    
    def save_data(self):
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
            report_text += "REPORTE DE DATOS\n"
            report_text = "-"*50 + "\n"
            
            report_text += f" Fecha del reporte: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report_text += f" Archivo de datos: {self.csv_file if hasattr(self, 'csv_file') else 'No disponible'}\n"
            report_text += f" Datos recibidos: {self.data_count if hasattr(self, 'data_count') else 0}\n"
            report_text += f" Unidad actual: {self.temp_unit_var.get().title()}\n"
            report_text += f" Duración del monitoreo: {self.get_monitor_duration_text()}\n"
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
                    sensor_report += f" Tiempo total: {self.get_time_window_text()}\n"
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
                    f.write("REPORTE DE DATOS DE SENSORES\n")
                    f.write("="*60 + "\n\n")
                    f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Archivo CSV: {self.csv_file if hasattr(self, 'csv_file') else 'N/A'}\n")
                    f.write(f"Datos recibidos: {self.data_count}\n")
                    f.write(f"Unidad actual: {self.temp_unit_var.get().title()}\n")
                    f.write(f"Duración del monitoreo: {self.get_monitor_duration_text()}\n\n")
                    
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