
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPushButton, QLabel, QSizePolicy, QFileDialog, QMessageBox, QFormLayout
from PySide6.QtCore import QStandardPaths
import pandas as pd
import datetime
from thread import SerialReader
from plot import Plot

class HomeSettings(QWidget):
    def __init__(self, parent):
        super().__init__()

        # Inicializar DataFrame completamente vacío
        self.data = pd.DataFrame({
            "localtemp": [],
            "localhum": [],
            "temp1": [],
            "hum1": [],
            "temp2": [],
            "hum2": [],
            "temp3": [],
            "hum3": [],
            "time": []
        })

        self.parent = parent

        # Plot local 
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

        # Buttons
        data_buttons = QGroupBox("Action Buttons")
        data_buttons_layout = QVBoxLayout()
        data_buttons.setLayout(data_buttons_layout)

        self.selected_device = QLabel("No device selected")
        data_buttons_layout.addWidget(self.selected_device)

        self.save_data_button = QPushButton("Save data")
        self.save_data_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.save_data_button.clicked.connect(self.save_data)

        self.start_button = QPushButton("Start Reading")
        self.start_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.start_button.clicked.connect(self.start_reading)

        self.stop_button = QPushButton("Stop Reading")
        self.stop_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.stop_button.clicked.connect(self.stop_reading)

        self.clear_data_button = QPushButton("Clear data")
        self.clear_data_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.clear_data_button.clicked.connect(self.clear_data)

        data_buttons_layout.addWidget(self.save_data_button)
        data_buttons_layout.addWidget(self.start_button)
        data_buttons_layout.addWidget(self.stop_button)
        data_buttons_layout.addWidget(self.clear_data_button)

        layout.addWidget(data_info)
        layout.addWidget(data_buttons)

    def serial_comand(self, command: str):
        if self.parent.device is None:
            self.parent.statusBar().showMessage("No device selected")
            return

        try:
            ser = serial.Serial(self.parent.device, 115200)
            print(command)
            ser.write(command.encode("utf-8"))
            ser.close()
        except Exception as e:
            self.parent.statusBar().showMessage("Invalid device, please check the device selected")
           
    def save_data(self):
        try:
            if self.data.empty:
                QMessageBox.warning(self, "Error", "No data to save.")
                return

            initial_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
            file_type = "Excel Files (*.xlsx);;CSV Files (*.csv);;All Files (*)"
            file_path, _ = QFileDialog.getSaveFileName(self, "Save data", initial_path + "/sensor_data.xlsx", file_type)

            if file_path:
                if file_path.endswith('.xlsx'):
                    self.data.to_excel(file_path, index=False, header=True)
                else:
                    self.data.to_csv(file_path, index=False, header=True)
                QMessageBox.information(self, "Success", f"Data saved: {len(self.data)} records\nAt: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def start_reading(self):
        if not self.parent.device:
            QMessageBox.warning(self, "Error", "No device selected.")
            return

        self.stop_reading()

        self.reader = SerialReader(self.parent.device, baudrate=9600)
        self.reader.data_received.connect(self.update_data)
        self.reader.error_signal.connect(self.show_error)
        self.reader.start()
        print("Reading thread started")

    def stop_reading(self):
        if hasattr(self, "reader") and self.reader:
            self.reader.stop()
            self.reader.wait(2000)
            if self.reader.isRunning():
                try:
                    self.reader.terminate()
                except Exception:
                    pass
            self.reader = None
            print(" Serial reading stopped")

    def update_data(self, result):
        try:
            n = result["id"]
            temp = result["temp"]
            hum = result["hum"]
            current_time = datetime.datetime.now().strftime("%H:%M:%S")

            new_row = {
                "localtemp": None, "localhum": None,
                "temp1": None, "hum1": None,
                "temp2": None, "hum2": None,
                "temp3": None, "hum3": None,
                "time": current_time
            }

            if n == 0:
                new_row["localtemp"] = temp
                new_row["localhum"] = hum
            elif n == 1:
                new_row["temp1"] = temp
                new_row["hum1"] = hum
            elif n == 2:
                new_row["temp2"] = temp
                new_row["hum2"] = hum
            elif n == 3:
                new_row["temp3"] = temp
                new_row["hum3"] = hum

            new_df = pd.DataFrame([new_row])
            new_df_clean = new_df.dropna(axis=1, how='all')
            self.data = pd.concat([self.data, new_df_clean], ignore_index=True)

            # actualizar display
            self.update_display(n, temp, hum)

            # actualizar plots
            if hasattr(self.parent, "plot_settings"):
                try:
        
                    html = self.plot.get_plots_html()
                    if html and hasattr(self.parent.plot_settings, "plot_view"):
                        self.parent.plot_settings.plot_view.setHtml(html)
                except Exception as e:
                    print(f" Error updating plots from HomeSettings: {e}")

        except Exception as e:
            print(f" Error in update_data: {e}")

    def show_error(self, msg):
        print(f" Serial reading error: {msg}")
        QMessageBox.warning(self, "Error", msg)

    def update_display(self, n, temp, hum):
        try:
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
        except Exception as e:
            print(f" Error updating display: {e}")

    def clear_data(self):
        try:
            if self.data.empty:
                QMessageBox.information(self, "Info", "No data to clear.")
                return

            reply = QMessageBox.question(
                self,
                "Confirm cleanup",
                f"Are you sure you want to clear all data?\n{len(self.data)} records will be lost.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.data = pd.DataFrame({
                    "localtemp": [], "localhum": [],
                    "temp1": [], "hum1": [],
                    "temp2": [], "hum2": [],
                    "temp3": [], "hum3": [],
                    "time": []
                })

                # reset labels
                self.value_local_temp.setText("-- °C")
                self.value_local_hum.setText("-- %")
                self.value_temp1.setText("-- °C")
                self.value_hum1.setText("-- %")
                self.value_temp2.setText("-- °C")
                self.value_hum2.setText("-- %")
                self.value_temp3.setText("-- °C")
                self.value_hum3.setText("-- %")

                # update plot (empty)
                if hasattr(self.parent, "plot_settings"):
                    self.parent.plot_settings.update_plot_view()

                QMessageBox.information(self, "Success", "All data has been cleared.")
        except Exception as e:
            print(f" Error clearing data: {e}")
            QMessageBox.critical(self, "Error", f"Error clearing data: {e}")
