from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPushButton, QLabel, QSizePolicy, QFileDialog, QMessageBox, QMenuBar, QFormLayout
from PySide6.QtCore import Qt, QStandardPaths
import serial
import pandas as pd
from thread import SerialReader
from bokeh.layouts import row
from bokeh.embed import file_html
from bokeh.resources import INLINE
from plot import Plot

class HomeSettings(QWidget):
    def __init__(self, parent):
        super().__init__()

        self.data = pd.DataFrame({
            "localtemp": [None],
            "localhum": [None],
            "temp1": [None],
            "hum1": [None],
            "temp2": [None],
            "hum2": [None],
            "temp3": [None],
            "hum3": [None],
            "time": [None]})

        self.parent = parent 
        self.state = "Standby"

        self.plot = Plot(self, self.data)

        layout = QVBoxLayout(self) 

        data_info = QGroupBox("Information")
        data_layout = QFormLayout()
        data_info.setLayout(data_layout)

        self.label_local_temp = QLabel("Local Sensor Temperature:")
        self.value_local_temp = QLabel("-- °C")

        self.label_local_hum = QLabel("Local Sensor Humidity:")
        self.value_local_hum = QLabel("-- %")

        self.label_temp1 = QLabel("Sensor 1 Temperature:")
        self.value_temp1 = QLabel("-- °C")

        self.label_hum1 = QLabel("Sensor 1 Humidity:")
        self.value_hum1 = QLabel("-- %")

        self.label_temp2 = QLabel("Sensor 2 Temperature:")
        self.value_temp2 = QLabel("-- °C")

        self.label_hum2 = QLabel("Sensor 2 Humidity:")
        self.value_hum2 = QLabel("-- %")

        self.label_temp3 = QLabel("Sensor 3 Temperature:")
        self.value_temp3 = QLabel("-- °C")

        self.label_hum3 = QLabel("Sensor 3 Humidity:")
        self.value_hum3 = QLabel("-- %")

        data_layout.addRow(self.label_local_temp, self.value_local_temp)
        data_layout.addRow(self.label_local_hum, self.value_local_hum)
        data_layout.addRow(self.label_temp1, self.value_temp1)
        data_layout.addRow(self.label_hum1, self.value_hum1)
        data_layout.addRow(self.label_temp2, self.value_temp2)
        data_layout.addRow(self.label_hum2, self.value_hum2)
        data_layout.addRow(self.label_temp3, self.value_temp3)
        data_layout.addRow(self.label_hum3, self.value_hum3)

        data_buttons = QGroupBox("Action Buttons")
        data_buttons_layout = QVBoxLayout()
        data_buttons.setLayout(data_buttons_layout)

        self.save_data_button = QPushButton("Save data")
        self.save_data_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.save_data_button.clicked.connect(self.save_data)

        self.start_button = QPushButton("Start")
        self.start_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.start_button.clicked.connect(self.start_reading)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.stop_button.clicked.connect(self.stop_reading)

        data_buttons_layout.addWidget(self.save_data_button)
        data_buttons_layout.addWidget(self.start_button)
        data_buttons_layout.addWidget(self.stop_button)

        layout.addWidget(data_info)
        layout.addWidget(data_buttons)

    def serial_comand(self, command: str): #verifica que se haya seleccionado un dispositivo
		
        if self.parent.device == None:
            self.parent.statusBar().showMessage("No device selected")
            return
        
        try:
            ser = serial.Serial(self.parent.device, 115200)
            print(command)
            ser.write(command.encode("utf-8"))
            ser.close()
        
        except serial.SerialException:
            self.parent.statusBar().showMessage("Invalid device, please check the device selected")
            return
    
    def save_data(self):

        initial_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation) #Ruta estandar de guardado
        file_type = "Excel Files (*.xlsx);;All Files (*)" #Tipo de archivos a guardar, ;; es la forma como Qt separa los filtros

        self.file, _ = QFileDialog.getSaveFileName(self, "Save data", initial_path, file_type) #Ruta final de guardado
        self.data.to_excel(self.file, index = 0, header = True)

    def start_reading(self):
        self.reader = SerialReader(self.parent.device)
        self.reader.data_received.connect(self.update_data)
        self.reader.error_signal.connect(self.show_error)
        self.reader.start()

    def stop_reading(self):
        if self.reader:
            self.reader.stop()

    def update_data(self, result):

        n = result["id"]
        temp = result["temp"]
        hum = result["hum"]
        t = result["time"]

        if n == 0:
            self.data.loc[len(self.data)] = [temp, hum, None, None, None, None, None, None, t]
        elif n == 1:
            self.data.loc[len(self.data)] = [None, None, temp, hum, None, None, None, None, t]
        elif n == 2:
            self.data.loc[len(self.data)] = [None, None, None, None, temp, hum, None, None, t]
        elif n == 3:
            self.data.loc[len(self.data)] = [None, None, None, None, None, None, temp, hum, t]

        self.update_display(n, temp, hum)
        self.plot.refresh_plot()

        self.plot.refresh_plot()
        html = file_html(row(*self.plot.get_plots()), INLINE, "Sensor Data")

    def show_error(self, msg):
        QMessageBox.warning(self, "Error", msg)

    def update_display(self, n, temp, hum):

        if n == 0:
            self.value_local_temp.setText(f"{temp:.1f} °C")
            self.value_local_hum.setText(f"{hum:.1f} %")

        elif n == 1:
            self.value_temp1.setText(f"{temp:.1f} °C")
            self.value_hum1.setText(f"{hum:.1f} %")

        elif n == 2:
            self.value_temp2.setText(f"{temp:.1f} °C")
            self.value_hum2.setText(f"{hum:.1f} %")

        elif n == 3:
            self.value_temp3.setText(f"{temp:.1f} °C")
            self.value_hum3.setText(f"{hum:.1f} %")
    
