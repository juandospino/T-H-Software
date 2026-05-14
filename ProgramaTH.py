from __future__ import annotations

import csv
import math
import os
import sys
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import serial

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QIcon
from PyQt6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox,
    QFileDialog, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QMainWindow, QMessageBox, QPushButton,
    QRadioButton, QSizePolicy, QSplitter,
    QVBoxLayout, QWidget, QGraphicsDropShadowEffect,
    QTabWidget,
)

import pyqtgraph as pg

from base0 import TitleFrame
from base1 import ReportTab
from base2 import SerialDataHandler
from base3 import HeatMapWidget
from header_widget import HeaderWidget


# ═════════════════════════════════════════════════════════════════════════════
#  Colores
# ═════════════════════════════════════════════════════════════════════════════

COLORS = ["#94e2d5", "#89b4fa", "#f38ba8", "#cba6f7", "#a6e3a1", "#fab387"]

UNIT_LABELS: dict[str, tuple[str, str]] = {
    "celsius":    ("°C",  "Temperatura (°C)"),
    "fahrenheit": ("°F",  "Temperatura (°F)"),
    "kelvin":     ("K",   "Temperatura (K)"),
}


# ═════════════════════════════════════════════════════════════════════════════
#  Temas  (Catppuccin Mocha oscuro | Latte claro)
# ═════════════════════════════════════════════════════════════════════════════

def _qss(t: dict) -> str:
    return f"""
QMainWindow, QDialog, QWidget {{
    background:{t['bg_main']}; color:{t['text']};
    font-family:"Segoe UI",Arial,sans-serif; font-size:13px;
}}
QWidget#HeaderWidget {{
    background:{t['glass_card']};
    border-bottom:1px solid {t['border_spec']};
}}
QTabWidget::pane {{
    border:1px solid {t['border']}; background:{t['bg_main']}; border-radius:8px;
}}
QTabBar::tab {{
    background:{t['tab_bg']}; color:{t['text']};
    padding:9px 24px; border-top-left-radius:7px;
    border-top-right-radius:7px; margin-right:2px; font-weight:600;
}}
QTabBar::tab:selected   {{ background:{t['accent']}; color:{t['accent_text']}; }}
QTabBar::tab:hover:!selected {{ background:{t['tab_hover']}; }}
QPushButton {{
    background:{t['btn_bg']}; color:{t['text']};
    border:1px solid {t['border']}; border-radius:8px;
    padding:6px 14px; font-weight:600; min-height:28px;
}}
QPushButton:hover   {{ background:{t['btn_hover']}; border-color:{t['accent']}; }}
QPushButton:pressed {{ background:{t['accent']};    color:{t['accent_text']}; }}
QPushButton:disabled{{ background:{t['bg_input']};  color:{t['text_muted']}; border-color:{t['border']}; }}
QPushButton#StartBtn {{ border-color:{t['green']};  color:{t['green']};  }}
QPushButton#StartBtn:hover  {{ background:{t['green']};  color:{t['accent_text']}; }}
QPushButton#StopBtn  {{ border-color:{t['red']};    color:{t['red']};    }}
QPushButton#StopBtn:hover   {{ background:{t['red']};    color:{t['accent_text']}; }}
QPushButton#PauseBtn {{ border-color:{t['yellow']}; color:{t['yellow']}; }}
QPushButton#PauseBtn:hover  {{ background:{t['yellow']}; color:{t['accent_text']}; }}
QPushButton#ThemeBtn {{ border-color:{t['accent']}; color:{t['accent']};
                        border-radius:14px; padding:4px 12px; }}
QGroupBox {{
    font-weight:bold; background:{t['glass_card']};
    border:1px solid {t['border_card']};
    border-top:2px solid {t['border_spec']};
    border-radius:14px; margin-top:16px; padding:8px 6px 6px 6px;
}}
QGroupBox::title {{
    subcontrol-origin:margin; subcontrol-position:top left;
    padding:0 10px; color:{t['accent']}; font-size:12px;
}}
QFrame#SensorCard, QFrame#SummaryCard, QFrame#MapFrame {{
    background:{t['glass_card']};
    border:1px solid {t['border_card']};
    border-top:1px solid {t['border_spec']};
    border-radius:12px;
}}
QLabel#CardLabel {{ color:{t['text_muted']}; font-size:11px; }}
QLabel#InfoValue  {{ color:{t['accent']}; font-weight:bold; }}
QComboBox {{
    background:{t['bg_input']}; color:{t['text']};
    border:1px solid {t['border']}; border-radius:6px; padding:4px 10px; min-width:90px;
}}
QComboBox:hover {{ border-color:{t['accent']}; }}
QComboBox::drop-down {{ border:none; width:18px; }}
QComboBox QAbstractItemView {{
    background:{t['bg_input']}; color:{t['text']};
    selection-background-color:{t['accent']}; selection-color:{t['accent_text']};
}}
QRadioButton, QCheckBox {{ spacing:7px; color:{t['text']}; }}
QRadioButton::indicator {{
    width:14px; height:14px; border-radius:7px;
    border:2px solid {t['border']}; background:{t['bg_input']};
}}
QRadioButton::indicator:checked {{ background:{t['accent']}; border-color:{t['accent']}; }}
QCheckBox::indicator {{
    width:14px; height:14px; border-radius:3px;
    border:2px solid {t['border']}; background:{t['bg_input']};
}}
QCheckBox::indicator:checked {{ background:{t['accent']}; border-color:{t['accent']}; }}
QDoubleSpinBox, QSpinBox {{
    background:{t['bg_input']}; color:{t['text']};
    border:1px solid {t['border']}; border-radius:6px; padding:4px;
}}
QTableWidget {{
    background:{t['bg_input']}; color:{t['text']};
    border:1px solid {t['border']}; border-radius:6px;
    gridline-color:{t['border']}; alternate-background-color:{t['glass_card']};
}}
QHeaderView::section {{
    background:{t['tab_bg']}; color:{t['accent']};
    border:1px solid {t['border']}; padding:5px; font-weight:bold;
}}
QTableWidget::item:selected {{ background:{t['accent']}; color:{t['accent_text']}; }}
QScrollBar:vertical   {{ background:{t['bg_main']}; width:10px; }}
QScrollBar::handle:vertical {{ background:{t['border']}; border-radius:5px; min-height:20px; }}
QScrollBar:horizontal {{ background:{t['bg_main']}; height:10px; }}
QScrollBar::handle:horizontal {{ background:{t['border']}; border-radius:5px; min-width:20px; }}
QTextEdit {{
    background:{t['bg_input']}; color:{t['text']};
    border:1px solid {t['border']}; border-radius:6px;
}}
QSplitter::handle {{ background:{t['border']}; }}
"""

_DARK = dict(
    bg_main="#1e1e2e", bg_input="#313244",
    glass_card="rgba(49,50,68,0.60)",
    border="rgba(203,166,247,0.20)", border_card="rgba(255,255,255,0.07)",
    border_spec="rgba(203,166,247,0.35)",
    text="#cdd6f4", text_muted="#a6adc8",
    accent="#cba6f7", accent_text="#1e1e2e",
    tab_bg="#313244", tab_hover="#45475a",
    btn_bg="#313244", btn_hover="#45475a",
    green="#a6e3a1", red="#f38ba8", yellow="#fab387",
    pg_bg="#181825", pg_fg="#cdd6f4",
    hm_bg="#1e1e2e", hm_fg="#cdd6f4",
)
_LIGHT = dict(
    bg_main="#eff1f5", bg_input="#ffffff",
    glass_card="rgba(255,255,255,0.65)",
    border="rgba(92,95,119,0.25)", border_card="rgba(0,0,0,0.07)",
    border_spec="rgba(114,135,253,0.40)",
    text="#4c4f69", text_muted="#6c6f85",
    accent="#7287fd", accent_text="#ffffff",
    tab_bg="#dce0e8", tab_hover="#ccd0da",
    btn_bg="#dce0e8", btn_hover="#ccd0da",
    green="#40a02b", red="#d20f39", yellow="#df8e1d",
    pg_bg="#ffffff", pg_fg="#4c4f69",
    hm_bg="#eff1f5", hm_fg="#4c4f69",
)

DARK_QSS  = _qss(_DARK)
LIGHT_QSS = _qss(_LIGHT)


def _shadow(w: QWidget, r: int = 18, opacity: float = 0.28) -> None:
    eff = QGraphicsDropShadowEffect(w)
    eff.setBlurRadius(r)
    c = QColor("#000000"); c.setAlphaF(opacity)
    eff.setColor(c); eff.setOffset(0, 4)
    w.setGraphicsEffect(eff)


def _style_pg(pw: pg.PlotWidget, t: dict, title: str, ylabel: str) -> None:
    """Aplica estilo y título a un PlotWidget de pyqtgraph."""
    pw.setBackground(t["pg_bg"])
    # Título: usar HTML para garantizar color independientemente del QSS
    pw.setTitle(f'<span style="color:{t["pg_fg"]};font-size:11pt;">{title}</span>')
    pw.setLabel("left",   ylabel,       color=t["pg_fg"], **{"font-size": "10pt"})
    pw.setLabel("bottom", "Tiempo (s)", color=t["pg_fg"], **{"font-size": "10pt"})
    pw.showGrid(x=True, y=True, alpha=0.15)
    for ax_name in ["left", "bottom"]:
        ax = pw.getAxis(ax_name)
        ax.setPen(pg.mkPen(color=t["pg_fg"], width=1))
        ax.setTextPen(pg.mkPen(color=t["pg_fg"]))


# ═════════════════════════════════════════════════════════════════════════════
#  Hilo de búsqueda de puertos (sin congelar la UI)
# ═════════════════════════════════════════════════════════════════════════════

class _PortScanThread(QThread):
    found: pyqtSignal = pyqtSignal(list)

    def run(self) -> None:
        ports: list[str] = []
        if sys.platform.startswith("win"):
            for i in range(1, 21):
                p = f"COM{i}"
                try:
                    s = serial.Serial(p, timeout=0.05)
                    s.close(); ports.append(p)
                except Exception:
                    pass
        else:
            import glob
            ports = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
        self.found.emit(ports)


# ═════════════════════════════════════════════════════════════════════════════
#  Ventana de pantalla completa con actualización en vivo
# ═════════════════════════════════════════════════════════════════════════════

class FullscreenWindow(QMainWindow):
    """
    QMainWindow independiente (sin padre) que se abre maximizado y
    actualiza las gráficas en vivo cada 500 ms.
    Ahora incluye controles gráficos (leyenda, zoom, guardado).
    """

    def __init__(self, app_ref: "SensorMonitorApp"):
        super().__init__()          # SIN padre → ventana de sistema real
        self._app = app_ref
        self._curves_t: list[pg.PlotDataItem] = []
        self._curves_h: list[pg.PlotDataItem] = []

        self.setWindowTitle("Monitor — Pantalla Completa")
        self.setStyleSheet(app_ref.styleSheet())

        central = QWidget()
        self.setCentralWidget(central)
        lay = QVBoxLayout(central)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        t   = _DARK if app_ref._theme == "dark" else _LIGHT
        sym = UNIT_LABELS[app_ref.temp_unit][0]

        # Encabezado
        hdr = QLabel("📊 Monitor en Pantalla Completa — Temperatura y Humedad")
        hdr.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hdr.setStyleSheet(f"color: {t['accent']}; padding: 6px;")
        lay.addWidget(hdr)

        self._pw_t = pg.PlotWidget()
        self._pw_h = pg.PlotWidget()
        _style_pg(self._pw_t, t, f"Temperatura ({sym}) vs Tiempo", f"Temperatura ({sym})")
        _style_pg(self._pw_h, t, "Humedad vs Tiempo", "Humedad (%)")

        lg_t = self._pw_t.addLegend(offset=(-10, 10))
        lg_h = self._pw_h.addLegend(offset=(-10, 10))
        self._legend_temp = lg_t
        self._legend_hum = lg_h

        _KEY = {"celsius":"temp_c","fahrenheit":"temp_f","kelvin":"temp_k"}
        tkey = _KEY[app_ref.temp_unit]

        for i in range(6):
            lbl  = "Sensor Local" if i == 0 else f"Sensor {i}"
            pen  = pg.mkPen(color=COLORS[i], width=3)
            sp   = pg.mkPen(color=COLORS[i])
            sb   = pg.mkBrush(color=COLORS[i])
            vis  = app_ref.selected_sensors[i]
            rt   = list(app_ref.data[f"sensor{i}"]["rel_time"])
            temp = list(app_ref.data[f"sensor{i}"][tkey])
            hum  = list(app_ref.data[f"sensor{i}"]["hum"])

            ct = self._pw_t.plot(x=rt, y=temp, pen=pen, name=lbl,
                                  symbol="o", symbolSize=5,
                                  symbolPen=sp, symbolBrush=sb, visible=vis)
            ch = self._pw_h.plot(x=rt, y=hum, pen=pen, name=lbl,
                                  symbol="s", symbolSize=5,
                                  symbolPen=sp, symbolBrush=sb, visible=vis)
            self._curves_t.append(ct)
            self._curves_h.append(ch)

        sp_widget = QSplitter(Qt.Orientation.Vertical)
        sp_widget.addWidget(self._pw_t); sp_widget.addWidget(self._pw_h)
        sp_widget.setSizes([500, 400])
        lay.addWidget(sp_widget, stretch=1)

        # ── Controles gráficos ────────────────────────────────────────────────
        ctrl_box = QGroupBox("📐  Controles de Gráficos")
        ctrl_lay = QHBoxLayout(ctrl_box)
        
        self._btn_legend = QPushButton("👁️ Ocultar Leyenda")
        self._btn_legend.clicked.connect(self._toggle_legend)
        ctrl_lay.addWidget(self._btn_legend)
        
        btn_restore = QPushButton("🏠 Restaurar Vista")
        btn_restore.clicked.connect(self._restore_view)
        ctrl_lay.addWidget(btn_restore)
        
        btn_save = QPushButton("💾 Guardar Gráfico")
        btn_save.clicked.connect(self._save_figure)
        ctrl_lay.addWidget(btn_save)
        
        self._legend_visible = True
        
        ctrl_lay.addStretch()
        
        btn_close = QPushButton("✖️  Cerrar Pantalla Completa")
        btn_close.clicked.connect(self.close)
        ctrl_lay.addWidget(btn_close)
        
        lay.addWidget(ctrl_box)

        # Timer de actualización en vivo
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()

    def _toggle_legend(self) -> None:
        """Muestra/oculta la leyenda en ambos gráficos."""
        self._legend_visible = not self._legend_visible
        self._legend_temp.setVisible(self._legend_visible)
        self._legend_hum.setVisible(self._legend_visible)
        self._btn_legend.setText("👁️ Mostrar Leyenda" if not self._legend_visible else "👁️ Ocultar Leyenda")

    def _restore_view(self) -> None:
        """Restaura el zoom a la vista original."""
        self._pw_t.enableAutoRange()
        self._pw_h.enableAutoRange()
        self._pw_t.setXRange(0, max(60, self._app.time_window), padding=0.02)
        self._pw_h.setXRange(0, max(60, self._app.time_window), padding=0.02)

    def _save_figure(self) -> None:
        """Guarda los gráficos como imagen PNG."""
        fname, _ = QFileDialog.getSaveFileName(
            self, "Guardar Gráficos",
            f"graficos_fullscreen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            "PNG (*.png);;PDF (*.pdf)")
        if fname:
            try:
                # Exportar como imagen
                exporter = pg.exporters.ImageExporter(self._pw_t.plotItem)
                exporter.export(fileName=fname)
                QMessageBox.information(self, "Éxito", f"Gráfico guardado:\n{fname}")
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Error al guardar: {str(exc)}")

    def _refresh(self) -> None:
        """Actualiza las curvas con los datos más recientes de la app."""
        _KEY = {"celsius":"temp_c","fahrenheit":"temp_f","kelvin":"temp_k"}
        tkey = _KEY[self._app.temp_unit]
        xmax = 60.0

        for i in range(6):
            key = f"sensor{i}"
            rt  = list(self._app.data[key]["rel_time"])
            vis = self._app.selected_sensors[i]
            if rt and vis:
                self._curves_t[i].setData(x=rt, y=list(self._app.data[key][tkey]))
                self._curves_h[i].setData(x=rt, y=list(self._app.data[key]["hum"]))
                if rt[-1] > xmax:
                    xmax = rt[-1]
            else:
                self._curves_t[i].setData([], [])
                self._curves_h[i].setData([], [])

        self._pw_t.setXRange(0, xmax, padding=0.02)
        self._pw_h.setXRange(0, xmax, padding=0.02)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.showMaximized()

    def closeEvent(self, event) -> None:
        self._timer.stop()
        event.accept()


# ═════════════════════════════════════════════════════════════════════════════
#  Aplicación principal
# ═════════════════════════════════════════════════════════════════════════════

class SensorMonitorApp(QMainWindow):
    data_updated: pyqtSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "Monitor de Temperatura y Humedad Relativa  —  "
            "E. Conde · Y. Avendaño · J. D. Ospino · A. Rodríguez"
        )
        try:
            self.setWindowIcon(QIcon(str(Path("Logos") / "icon.ico")))
        except Exception:
            pass

        # ── estado ────────────────────────────────────────────────────────────
        self.is_running:   bool            = False
        self.is_paused:    bool            = False
        self.serial_port                   = None
        self.csv_file:     str | None      = None
        self.data_count:   int             = 0
        self.start_time:   datetime | None = None
        self.elapsed_time: float           = 0.0
        self.time_window:  float           = 60.0
        self.temp_unit:    str             = "celsius"
        self.selected_sensors: list[bool]  = [True] * 6
        self._theme:       str             = "dark"
        self._legend_visible: bool         = True
        self._fullscreen_win: FullscreenWindow | None = None
        self._scan_thread: _PortScanThread | None     = None

        self.data: dict[str, dict[str, deque]] = {
            f"sensor{i}": {
                "temp_c": deque(), "temp_f": deque(), "temp_k": deque(),
                "hum":    deque(), "rel_time": deque(),
            }
            for i in range(6)
        }

        self._serial_hdl = SerialDataHandler(self)
        self.data_updated.connect(self._on_data_updated)

        self._curves_temp: list[pg.PlotDataItem] = []
        self._curves_hum:  list[pg.PlotDataItem] = []
        self._cards:       list[dict]            = []
        self._plots_splitter: QSplitter | None   = None

        self._build_ui()
        self._build_pg_plots()
        self._find_ports()

        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.setInterval(1_000)
        self._elapsed_timer.timeout.connect(self._tick_elapsed)

        self._plot_timer = QTimer(self)
        self._plot_timer.setInterval(500)
        self._plot_timer.timeout.connect(self._refresh_plots)

        self._heatmap_timer = QTimer(self)
        self._heatmap_timer.setInterval(2_000)
        self._heatmap_timer.timeout.connect(self._heatmap_widget.refresh)

        self.apply_theme("dark")
        self.showMaximized()

    # ─────────────────────────────────────────────────────────────────────────
    #  UI
    # ─────────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        central = QWidget(); self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(6); root.setContentsMargins(8, 8, 8, 8)

        # Usar el nuevo HeaderWidget mejorado
        self._header_widget = HeaderWidget(
            title_text="🌡️  Monitor de Temperatura y Humedad  💧",
            icon_path=Path("Logos") / "icon.ico",
            left_logos=[(Path("Logos") / "LogoSemillero.png", 55),
                       (Path("Logos") / "LogoFisica.png", 50)],
            right_logos=[(Path("Logos") / "UA.png", 50)],
        )
        self._btn_theme = self._header_widget.add_theme_button(self._toggle_theme)
        root.addWidget(self._header_widget)

        self._tabs = QTabWidget(); root.addWidget(self._tabs)

        monitor_w = QWidget()
        self._monitor_layout = QVBoxLayout(monitor_w)
        self._monitor_layout.setSpacing(6)
        self._build_monitor_controls(self._monitor_layout)
        self._tabs.addTab(monitor_w, "📈  Monitor")

        self._heatmap_widget = HeatMapWidget(self)
        self._tabs.addTab(self._heatmap_widget, "🗺️  Mapa de Calor")

        self._report_tab = ReportTab(self)
        self._tabs.addTab(self._report_tab, "📋  Reporte")

    def _build_monitor_controls(self, lay: QVBoxLayout) -> None:
        # Puerto
        cfg = QGroupBox("⚙️  Configuración de Puerto"); _shadow(cfg)
        ch = QHBoxLayout(cfg)
        ch.addWidget(QLabel("Puerto:"))
        self._port_cb = QComboBox(); self._port_cb.setMinimumWidth(110)
        ch.addWidget(self._port_cb)
        self._btn_scan = QPushButton("🔍 Buscar")
        self._btn_scan.clicked.connect(self._find_ports)
        ch.addWidget(self._btn_scan); ch.addSpacing(20)
        ch.addWidget(QLabel("Baudrate:"))
        self._baud_cb = QComboBox()
        self._baud_cb.addItems(["9600","19200","38400","57600","115200"])
        ch.addWidget(self._baud_cb); ch.addStretch()
        lay.addWidget(cfg)

        # Unidades
        ub = QGroupBox("🌡️  Unidades de Temperatura"); _shadow(ub)
        uh = QHBoxLayout(ub); self._unit_group = QButtonGroup(self)
        for val, txt in [("celsius","Celsius (°C)"),
                          ("fahrenheit","Fahrenheit (°F)"),
                          ("kelvin","Kelvin (K)")]:
            rb = QRadioButton(txt)
            if val == "celsius": rb.setChecked(True)
            rb.setProperty("unit_val", val)
            rb.toggled.connect(self._on_unit_changed)
            self._unit_group.addButton(rb); uh.addWidget(rb)
        uh.addStretch(); lay.addWidget(ub)

        # Botones de acción
        br = QHBoxLayout()
        self._btn_start = QPushButton("▶  Comenzar");  self._btn_start.setObjectName("StartBtn")
        self._btn_pause = QPushButton("⏸  Pausar");    self._btn_pause.setObjectName("PauseBtn")
        self._btn_stop  = QPushButton("⏹  Detener");   self._btn_stop.setObjectName("StopBtn")
        btn_reset = QPushButton("↺  Reiniciar"); self._btn_full = QPushButton("⛶  Pantalla completa")
        self._btn_pause.setEnabled(False); self._btn_stop.setEnabled(False)
        self._btn_start.clicked.connect(self._start_monitoring)
        self._btn_pause.clicked.connect(self._pause_monitoring)
        self._btn_stop.clicked.connect(self._stop_monitoring)
        btn_reset.clicked.connect(self._reset_graphs)
        self._btn_full.clicked.connect(self._open_fullscreen)
        for b in [self._btn_start, self._btn_pause, self._btn_stop, btn_reset, self._btn_full]:
            br.addWidget(b)
        br.addStretch(); lay.addLayout(br)

        # Info
        ib = QGroupBox("ℹ️  Información del Sistema"); _shadow(ib)
        ih = QHBoxLayout(ib)
        self._lbl_status = QLabel("Estado: Desconectado")
        self._lbl_count  = QLabel("Datos: 0")
        self._lbl_unit   = QLabel("Unidad: Celsius (°C)")
        self._lbl_time   = QLabel("⏱ 00:00:00")
        for lbl in [self._lbl_status, self._lbl_count, self._lbl_unit, self._lbl_time]:
            ih.addWidget(lbl)
        ih.addStretch(); lay.addWidget(ib)

        # Tarjetas
        cb = QGroupBox("📡  Valores Actuales"); _shadow(cb); ch2 = QHBoxLayout(cb)
        for i in range(6):
            card = QFrame(); card.setObjectName("SensorCard"); _shadow(card, r=12, opacity=0.18)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            cl = QVBoxLayout(card); cl.setSpacing(3); cl.setContentsMargins(10, 8, 10, 8)
            hr = QHBoxLayout()
            chk = QCheckBox(); chk.setChecked(True)
            chk.stateChanged.connect(lambda s, idx=i: self._on_sensor_check(idx, s))
            hr.addWidget(chk)
            nl = QLabel("Local" if i == 0 else f"Sensor {i}")
            nl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            nl.setStyleSheet(f"color:{COLORS[i]};"); hr.addWidget(nl); hr.addStretch()
            cl.addLayout(hr)
            t_lbl = QLabel("--"); t_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
            t_lbl.setStyleSheet(f"color:{COLORS[i]};")
            t_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(t_lbl)
            sym_lbl = QLabel("°C"); sym_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sym_lbl.setStyleSheet("font-size:11px;"); cl.addWidget(sym_lbl)
            h_lbl = QLabel("Hum: --"); h_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            h_lbl.setStyleSheet("color:#89dceb;font-size:11px;"); cl.addWidget(h_lbl)
            rt_lbl = QLabel("--"); rt_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rt_lbl.setStyleSheet("font-size:10px;"); cl.addWidget(rt_lbl)
            ch2.addWidget(card)
            self._cards.append({"temp": t_lbl, "sym": sym_lbl, "hum": h_lbl, "time": rt_lbl})
        lay.addWidget(cb)

        # Controles de gráficos
        gc = QGroupBox("📐  Controles de Gráficos"); gch = QHBoxLayout(gc)
        self._btn_legend = QPushButton("Ocultar leyenda")
        btn_save_fig = QPushButton("💾 Guardar gráfico"); btn_restore = QPushButton("🏠 Restaurar vista")
        self._btn_legend.clicked.connect(self._toggle_legend)
        btn_save_fig.clicked.connect(self._save_figure)
        btn_restore.clicked.connect(self._restore_view)
        for b in [btn_restore, btn_save_fig, self._btn_legend]:
            gch.addWidget(b)
        gch.addStretch(); lay.addWidget(gc)

    # ─────────────────────────────────────────────────────────────────────────
    #  pyqtgraph
    # ─────────────────────────────────────────────────────────────────────────

    def _build_pg_plots(self) -> None:
        pg.setConfigOptions(antialias=True, useOpenGL=False)
        self._pw_temp = pg.PlotWidget()
        self._pw_hum  = pg.PlotWidget()

        t = _DARK  # se actualiza en apply_theme
        _style_pg(self._pw_temp, t, "Temperatura vs Tiempo", "Temperatura (°C)")
        _style_pg(self._pw_hum,  t, "Humedad vs Tiempo",     "Humedad (%)")
        self._pw_temp.setXRange(0, self.time_window, padding=0.02)
        self._pw_hum.setXRange(0, self.time_window,  padding=0.02)

        self._legend_temp = self._pw_temp.addLegend(offset=(-10, 10))
        self._legend_hum  = self._pw_hum.addLegend(offset=(-10, 10))

        for i in range(6):
            name = "Sensor Local" if i == 0 else f"Sensor {i}"
            pen  = pg.mkPen(color=COLORS[i], width=2.5)
            sp   = pg.mkPen(color=COLORS[i]); sb = pg.mkBrush(color=COLORS[i])
            ct   = self._pw_temp.plot(pen=pen, name=name, symbol="o",
                                       symbolSize=5, symbolPen=sp, symbolBrush=sb)
            ch   = self._pw_hum.plot( pen=pen, name=name, symbol="s",
                                       symbolSize=5, symbolPen=sp, symbolBrush=sb)
            self._curves_temp.append(ct); self._curves_hum.append(ch)

        self._plots_splitter = QSplitter(Qt.Orientation.Vertical)
        self._plots_splitter.addWidget(self._pw_temp)
        self._plots_splitter.addWidget(self._pw_hum)
        self._plots_splitter.setSizes([400, 300])
        self._monitor_layout.addWidget(self._plots_splitter, stretch=1)

    # ─────────────────────────────────────────────────────────────────────────
    #  Tema
    # ─────────────────────────────────────────────────────────────────────────

    def apply_theme(self, theme: str) -> None:
        self._theme = theme
        t = _DARK if theme == "dark" else _LIGHT
        self.setStyleSheet(DARK_QSS if theme == "dark" else LIGHT_QSS)

        sym = UNIT_LABELS[self.temp_unit][0]
        _style_pg(self._pw_temp, t, f"Temperatura ({sym}) vs Tiempo", f"Temperatura ({sym})")
        _style_pg(self._pw_hum,  t, "Humedad vs Tiempo",               "Humedad (%)")

        self._heatmap_widget.update_theme(t["hm_bg"], t["hm_fg"])
        self._header_widget.update_theme(t["glass_card"], t["accent"])

    def _toggle_theme(self) -> None:
        new = "light" if self._theme == "dark" else "dark"
        self.apply_theme(new)
        self._btn_theme.setText("🌙 Modo Oscuro" if new == "light" else "☀️ Modo Claro")

    # ─────────────────────────────────────────────────────────────────────────
    #  Puertos — en hilo separado para no congelar la UI
    # ─────────────────────────────────────────────────────────────────────────

    def _find_ports(self) -> None:
        self._btn_scan.setEnabled(False)
        self._btn_scan.setText("🔍 Buscando…")
        self._scan_thread = _PortScanThread()
        self._scan_thread.found.connect(self._on_ports_found)
        self._scan_thread.start()

    def _on_ports_found(self, ports: list) -> None:
        self._port_cb.clear(); self._port_cb.addItems(ports)
        self._btn_scan.setEnabled(True); self._btn_scan.setText("🔍 Buscar")

    # ─────────────────────────────────────────────────────────────────────────
    #  Monitoreo
    # ─────────────────────────────────────────────────────────────────────────

    def _start_monitoring(self) -> None:
        if self.is_running: return
        port_name = self._port_cb.currentText()
        if not port_name:
            QMessageBox.critical(self, "Error", "Selecciona un puerto COM."); return
        try:
            self.serial_port = serial.Serial(
                port=port_name, baudrate=int(self._baud_cb.currentText()), timeout=1)
        except Exception as exc:
            QMessageBox.critical(self, "Error de conexión", str(exc)); return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_file = f"sensor_data_{ts}.csv"
        with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(
                ["timestamp","MJD","JD","sensor_id","temperature_c","humidity"])

        for key in self.data:
            for buf in self.data[key].values(): buf.clear()

        self.is_running = True; self.is_paused = False
        self.data_count = 0; self.start_time = datetime.now()
        self.elapsed_time = 0.0; self.time_window = 60.0

        self._btn_start.setEnabled(False)
        self._btn_pause.setEnabled(True); self._btn_stop.setEnabled(True)
        self._lbl_status.setText("Estado: ✅ Monitoreando")

        self._serial_hdl.start(self.serial_port)
        self._elapsed_timer.start(); self._plot_timer.start()
        self._heatmap_timer.start()
        self._pw_temp.setXRange(0, self.time_window, padding=0.02)
        self._pw_hum.setXRange(0,  self.time_window, padding=0.02)

        QMessageBox.information(self, "Conectado",
            f"Monitoreo iniciado en {port_name}\nUnidad: {self.temp_unit.title()}")

    def _pause_monitoring(self) -> None:
        if not self.is_running: return
        self.is_paused = not self.is_paused
        self._serial_hdl.set_paused(self.is_paused)
        if self.is_paused:
            self._btn_pause.setText("▶  Reanudar")
            self._lbl_status.setText("Estado: ⏸ Pausado"); self._elapsed_timer.stop()
        else:
            self._btn_pause.setText("⏸  Pausar")
            self._lbl_status.setText("Estado: ✅ Monitoreando"); self._elapsed_timer.start()

    def _stop_monitoring(self) -> None:
        if not self.is_running: return
        self.is_running = False; self.is_paused = False
        self._serial_hdl.stop()
        self._elapsed_timer.stop(); self._plot_timer.stop(); self._heatmap_timer.stop()
        if self.serial_port and self.serial_port.is_open: self.serial_port.close()
        self._btn_start.setEnabled(True)
        self._btn_pause.setEnabled(False); self._btn_stop.setEnabled(False)
        self._btn_pause.setText("⏸  Pausar")
        self._lbl_status.setText("Estado: ⏹ Detenido")
        QMessageBox.information(self, "Detenido", "Monitoreo detenido.")

    def _reset_graphs(self) -> None:
        ans = QMessageBox.question(self, "Reiniciar",
            "¿Borrar todos los datos visualizados?\n(El CSV no se elimina.)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ans != QMessageBox.StandardButton.Yes: return
        if self.is_running: self._stop_monitoring()
        for key in self.data:
            for buf in self.data[key].values(): buf.clear()
        self.data_count = 0; self.elapsed_time = 0.0; self.time_window = 60.0
        self._lbl_count.setText("Datos: 0"); self._lbl_time.setText("⏱ 00:00:00")
        for card in self._cards:
            card["temp"].setText("--"); card["hum"].setText("Hum: --"); card["time"].setText("--")
        for c in self._curves_temp + self._curves_hum: c.setData([], [])
        self._pw_temp.setXRange(0, 60, padding=0.02)
        self._pw_hum.setXRange(0,  60, padding=0.02)
        QMessageBox.information(self, "Listo", "Gráficos reiniciados.")

    # ─────────────────────────────────────────────────────────────────────────
    #  Slots de datos
    # ─────────────────────────────────────────────────────────────────────────

    def _on_data_updated(self) -> None:
        self._lbl_count.setText(f"Datos: {self.data_count}")
        _KEY = {"celsius":"temp_c","fahrenheit":"temp_f","kelvin":"temp_k"}
        _SYM = {"celsius":"°C","fahrenheit":"°F","kelvin":"K"}
        tkey = _KEY[self.temp_unit]; sym = _SYM[self.temp_unit]
        for i, card in enumerate(self._cards):
            buf = self.data[f"sensor{i}"]
            if buf["rel_time"]:
                tv = buf[tkey][-1]; hv = buf["hum"][-1]; rt = buf["rel_time"][-1]
                if not math.isnan(tv):
                    card["temp"].setText(f"{tv:.1f}"); card["sym"].setText(sym)
                    card["hum"].setText(f"Hum: {hv:.1f}%")
                    ts = (f"{rt/3600:.1f}h" if rt>=3600 else
                          f"{rt/60:.1f}m"   if rt>=60   else f"{rt:.0f}s")
                    card["time"].setText(ts); continue
            card["temp"].setText("--"); card["hum"].setText("Hum: --"); card["time"].setText("--")

    def _on_unit_changed(self, checked: bool) -> None:
        if not checked: return
        rb = self.sender(); self.temp_unit = rb.property("unit_val")
        sym = UNIT_LABELS[self.temp_unit][0]; ttl = UNIT_LABELS[self.temp_unit][1]
        t   = _DARK if self._theme == "dark" else _LIGHT
        _style_pg(self._pw_temp, t, f"Temperatura ({sym}) vs Tiempo", f"Temperatura ({sym})")
        self._lbl_unit.setText(f"Unidad: {ttl}")
        for card in self._cards: card["sym"].setText(sym)
        self._refresh_plots()

    def _on_sensor_check(self, idx: int, state: int) -> None:
        self.selected_sensors[idx] = bool(state)
        self._curves_temp[idx].setVisible(bool(state))
        self._curves_hum[idx].setVisible(bool(state))

    # ─────────────────────────────────────────────────────────────────────────
    #  Timers
    # ─────────────────────────────────────────────────────────────────────────

    def _tick_elapsed(self) -> None:
        if self.start_time:
            self.elapsed_time = (datetime.now() - self.start_time).total_seconds()
            h = int(self.elapsed_time // 3600)
            m = int((self.elapsed_time % 3600) // 60)
            s = int(self.elapsed_time % 60)
            self._lbl_time.setText(f"⏱ {h:02d}:{m:02d}:{s:02d}")
            if self.elapsed_time > self.time_window:
                self.time_window = self.elapsed_time
                self._pw_temp.setXRange(0, self.time_window, padding=0.02)
                self._pw_hum.setXRange(0, self.time_window,  padding=0.02)

    def _refresh_plots(self) -> None:
        if self.is_paused: return
        _KEY = {"celsius":"temp_c","fahrenheit":"temp_f","kelvin":"temp_k"}
        tkey = _KEY[self.temp_unit]
        for i in range(6):
            key = f"sensor{i}"; rt = list(self.data[key]["rel_time"])
            if rt and self.selected_sensors[i]:
                self._curves_temp[i].setData(x=rt, y=list(self.data[key][tkey]))
                self._curves_hum[i].setData( x=rt, y=list(self.data[key]["hum"]))
            else:
                self._curves_temp[i].setData([], []); self._curves_hum[i].setData([], [])

    # ─────────────────────────────────────────────────────────────────────────
    #  Controles de gráfico
    # ─────────────────────────────────────────────────────────────────────────

    def _toggle_legend(self) -> None:
        self._legend_visible = not self._legend_visible
        self._legend_temp.setVisible(self._legend_visible)
        self._legend_hum.setVisible(self._legend_visible)
        self._btn_legend.setText(
            "Mostrar leyenda" if not self._legend_visible else "Ocultar leyenda")

    def _restore_view(self) -> None:
        self._pw_temp.enableAutoRange(); self._pw_hum.enableAutoRange()
        self._pw_temp.setXRange(0, self.time_window, padding=0.02)
        self._pw_hum.setXRange(0,  self.time_window, padding=0.02)

    def _save_figure(self) -> None:
        fname, _ = QFileDialog.getSaveFileName(
            self, "Guardar Gráfico",
            f"graficos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png", "PNG (*.png)")
        if not fname: return
        try:
            px = self._plots_splitter.grab(); px.save(fname)
            QMessageBox.information(self, "Éxito", f"Gráfico guardado:\n{fname}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _open_fullscreen(self) -> None:
        if self._fullscreen_win and self._fullscreen_win.isVisible():
            self._fullscreen_win.raise_(); self._fullscreen_win.activateWindow(); return
        self._fullscreen_win = FullscreenWindow(self)
        self._fullscreen_win.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._fullscreen_win.destroyed.connect(
            lambda: setattr(self, "_fullscreen_win", None))
        self._fullscreen_win.show()

    # ─────────────────────────────────────────────────────────────────────────
    #  Matemáticas
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def convert_temperature(tc: float, to: str) -> float:
        if pd.isna(tc): return tc
        if to == "fahrenheit": return tc * 9 / 5 + 32
        if to == "kelvin":     return tc + 273.15
        return tc

    @staticmethod
    def _jd(dt: datetime) -> float:
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        y, mo = dt.year, dt.month
        d = dt.day + (dt.hour + (dt.minute + (dt.second + dt.microsecond/1e6)/60)/60)/24
        if mo <= 2: y -= 1; mo += 12
        A = math.floor(y/100); B = 2 - A + math.floor(A/4)
        return math.floor(365.25*(y+4716)) + math.floor(30.6001*(mo+1)) + d + B - 1524.5

    def compute_jd(self, dt): return self._jd(dt)
    def compute_mjd(self, dt): return self._jd(dt) - 2_400_000.5

    @staticmethod
    def get_time_text(s: float) -> str:
        h, rem = divmod(int(s), 3600); m, sec = divmod(rem, 60)
        return f"{h}h {m}m {sec}s" if h else (f"{m}m {sec}s" if m else f"{sec}s")

    def closeEvent(self, event) -> None:
        if self.is_running: self._stop_monitoring()
        if self.serial_port and self.serial_port.is_open: self.serial_port.close()
        if self._fullscreen_win: self._fullscreen_win.close()
        event.accept()


# ═════════════════════════════════════════════════════════════════════════════
#  Punto de entrada
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font_path = str(Path("fonts") / "Roboto.ttf")
    if os.path.exists(font_path):
        QFontDatabase.addApplicationFont(font_path); app.setFont(QFont("Roboto", 11))
    else:
        app.setFont(QFont("Segoe UI", 11))
    win = SensorMonitorApp()
    sys.exit(app.exec())
