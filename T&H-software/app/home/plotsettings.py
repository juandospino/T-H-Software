from plot import Plot
from bokeh.layouts import column
from bokeh.embed import file_html
from bokeh.resources import INLINE
from PySide6.QtWidgets import QWidget, QHBoxLayout, QGroupBox, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView

class PlotSettings(QWidget):
    def __init__(self, parent):
        super().__init__()
    
        self.parent = parent

        self.plot = Plot(self, self.parent.data)
        self.t, self.h = self.plot.get_plots()

        layout = QHBoxLayout(self)

        self.plot_info = QGroupBox("Plot")
        plot_info_layout = QVBoxLayout()
        self.plot_info.setLayout(plot_info_layout)
        layout.addWidget(self.plot_info)

        bokeh_layout = column(self.t, self.h)
        html = file_html(bokeh_layout, INLINE, "Sensor Data")

        self.plot_view = QWebEngineView()
        self.plot_view.setHtml(html)

        plot_info_layout.addWidget(self.plot_view)






