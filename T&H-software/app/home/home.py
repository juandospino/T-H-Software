import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
from PySide6.QtCore import Qt
from homesettings import HomeSettings
from serial.tools import list_ports
from plotsettings import PlotSettings

class Home(QMainWindow): #La clase Home hereda todos los atributos y métodos de la clase QMainWindow

    def __init__(self):
        super().__init__()

        self.device = None

        self.data = HomeSettings(self).data

        self.setWindowTitle("Temperature and Humidity")

        menu_bar = self.menuBar()

        self.devices = menu_bar.addMenu("Devices")
        self.devices.aboutToShow.connect(self.avialable_devices)

        file = menu_bar.addMenu("File")
        exit_action = file.addAction("Exit")
        exit_action.triggered.connect(exit)

        container = QWidget()
        self.setCentralWidget(container)

        layout = QHBoxLayout(container)

        self.settings = HomeSettings(self)
        layout.addWidget(self.settings)
        self.settings.setMinimumWidth(250)
        self.settings.setMaximumWidth(250)

        self.plot_settings = PlotSettings(self)
        layout.addWidget(self.plot_settings)
        self.plot_settings.setMinimumSize(270, 240)

        container.setLayout(layout)
    
    def avialable_devices(self):

        available_devices = [tuple(i)[0] for i in list(list_ports.comports())]
        dev_actions = []

        self.devices.clear()

        if not available_devices:
             self.devices.addAction("No devices connected").setEnabled(False)
        
        for dev in available_devices:
            dev_actions.append(self.devices.addAction(dev))

        for action in dev_actions:
            action.triggered.connect(lambda s, dev=action: self.select_device(dev.text()))
    
    def select_device(self, device):
        self.device = device
        self.settings.selected_device.setText(f"Selected device: {device}")

app = QApplication(sys.argv)

window = Home()
window.show()

app.exec()