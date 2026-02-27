import serial
import csv
import time
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font
import threading
import queue
import sys
import ctypes, os
from PIL import Image, ImageTk
from base0 import TitleFrame
from base1 import ReportManager
from base2 import SerialDataHandler

class SensorMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Esteban Andres Conde, Yosley Yael Avendaño, Juan David Ospino, Andres David Rodriguez")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        ruta = os.path.join("fonts", "Roboto.ttf")
        self.root.iconbitmap(True,Path("Logos") / "icon.ico")

        ctypes.windll.gdi32.AddFontResourceExW(ruta, 0x10, 0)

        self.scale_factor = min(screen_width / 1920, screen_height / 1080, 4.5)
    
        self.is_running = False
        self.is_paused = False
        self.serial_port = None
        self.data_queue = queue.Queue()
        self.fullscreen_window = None
        self.fullscreen_animation = None

        self.time_window = 60
        self.start_time = None
        self.elapsed_time = 0

        self.data = {
            'sensor0': {'temp_c': deque(), 'temp_f': deque(), 'temp_k': deque(), 'hum': deque(),
                       'rel_time': deque()},
            'sensor1': {'temp_c': deque(), 'temp_f': deque(), 'temp_k': deque(), 'hum': deque(),
                         'rel_time': deque()},
            'sensor2': {'temp_c': deque(), 'temp_f': deque(), 'temp_k': deque(), 'hum': deque(),
                          'rel_time': deque()},
            'sensor3': {'temp_c': deque(),  'temp_f': deque(),  'temp_k': deque(),  'hum': deque(),
                       'rel_time': deque()},
            'sensor4': {'temp_c': deque(), 'temp_f': deque(), 'temp_k': deque(), 'hum': deque(),
                       'rel_time': deque()}
        }

        self.port_var = tk.StringVar()
        self.baudrate_var = tk.StringVar(value="9600")
        self.temp_unit_var = tk.StringVar(value="celsius")
        self.csv_file = None
        self.selected_sensors = [tk.BooleanVar(value=True) for _ in range(5)]

        self.unit_labels = {
            'celsius': ('°C', 'Temperatura (°C)'),
            'fahrenheit': ('°F', 'Temperatura (°F)'),
            'kelvin': ('K', 'Temperatura (K)')
        }

        self.data_count = 0
        self.elapsed_timer = None
        self.legend_visible = True

        self.data_manager = ReportManager(self)
        self.save_data = self.data_manager.save_data
        self.show_report = self.data_manager.show_report

        self.serial_handler = SerialDataHandler(self)
        self.read_serial_data = self.serial_handler.read_serial_data
        self.update_data = self.serial_handler.update_data
        self.process_data = self.serial_handler.process_data

        self.setup_ui()
        self.setup_plots()
        self.find_serial_ports()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        # Frame principal
        self.main_frame = ttk.Frame(self.root, padding=self.scale(5))
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        style = ttk.Style()
        default_font = tk.font.nametofont("TkDefaultFont")
        default_font.configure(family="New York Semibold", size=11)
        default_size = default_font.cget("size")
        new_size = int(default_size * self.scale_factor)
        default_font.configure(size=new_size)

        # También podemos crear estilos personalizados para títulos
        style.configure("Escalado.TLabelframe.Label", font=("Arial", int(12 * self.scale_factor), "bold"))

        # Configurar expansión
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        for col in range(4):
            self.main_frame.columnconfigure(col, weight=1)

        # Título con imágenes (sin cambios porque TitleFrame probablemente ya maneja su propio escalado)
        title_frame = TitleFrame(
            self.main_frame,
            image_path1=Path("Logos") / "LogoSemillero.png",
            image_path2=Path("Logos") / "LogoFisica.png",
            image_path3=Path("Logos") / "UA.png",
            title_text="Monitor de temperatura y humedad relativa"
        )
        title_frame.grid(row=0, column=0, columnspan=4, pady=(0, self.scale(10)), sticky="ew")

        # Frame de control principal
        control_frame = ttk.LabelFrame(self.main_frame, text="Configuración Principal",
                                       style="Escalado.TLabelframe", padding=self.scale(10))
        control_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, self.scale(10)))

        ttk.Label(control_frame, text="Puerto COM:").grid(row=0, column=0, padx=(0, self.scale(5)), pady=self.scale(5), sticky=tk.W)
        self.port_combo = ttk.Combobox(control_frame, textvariable=self.port_var, width=self.scale(15))
        self.port_combo.grid(row=0, column=1, padx=(0, self.scale(15)), pady=self.scale(5), sticky=tk.W)

        ttk.Button(control_frame, text="🔍 Buscar Puertos",
                  command=self.find_serial_ports, width=self.scale(15), cursor="hand2").grid(
                      row=0, column=2, padx=(0, self.scale(15)), pady=self.scale(5), sticky=tk.W)

        ttk.Label(control_frame, text="Baudrate:").grid(row=0, column=3, padx=(0, self.scale(5)), pady=self.scale(5), sticky=tk.W)
        baudrates = ["9600", "19200", "38400", "57600", "115200"]
        baudrate_combo = ttk.Combobox(control_frame, textvariable=self.baudrate_var,
                                     values=baudrates, width=self.scale(10), state="readonly")
        baudrate_combo.grid(row=0, column=4, padx=(0, self.scale(15)), pady=self.scale(5), sticky=tk.W)

        # Frame de unidades de temperatura
        unit_frame = ttk.LabelFrame(self.main_frame, text="Unidades de Temperatura",
                                   style="Escalado.TLabelframe", padding=self.scale(10))
        unit_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, self.scale(10)))

        ttk.Radiobutton(unit_frame, text="Celsius (°C)",
                       variable=self.temp_unit_var,
                       value="celsius",
                       command=self.update_units, cursor="hand2").grid(row=0, column=0, padx=self.scale(10))
        ttk.Radiobutton(unit_frame, text="Fahrenheit (°F)",
                       variable=self.temp_unit_var,
                       value="fahrenheit",
                       command=self.update_units, cursor="hand2").grid(row=0, column=1, padx=self.scale(10))
        ttk.Radiobutton(unit_frame, text="Kelvin (K)",
                       variable=self.temp_unit_var,
                       value="kelvin",
                       command=self.update_units, cursor="hand2").grid(row=0, column=2, padx=self.scale(10))

        # Frame de botones principales
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=5, column=0, columnspan=4, pady=(0, self.scale(10)))

        self.start_button = ttk.Button(button_frame, text="▶️ Comenzar",
                                      command=self.start_monitoring, width=self.scale(15), cursor="hand2")
        self.start_button.grid(row=0, column=0, padx=self.scale(5))
        self.pause_button = ttk.Button(button_frame, text="⏸️ Pausar",
                                      command=self.pause_monitoring, width=self.scale(15), state=tk.DISABLED, cursor="hand2")
        self.pause_button.grid(row=0, column=1, padx=self.scale(5))
        self.stop_button = ttk.Button(button_frame, text="⏹️ Detener",
                                     command=self.stop_monitoring, width=self.scale(15), state=tk.DISABLED, cursor="hand2")
        self.stop_button.grid(row=0, column=2, padx=self.scale(5))
        ttk.Button(button_frame, text="Reiniciar",
                  command=self.reset_graphs, width=self.scale(15), cursor="hand2").grid(row=0, column=3, padx=self.scale(5))
        ttk.Button(button_frame, text="💾 Guardar Datos",
                  command=self.save_data, width=self.scale(15), cursor="hand2").grid(row=0, column=4, padx=self.scale(5))
        ttk.Button(button_frame, text="📊 Ver Reporte",
                  command=self.show_report, width=self.scale(15), cursor="hand2").grid(row=0, column=5, padx=self.scale(5))
        self.fullscreen_btn = ttk.Button(button_frame, text="⛶ Pantalla Completa",
                                        command=self.toggle_fullscreen, width=self.scale(20), cursor="hand2")
        self.fullscreen_btn.grid(row=0, column=6, padx=self.scale(5))

        # Frame de información del sistema
        info_frame = ttk.LabelFrame(self.main_frame, text="Información del Sistema",
                                   style="Escalado.TLabelframe", padding=self.scale(10))
        info_frame.grid(row=6, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, self.scale(10)))

        self.status_label = ttk.Label(info_frame, text="Estado: Desconectado")
        self.status_label.grid(row=0, column=0, sticky=tk.W, padx=(0, self.scale(20)))
        self.data_count_label = ttk.Label(info_frame, text="Datos recibidos: 0")
        self.data_count_label.grid(row=0, column=1, sticky=tk.W, padx=(0, self.scale(20)))
        self.unit_label = ttk.Label(info_frame, text="Unidad: Celsius (°C)")
        self.unit_label.grid(row=0, column=2, sticky=tk.W, padx=(0, self.scale(20)))
        self.elapsed_time_label = ttk.Label(info_frame, text="Tiempo: 00:00:00")
        self.elapsed_time_label.grid(row=0, column=4, sticky=tk.W, padx=(0, self.scale(20)))

        # Frame de valores actuales
        values_frame = ttk.LabelFrame(self.main_frame, text="Valores Actuales",
                                     style="Escalado.TLabelframe", padding=self.scale(5))
        values_frame.grid(row=7, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, self.scale(10)))

        for i in range(5):
            values_frame.columnconfigure(i, weight=1)

        self.sensor_labels = []
        for i in range(5):
            col = i
            row = 0
            sensor_frame = ttk.Frame(values_frame, relief=tk.RIDGE, padding=self.scale(3))
            sensor_frame.grid(row=row, column=col, padx=self.scale(2), pady=self.scale(2), sticky=(tk.W, tk.E, tk.N, tk.S))

            header_frame = ttk.Frame(sensor_frame)
            header_frame.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, self.scale(2)))

            sensor_check = ttk.Checkbutton(header_frame,
                                          variable=self.selected_sensors[i],
                                          command=self.update_sensor_display)
            sensor_check.grid(row=0, column=0, padx=(0, self.scale(2)))

            sensor_name = f"Sensor {i}" if i > 0 else "Local"
            name_label = ttk.Label(header_frame, text=f" {sensor_name}",
                                  font=("Arial", int(10 * self.scale_factor), "bold"))
            name_label.grid(row=0, column=1, sticky=tk.W)

            temp_frame = ttk.Frame(sensor_frame)
            temp_frame.grid(row=1, column=0, sticky=tk.W, pady=self.scale(1))
            ttk.Label(temp_frame, text="Temp:").grid(row=0, column=0, sticky=tk.W)
            temp_value_label = ttk.Label(temp_frame, text="--", font=("Arial", int(9 * self.scale_factor), "bold"))
            temp_value_label.grid(row=0, column=1, sticky=tk.W, padx=(self.scale(2), self.scale(2)))
            temp_symbol_label = ttk.Label(temp_frame, text="°C", font=("Arial", int(8 * self.scale_factor)))
            temp_symbol_label.grid(row=0, column=2, sticky=tk.W)

            hum_frame = ttk.Frame(sensor_frame)
            hum_frame.grid(row=2, column=0, sticky=tk.W, pady=self.scale(1))
            ttk.Label(hum_frame, text="Hum:").grid(row=0, column=0, sticky=tk.W)
            hum_value_label = ttk.Label(hum_frame, text="--", font=("Arial", int(9 * self.scale_factor), "bold"))
            hum_value_label.grid(row=0, column=1, sticky=tk.W, padx=(self.scale(2), self.scale(2)))
            ttk.Label(hum_frame, text="%", font=("Arial", int(8 * self.scale_factor))).grid(row=0, column=2, sticky=tk.W)

            time_frame = ttk.Frame(sensor_frame)
            time_frame.grid(row=3, column=0, sticky=tk.W, pady=(self.scale(2), 0))
            ttk.Label(time_frame, font=("Arial", int(7 * self.scale_factor)), foreground="gray").grid(row=0, column=0, sticky=tk.W)
            time_label = ttk.Label(time_frame, text="--", font=("Arial", int(7 * self.scale_factor), "bold"), foreground="gray")
            time_label.grid(row=0, column=1, sticky=tk.W, padx=(self.scale(2), 0))

            self.sensor_labels.append({
                'temp_value': temp_value_label,
                'temp_symbol': temp_symbol_label,
                'hum_value': hum_value_label,
                'time': time_label
            })

        # Frame de controles de gráficos
        graph_controls_frame = ttk.LabelFrame(self.main_frame, text="Controles de Gráficos",
                                            style="Escalado.TLabelframe", padding=self.scale(10))
        graph_controls_frame.grid(row=8, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, self.scale(10)))

        toolbar_frame = ttk.Frame(graph_controls_frame)
        toolbar_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(self.scale(5), 0))

        ttk.Button(toolbar_frame, text="📐 Zoom",
                  command=self.toggle_zoom_mode, width=self.scale(10)).grid(row=0, column=0, padx=(0, self.scale(5)))
        ttk.Button(toolbar_frame, text="✋ Mover",
                  command=self.toggle_pan_mode, width=self.scale(10)).grid(row=0, column=1, padx=(0, self.scale(5)))
        ttk.Button(toolbar_frame, text="🏠 Restaurar Vista",
                  command=self.reset_view, width=self.scale(17)).grid(row=0, column=2, padx=(0, self.scale(5)))
        ttk.Button(toolbar_frame, text="💾 Guardar Gráfico",
                  command=self.save_figure, width=self.scale(17)).grid(row=0, column=3, padx=(0, self.scale(5)))
        self.legend_btn = ttk.Button(toolbar_frame, text="Ocultar Leyenda",
                                      command=self.toggle_legend, width=self.scale(17))
        self.legend_btn.grid(row=0, column=5, padx=(0, self.scale(5)))

        # Configurar expansión de la fila que contendrá el canvas
        self.main_frame.rowconfigure(9, weight=1)

    def scale(self, value):
        """Aplica el factor de escala a un valor numérico (entero o flotante)."""
        if isinstance(value, (int, float)):
            return int(value * self.scale_factor)
        return value

    def setup_plots(self):
        # Crear figura sin tamaño fijo; se ajustará dinámicamente al canvas
        self.fig, self.axes = plt.subplots(2, 1)
        # Ajustar el tamaño inicial basado en el factor de escala (opcional)
        ancho_inicial = 15* self.scale_factor
        alto_inicial = 5 * self.scale_factor
        self.fig.set_size_inches(ancho_inicial, alto_inicial)

        current_unit = self.temp_unit_var.get()
        unit_symbol = self.unit_labels[current_unit][0]
        unit_title = self.unit_labels[current_unit][1]

        self.axes[0].set_title(f'{unit_title} vs Tiempo')
        self.axes[0].set_ylabel(f'Temperatura ({unit_symbol}) ')
        self.axes[0].grid(True, alpha=0.3)

        self.axes[1].set_title('Humedad vs Tiempo')
        self.axes[1].set_xlabel('Tiempo (s)', fontsize=10)
        self.axes[1].set_ylabel('Humedad (%)')
        self.axes[1].grid(True, alpha=0.3)

        self.colors = ["#000000", "#0019FC", '#d62728', "#a547fd", "#00e608"]
        self.lines_temp = []
        self.lines_hum = []

        for i in range(5):
            line_temp, = self.axes[0].plot([], [],
                                         color=self.colors[i],
                                         marker='o',
                                         markersize=self.scale(5),
                                         linewidth=2.5,
                                         alpha=0.8,
                                         label=f'Sensor {i}' if i > 0 else 'Sensor Local',
                                         visible=self.selected_sensors[i].get())
            line_hum, = self.axes[1].plot([], [],
                                        color=self.colors[i],
                                        marker='s',
                                        markersize=self.scale(5),
                                        linewidth=2.5,
                                        alpha=0.8,
                                        label=f'Sensor {i}' if i > 0 else 'Sensor Local',
                                        visible=self.selected_sensors[i].get())
            self.lines_temp.append(line_temp)
            self.lines_hum.append(line_hum)

        self.update_legends()
        self.axes[0].set_xlim(0, self.time_window)
        self.axes[1].set_xlim(0, self.time_window)
        plt.tight_layout()

        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        

        # Colocar el canvas en fila 9 (que tiene weight=1)
        self.canvas_widget.grid(row=9, column=0, columnspan=4,
                                sticky=(tk.W, tk.E, tk.N, tk.S),
                                padx=self.scale(15), pady=(0, self.scale(9)))

    def toggle_legend(self):
        self.legend_visible = not self.legend_visible

        if hasattr(self.axes[0], 'legend_') and self.axes[0].legend_ is not None:
            self.axes[0].legend_.set_visible(self.legend_visible)
        if hasattr(self.axes[1], 'legend_') and self.axes[1].legend_ is not None:
            self.axes[1].legend_.set_visible(self.legend_visible)

        if hasattr(self, 'fullscreen_axes'):
            if hasattr(self.fullscreen_axes[0], 'legend_') and self.fullscreen_axes[0].legend_ is not None:
                self.fullscreen_axes[0].legend_.set_visible(self.legend_visible)
            if hasattr(self.fullscreen_axes[1], 'legend_') and self.fullscreen_axes[1].legend_ is not None:
                self.fullscreen_axes[1].legend_.set_visible(self.legend_visible)

        self.legend_btn.config(text='Mostrar Leyenda' if not self.legend_visible else 'Ocultar Leyenda')
        self.canvas.draw()
        if hasattr(self, 'fullscreen_canvas') and self.fullscreen_canvas:
            self.fullscreen_canvas.draw()

    def update_legends(self):
        handles_temp, labels_temp = self.axes[0].get_legend_handles_labels()
        handles_hum, labels_hum = self.axes[1].get_legend_handles_labels()

        visible_handles_temp = [h for h, selected in zip(handles_temp, self.selected_sensors) if selected.get()]
        visible_labels_temp = [l for l, selected in zip(labels_temp, self.selected_sensors) if selected.get()]
        visible_handles_hum = [h for h, selected in zip(handles_hum, self.selected_sensors) if selected.get()]
        visible_labels_hum = [l for l, selected in zip(labels_hum, self.selected_sensors) if selected.get()]

        self.axes[0].legend(visible_handles_temp, visible_labels_temp, loc='upper right', fontsize=self.scale(9))
        self.axes[1].legend(visible_handles_hum, visible_labels_hum, loc='upper right', fontsize=self.scale(9))

        if hasattr(self, 'legend_visible'):
            self.axes[0].legend_.set_visible(self.legend_visible)
            self.axes[1].legend_.set_visible(self.legend_visible)

    def reset_graphs(self):
        if messagebox.askyesno("Reiniciar Gráficos",
                              "¿Estás seguro de que quieres reiniciar los gráficos?\n"
                              "Esto borrará todos los datos visualizados pero no los del archivo CSV."):
            if self.is_running:
                self.stop_monitoring()

            for i in range(5):
                sensor_key = f'sensor{i}'
                for key in self.data[sensor_key]:
                    self.data[sensor_key][key].clear()

            self.data_count = 0
            self.data_count_label.config(text="Datos recibidos: 0")
            self.elapsed_time = 0
            self.elapsed_time_label.config(text="Tiempo: 00:00:00")

            for labels in self.sensor_labels:
                labels['temp_value'].config(text="--")
                labels['hum_value'].config(text="--")
                labels['time'].config(text="--")

            for line in self.lines_temp + self.lines_hum:
                line.set_data([], [])

            if hasattr(self, 'fullscreen_lines_temp'):
                for line in self.fullscreen_lines_temp + self.fullscreen_lines_hum:
                    line.set_data([], [])

            self.time_window = 60
            self.axes[0].set_xlim(0, self.time_window)
            self.axes[1].set_xlim(0, self.time_window)

            self.canvas.draw()
            if hasattr(self, 'fullscreen_canvas') and self.fullscreen_canvas:
                self.fullscreen_canvas.draw()

            messagebox.showinfo("Reiniciado", "Gráficos reiniciados. Puedes comenzar una nueva monitorización.")

    def update_fullscreen_legends(self):
        if not hasattr(self, 'fullscreen_axes'):
            return

        handles_temp, labels_temp = self.fullscreen_axes[0].get_legend_handles_labels()
        handles_hum, labels_hum = self.fullscreen_axes[1].get_legend_handles_labels()

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
                                      loc='upper right', fontsize=self.scale(11))
        self.fullscreen_axes[1].legend(visible_handles_hum, visible_labels_hum,
                                      loc='upper right', fontsize=self.scale(11))

        if hasattr(self, 'legend_visible'):
            self.fullscreen_axes[0].legend_.set_visible(self.legend_visible)
            self.fullscreen_axes[1].legend_.set_visible(self.legend_visible)

    def update_elapsed_time(self):
        if self.is_running and not self.is_paused and self.start_time:
            current_time = datetime.now()
            elapsed = (current_time - self.start_time).total_seconds()
            self.elapsed_time = elapsed

            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)

            self.elapsed_time_label.config(text=f"Tiempo: {hours:02d}:{minutes:02d}:{seconds:02d}")

            if elapsed > self.time_window:
                self.time_window = elapsed
                self.axes[0].set_xlim(0, self.time_window)
                self.axes[1].set_xlim(0, self.time_window)
                self.canvas.draw()

                if hasattr(self, 'fullscreen_canvas') and self.fullscreen_canvas:
                    if hasattr(self, 'fullscreen_axes'):
                        self.fullscreen_axes[0].set_xlim(0, self.time_window)
                        self.fullscreen_axes[1].set_xlim(0, self.time_window)
                        self.fullscreen_canvas.draw()

            self.elapsed_timer = self.root.after(1000, self.update_elapsed_time)

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
        for i in range(5):
            visible = self.selected_sensors[i].get()
            self.lines_temp[i].set_visible(visible)
            self.lines_hum[i].set_visible(visible)

        self.update_legends()
        self.canvas.draw()

        if hasattr(self, 'fullscreen_canvas') and self.fullscreen_canvas:
            if hasattr(self, 'fullscreen_selected_sensors') and self.fullscreen_selected_sensors:
                for i in range(5):
                    self.fullscreen_selected_sensors[i].set(self.selected_sensors[i].get())
            self.fullscreen_canvas.draw()

    def toggle_fullscreen(self):
        if self.fullscreen_window is None or not self.fullscreen_window.winfo_exists():
            self.create_fullscreen_window()
            self.fullscreen_btn.config(text="✖ Salir Pantalla Completa")
        else:
            self.close_fullscreen_window()
            self.fullscreen_btn.config(text="⛶ Pantalla Completa")

    def create_fullscreen_window(self):
        self.fullscreen_window = tk.Toplevel(self.root)
        self.fullscreen_window.title("Esteban Andres Conde, Yosley Yael Avendaño, Juan David Ospino, Andres David Rodriguez")

        screen_width = self.fullscreen_window.winfo_screenwidth()
        screen_height = self.fullscreen_window.winfo_screenheight()

        self.fullscreen_window.geometry(f"{screen_width}x{screen_height}")
        self.fullscreen_window.state('zoomed')

        fullscreen_frame = ttk.Frame(self.fullscreen_window)
        fullscreen_frame.pack(fill=tk.BOTH, expand=True, padx=self.scale(10), pady=self.scale(10))

        # Configurar expansión de la fila que contendrá el canvas
        self.main_frame.rowconfigure(9, weight=1)

        controls_frame = ttk.Frame(fullscreen_frame)
        controls_frame.pack(fill=tk.X, pady=(0, self.scale(10)))

        title_label = ttk.Label(controls_frame, text="📈  Monitor de temperatura y humedad relativa",
                               font=("Arial", int(16 * self.scale_factor), "bold"))
        title_label.pack(side=tk.LEFT, padx=(0, self.scale(20)))

        close_btn = ttk.Button(controls_frame, text="✖ Cerrar",
                              command=self.close_fullscreen_window, width=self.scale(15))
        close_btn.pack(side=tk.RIGHT)

        sensors_frame = ttk.Frame(controls_frame)
        sensors_frame.pack(side=tk.LEFT, padx=self.scale(15))

        ttk.Label(sensors_frame, text="Sensores:").pack(side=tk.LEFT, padx=(0, self.scale(10)))

        self.fullscreen_selected_sensors = [tk.BooleanVar(value=self.selected_sensors[i].get())
                                           for i in range(5)]

        for i in range(5):
            sensor_name = f"S{i}" if i > 0 else "Local"
            check = ttk.Checkbutton(sensors_frame,
                                   text=sensor_name,
                                   variable=self.fullscreen_selected_sensors[i],
                                   command=self.update_fullscreen_sensor_display)
            check.pack(side=tk.LEFT, padx=(0, self.scale(5)))

        # Crear figura con tamaño basado en la pantalla
        dpi = 100  # valor típico
        figsize_ancho = screen_width / dpi
        figsize_alto = screen_height / dpi * 0.8  # dejar espacio para controles
        self.fullscreen_fig, self.fullscreen_axes = plt.subplots(2, 1, figsize=(figsize_ancho, figsize_alto))
    
        current_unit = self.temp_unit_var.get()
        unit_symbol = self.unit_labels[current_unit][0]
        unit_title = self.unit_labels[current_unit][1]

        self.fullscreen_axes[0].set_title(f'{unit_title} vs Tiempo', fontsize=self.scale(14))
        self.fullscreen_axes[0].set_xlabel('')
        self.fullscreen_axes[0].set_ylabel(f'Temperatura ({unit_symbol})', fontsize=self.scale(12))
        self.fullscreen_axes[0].grid(True, alpha=0.3)
        self.fullscreen_axes[0].tick_params(axis='both', which='major', labelsize=self.scale(10))
        self.fullscreen_axes[0].set_xlim(0, self.time_window)

        self.fullscreen_axes[1].set_title('Humedad vs Tiempo', fontsize=self.scale(14))
        self.fullscreen_axes[1].set_xlabel('Tiempo (s)', fontsize=self.scale(12))
        self.fullscreen_axes[1].set_ylabel('Humedad (%)', fontsize=self.scale(12))
        self.fullscreen_axes[1].grid(True, alpha=0.3)
        self.fullscreen_axes[1].tick_params(axis='both', which='major', labelsize=self.scale(10))
        self.fullscreen_axes[1].set_xlim(0, self.time_window)

        self.fullscreen_lines_temp = []
        self.fullscreen_lines_hum = []

        temp_key = f'temp_{current_unit[0]}'

        for i in range(5):
            sensor_key = f'sensor{i}'
            times = list(self.data[sensor_key]['rel_time'])
            temps = list(self.data[sensor_key][temp_key])
            hums = list(self.data[sensor_key]['hum'])

            line_temp, = self.fullscreen_axes[0].plot(
                times, temps,
                color=self.colors[i],
                marker='o',
                markersize=self.scale(6),
                linewidth=3,
                alpha=0.8,
                label=f'Sensor {i}' if i > 0 else 'Sensor Local',
                visible=self.fullscreen_selected_sensors[i].get()
            )
            line_hum, = self.fullscreen_axes[1].plot(
                times, hums,
                color=self.colors[i],
                marker='s',
                markersize=self.scale(6),
                linewidth=3,
                alpha=0.8,
                label=f'Sensor {i}' if i > 0 else 'Sensor Local',
                visible=self.fullscreen_selected_sensors[i].get()
            )
            self.fullscreen_lines_temp.append(line_temp)
            self.fullscreen_lines_hum.append(line_hum)

        self.update_fullscreen_legends()
        plt.tight_layout()

        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

        self.fullscreen_canvas = FigureCanvasTkAgg(self.fullscreen_fig, master=fullscreen_frame)
        self.fullscreen_canvas_widget = self.fullscreen_canvas.get_tk_widget()
        self.fullscreen_toolbar = NavigationToolbar2Tk(self.fullscreen_canvas, fullscreen_frame, pack_toolbar=False)
        self.fullscreen_toolbar.update()
        self.fullscreen_toolbar.pack(side=tk.TOP, fill=tk.X)
        self.fullscreen_canvas_widget.pack(fill=tk.BOTH, expand=True)

        self.fullscreen_window.protocol("WM_DELETE_WINDOW", self.close_fullscreen_window)

        self.fullscreen_animation = animation.FuncAnimation(
            self.fullscreen_fig,
            self.update_fullscreen_plot,
            interval=1000,
            cache_frame_data=False,
            blit=False
        )
        self.fullscreen_canvas.draw()

    def update_fullscreen_sensor_display(self):
        if not hasattr(self, 'fullscreen_lines_temp'):
            return

        for i in range(5):
            visible = self.fullscreen_selected_sensors[i].get()
            if i < len(self.fullscreen_lines_temp):
                self.fullscreen_lines_temp[i].set_visible(visible)
                self.fullscreen_lines_hum[i].set_visible(visible)

        self.update_fullscreen_legends()
        if hasattr(self, 'fullscreen_canvas') and self.fullscreen_canvas:
            self.fullscreen_canvas.draw()

    def update_fullscreen_plot(self, frame=None):
        if not hasattr(self, 'fullscreen_lines_temp') or not hasattr(self, 'fullscreen_canvas'):
            return

        try:
            current_unit = self.temp_unit_var.get()
            temp_key = f'temp_{current_unit[0]}'

            for sensor_idx in range(5):
                sensor_key = f'sensor{sensor_idx}'
                if len(self.data[sensor_key]['rel_time']) > 0:
                    times = list(self.data[sensor_key]['rel_time'])
                    temps = list(self.data[sensor_key][temp_key])
                    hums = list(self.data[sensor_key]['hum'])

                    if (sensor_idx < len(self.fullscreen_lines_temp) and
                        sensor_idx < len(self.fullscreen_lines_hum)):
                        if (hasattr(self, 'fullscreen_selected_sensors') and
                            self.fullscreen_selected_sensors[sensor_idx].get()):
                            self.fullscreen_lines_temp[sensor_idx].set_data(times, temps)
                            self.fullscreen_lines_hum[sensor_idx].set_data(times, hums)
                        else:
                            self.fullscreen_lines_temp[sensor_idx].set_data([], [])
                            self.fullscreen_lines_hum[sensor_idx].set_data([], [])

            if hasattr(self, 'fullscreen_axes'):
                self.fullscreen_axes[0].set_xlim(0, self.time_window)
                self.fullscreen_axes[1].set_xlim(0, self.time_window)

            for ax in self.fullscreen_axes:
                ax.relim()
                ax.autoscale_view(scaley=True)

            self.update_fullscreen_legends()
            self.fullscreen_canvas.draw_idle()

        except Exception as e:
            print(f"Error actualizando gráficos en pantalla completa: {e}")

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

        if hasattr(self, 'fullscreen_fig'):
            plt.close(self.fullscreen_fig)

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
            ax.set_xlim(0, self.time_window)
            ax.relim()
            ax.autoscale_view(scaley=True)
        self.canvas.draw()

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

        self.unit_label.config(text=f"Unidad: {unit_title}")

        self.axes[0].set_title(unit_title)
        self.axes[0].set_ylabel(f'Temperatura ({unit_symbol})')

        if hasattr(self, 'fullscreen_axes') and self.fullscreen_axes:
            self.fullscreen_axes[0].set_title(unit_title)
            self.fullscreen_axes[0].set_ylabel(f'Temperatura ({unit_symbol})')

        for labels in self.sensor_labels:
            labels['temp_symbol'].config(text=unit_symbol)

        self.update_display()

        self.canvas.draw()
        if hasattr(self, 'fullscreen_canvas') and self.fullscreen_canvas:
            self.fullscreen_canvas.draw()

    def find_serial_ports(self):
        ports = []
        if sys.platform.startswith('win'):
            for i in range(1, 21):
                port = f'COM{i}'
                try:
                    s = serial.Serial(port)
                    s.close()
                    ports.append(port)
                except:
                    pass
        elif sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
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
            self.serial_port = serial.Serial(
                port=self.port_var.get(),
                baudrate=int(self.baudrate_var.get()),
                timeout=1
            )

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.csv_file = f"sensor_data_{timestamp}.csv"

            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'sensor_id', 'temperature_c', 'humidity'])

            for i in range(5):
                sensor_key = f'sensor{i}'
                for key in self.data[sensor_key]:
                    self.data[sensor_key][key].clear()

            self.is_running = True
            self.is_paused = False
            self.data_count = 0
            self.start_time = datetime.now()
            self.elapsed_time = 0

            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="Estado: Conectado y monitoreando")
            self.elapsed_time_label.config(text="Tiempo: 00:00:00")

            self.update_units()
            self.update_elapsed_time()

            self.serial_thread = threading.Thread(target=self.read_serial_data, daemon=True)
            self.serial_thread.start()
            self.update_thread = threading.Thread(target=self.update_data, daemon=True)
            self.update_thread.start()

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
        if not self.is_running:
            return

        self.is_paused = not self.is_paused

        if self.is_paused:
            self.pause_button.config(text="▶️ Reanudar")
            self.status_label.config(text="Estado: Pausado")
            if self.elapsed_timer:
                self.root.after_cancel(self.elapsed_timer)
                self.elapsed_timer = None
        else:
            self.pause_button.config(text="⏸️ Pausar")
            self.status_label.config(text="Estado: Monitoreando")
            self.update_elapsed_time()

    def stop_monitoring(self):
        if not self.is_running:
            return

        self.is_running = False
        self.is_paused = False

        if self.elapsed_timer:
            self.root.after_cancel(self.elapsed_timer)
            self.elapsed_timer = None

        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        self.pause_button.config(text="⏸️ Pausar")
        self.status_label.config(text="Estado: Detenido")

        if hasattr(self, 'animation'):
            self.animation.event_source.stop()

        if hasattr(self, 'fullscreen_animation'):
            try:
                self.fullscreen_animation.event_source.stop()
            except:
                pass

        messagebox.showinfo("Información", "Monitoreo detenido")

    def update_plot(self, frame):
        if self.is_paused:
            return self.lines_temp + self.lines_hum

        try:
            current_unit = self.temp_unit_var.get()
            temp_key = f'temp_{current_unit[0]}'

            for sensor_idx in range(5):
                sensor_key = f'sensor{sensor_idx}'
                if len(self.data[sensor_key]['rel_time']) > 0:
                    times = list(self.data[sensor_key]['rel_time'])
                    temps = list(self.data[sensor_key][temp_key])
                    hums = list(self.data[sensor_key]['hum'])

                    if self.selected_sensors[sensor_idx].get():
                        self.lines_temp[sensor_idx].set_data(times, temps)
                        self.lines_hum[sensor_idx].set_data(times, hums)
                    else:
                        self.lines_temp[sensor_idx].set_data([], [])
                        self.lines_hum[sensor_idx].set_data([], [])

            for ax in self.axes:
                ax.relim()
                ax.autoscale_view(scaley=True)

            self.update_legends()

        except Exception as e:
            print(f"Error actualizando gráficos: {e}")

        return self.lines_temp + self.lines_hum

    def update_display(self):
        self.data_count_label.config(text=f"Datos recibidos: {self.data_count}")

        current_unit = self.temp_unit_var.get()
        temp_key = f'temp_{current_unit[0]}'

        for sensor_idx in range(5):
            sensor_key = f'sensor{sensor_idx}'
            labels = self.sensor_labels[sensor_idx]

            if len(self.data[sensor_key]['rel_time']) > 0:
                temp = self.data[sensor_key][temp_key][-1]
                hum = self.data[sensor_key]['hum'][-1]
                last_time = self.data[sensor_key]['rel_time'][-1]

                if not pd.isna(temp) and not pd.isna(hum):
                    if current_unit == 'kelvin':
                        temp_text = f"{temp:.1f}"
                    else:
                        temp_text = f"{temp:.1f}"

                    labels['temp_value'].config(text=temp_text)
                    labels['hum_value'].config(text=f"{hum:.1f}")

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
            else:
                labels['temp_value'].config(text="--")
                labels['hum_value'].config(text="--")
                labels['time'].config(text="--")

    def on_closing(self):
        if self.is_running:
            self.stop_monitoring()
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SensorMonitorGUI(root)
    root.mainloop()