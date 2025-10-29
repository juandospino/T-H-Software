# home.py
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
from serial.tools import list_ports
from homesettings import HomeSettings
from plotsettings import PlotSettings

class Home(QMainWindow):
    def __init__(self):
        super().__init__()

        self.device = None

        self.setWindowTitle("Temperature and Humidity Monitor")
        self.resize(1200, 600)

        menu_bar = self.menuBar()
        self.devices = menu_bar.addMenu("Devices")
        self.devices.aboutToShow.connect(self.available_devices)

        file = menu_bar.addMenu("File")
        exit_action = file.addAction("Exit")
        exit_action.triggered.connect(self.close)

        container = QWidget()
        self.setCentralWidget(container)
        layout = QHBoxLayout(container)

        self.settings = HomeSettings(self)
        layout.addWidget(self.settings)
        self.settings.setMinimumWidth(250)
        self.settings.setMaximumWidth(300)

        self.plot_settings = PlotSettings(self)
        layout.addWidget(self.plot_settings)
        self.plot_settings.setMinimumSize(600, 400)

        container.setLayout(layout)

    def available_devices(self):
        try:
            available_devices = [tuple(i)[0] for i in list(list_ports.comports())]
            dev_actions = []
            self.devices.clear()

            if not available_devices:
                self.devices.addAction("No devices connected").setEnabled(False)
                return

            for dev in available_devices:
                dev_actions.append(self.devices.addAction(dev))

            for action in dev_actions:
                action.triggered.connect(lambda s, dev=action: self.select_device(dev.text()))
        except Exception as e:
            print(f"❌ Error scanning devices: {e}")

    def select_device(self, device):
        try:
            self.device = device
            if hasattr(self.settings, 'selected_device'):
                self.settings.selected_device.setText(f"Selected device: {device}")
            print(f"✅ Device selected: {device}")
        except Exception as e:
            print(f"❌ Error selecting device: {e}")

    def closeEvent(self, event):
        try:
            if hasattr(self.settings, 'stop_reading'):
                self.settings.stop_reading()
        except Exception as e:
            print(f"❌ Error on close: {e}")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Home()
    window.show()
    sys.exit(app.exec())
