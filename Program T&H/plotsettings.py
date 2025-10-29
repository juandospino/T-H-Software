# plotsettings.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox
from PySide6.QtWebEngineWidgets import QWebEngineView
from bokeh.layouts import column

class PlotSettings(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        layout = QVBoxLayout(self)
        self.plot_info = QGroupBox("Real-time Plots")
        plot_info_layout = QVBoxLayout()
        self.plot_info.setLayout(plot_info_layout)
        layout.addWidget(self.plot_info)

        from plot import Plot
        self.plot = Plot(self.parent, getattr(self.parent.settings, "data", None))

        
        self.plot_view = QWebEngineView()
        initial_html = """
        
        """
        self.plot_view.setHtml(initial_html)
        plot_info_layout.addWidget(self.plot_view)

        print("✅ PlotSettings initialized successfully")

    def update_plot_view(self):
        """Pedir HTML nuevo al Plot y actualizar la vista"""
        try:
            html = self.plot.get_plots_html()
            if html:
                self.plot_view.setHtml(html)
                print("✅ Plot view updated")
        except Exception as e:
            print(f"❌ Error updating plot view: {e}")
