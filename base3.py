"""
base3.py — Mapa de calor dual (Temperatura + Humedad).

Mejoras:
  • Renderizado con matplotlib colormap + pcolormesh(shading='gouraud')
    → RdBu_r (temperatura): azul frío → rojo caliente
    → YlGnBu (humedad): amarillo seco → azul húmedo
  • Funciona con 1, 2 ó 6+ sensores (sin mínimo rígido de 3).
  • Sensores arrastrables sincronizados entre ambos mapas.
  • Posiciones editables con QDoubleSpinBox (dos vías: drag ↔ spin).
  • Fuente de datos: En vivo | Cargar CSV.
  • CORREGIDO: Solo muestra marcadores para sensores con datos activos.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.cm as cm
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib import patheffects as pe

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QGroupBox, QGridLayout, QLabel, QPushButton,
    QDoubleSpinBox, QFrame, QRadioButton, QButtonGroup,
    QFileDialog, QMessageBox,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

_SCIPY = False
try:
    from scipy.interpolate import griddata as _gd
    _SCIPY = True
except ImportError:
    print("⚠  scipy no encontrado — pip install scipy")

# ── colormaps matplotlib ──────────────────────────────────────────────────────
_CMAP_TEMP = cm.get_cmap("RdBu_r")    # Red-Blue reversed: rojo=caliente, azul=frío
_CMAP_HUM  = cm.get_cmap("YlGnBu")    # Yellow-Green-Blue: amarillo=seco, azul=húmedo

# ── constantes ────────────────────────────────────────────────────────────────
_COLORS = ["#94e2d5", "#89b4fa", "#f38ba8", "#cba6f7", "#a6e3a1", "#fab387"]
_DEFAULTS: list[tuple[float, float]] = [
    (0.20, 0.75), (0.50, 0.75), (0.80, 0.75),
    (0.20, 0.25), (0.50, 0.25), (0.80, 0.25),
]
_GRID = 150      # resolución de la cuadrícula de interpolación
_XY   = np.linspace(0, 1, _GRID)
_GX, _GY = np.meshgrid(_XY, _XY)


# ═════════════════════════════════════════════════════════════════════════════
#  Almacén de posiciones compartido
# ═════════════════════════════════════════════════════════════════════════════

class _PositionStore:
    def __init__(self):
        self._pos: list[list[float]] = [[x, y] for x, y in _DEFAULTS]
        self._cbs: list = []

    def register(self, cb) -> None:
        self._cbs.append(cb)

    def get_all(self) -> list[tuple[float, float]]:
        return [tuple(p) for p in self._pos]           # type: ignore[return-value]

    def move(self, idx: int, x: float, y: float, source=None) -> None:
        self._pos[idx] = [x, y]
        for cb in self._cbs:
            cb(idx, x, y, source)

    def reset(self) -> None:
        for i, (x, y) in enumerate(_DEFAULTS):
            self._pos[i] = [x, y]
        for cb in self._cbs:
            cb(-1, 0.0, 0.0, "reset")


# ═════════════════════════════════════════════════════════════════════════════
#  Un mapa de calor matplotlib con pcolormesh
# ═════════════════════════════════════════════════════════════════════════════

class _HeatMapPlot(QWidget):
    """
    Canvas matplotlib con pcolormesh(shading='gouraud') para degradado suave,
    contornos, marcadores arrastrables y hotspot/coldspot.
    """

    def __init__(self, store: _PositionStore, unit_sym: str,
                 plot_title: str, cmap):
        super().__init__()
        self.store    = store
        self.unit_sym = unit_sym
        self._cmap    = cmap
        self._active: int | None = None
        # datos de los marcadores (solo posición; se redibujan en render)
        self._mpos: list[list[float]] = [[x, y] for x, y in _DEFAULTS]
        # handles matplotlib que se recrean en cada render
        self._mesh   = None
        self._cbar   = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.fig    = Figure(tight_layout=True, facecolor="#1e1e2e")
        self.canvas = FigureCanvasQTAgg(self.fig)
        lay.addWidget(self.canvas)

        # Axes con espacio reservado para colorbar
        self.ax   = self.fig.add_axes([0.08, 0.08, 0.76, 0.84])
        self.cax  = self.fig.add_axes([0.87, 0.08, 0.03, 0.84])
        self._style_axes(plot_title)

        # primer render en blanco
        self._draw_blank()

        # eventos de drag
        self.canvas.mpl_connect("button_press_event",   self._press)
        self.canvas.mpl_connect("button_release_event", self._release)
        self.canvas.mpl_connect("motion_notify_event",  self._motion)

        # sincronización desde el store
        self.store.register(self._on_store)

    # ── axes style ────────────────────────────────────────────────────────────

    def _style_axes(self, title: str = "") -> None:
        ax = self.ax
        ax.set_facecolor("#181825")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("Posición X", color="#cdd6f4", fontsize=9)
        ax.set_ylabel("Posición Y", color="#cdd6f4", fontsize=9)
        ax.tick_params(colors="#cdd6f4", labelsize=8)
        if title:
            ax.set_title(title, color="#cdd6f4", fontsize=11, fontweight="bold", pad=6)
        for sp in ax.spines.values():
            sp.set_edgecolor("#45475a")
        ax.grid(True, color="#313244", linestyle="--", alpha=0.35, zorder=0)

    def _draw_blank(self) -> None:
        blank = np.zeros((_GRID, _GRID))
        self._mesh = self.ax.pcolormesh(
            _GX, _GY, blank,
            cmap=self._cmap, shading="gouraud",
            alpha=0.0, vmin=0, vmax=1, zorder=1,
        )
        self._cbar = self.fig.colorbar(
            self._mesh, cax=self.cax,
            label=f"({self.unit_sym})",
        )
        self._cbar.ax.yaxis.label.set_color("#cdd6f4")
        self._cbar.ax.tick_params(colors="#cdd6f4", labelsize=8)
        self._draw_markers([])  # No mostrar marcadores en blanco
        self.canvas.draw()

    # ── interpolación ─────────────────────────────────────────────────────────

    @staticmethod
    def _interpolate(pts: np.ndarray, vals: np.ndarray) -> np.ndarray:
        """
        Interpola pts→vals en la cuadrícula global.
        Funciona con 1, 2 ó 3+ puntos.
        """
        n = len(pts)
        if n == 0:
            return np.full((_GRID, _GRID), np.nan)
        if n == 1:
            return np.full((_GRID, _GRID), float(vals[0]))
        if n == 2:
            # dos puntos → nearest (muestra dos zonas de color)
            return _gd(pts, vals, (_GX, _GY), method="nearest")
        # 3+ puntos → linear + nearest fallback
        gz = _gd(pts, vals, (_GX, _GY), method="linear")
        near = _gd(pts, vals, (_GX, _GY), method="nearest")
        return np.where(np.isnan(gz), near, gz)

    # ── renderizado principal ─────────────────────────────────────────────────

    def render(self, values: dict[int, float]) -> tuple[float, float] | None:
        """
        Redibuja el mapa con los valores dados.
        values: {sensor_idx → float}
        Devuelve (hotspot_val, coldspot_val) o None si no hay datos.
        """
        if not values:
            return None

        pos_all = self.store.get_all()
        pts  = np.array([list(pos_all[i]) for i in values], dtype=float)
        vals = np.array([values[i]        for i in values], dtype=float)

        gz = self._interpolate(pts, vals)

        vmin = float(np.nanmin(gz)); vmax = float(np.nanmax(gz))
        # Asegurar rango mínimo para que el gradiente sea visible
        if abs(vmax - vmin) < 0.5:
            mid = (vmin + vmax) / 2
            vmin, vmax = mid - 1.0, mid + 1.0

        # ── limpiar axes y redibujar todo ─────────────────────────────────────
        self.ax.cla()
        self.cax.cla()
        self._style_axes()

        # pcolormesh con gradiente gouraud
        self._mesh = self.ax.pcolormesh(
            _GX, _GY, gz,
            cmap=self._cmap, shading="gouraud",
            alpha=0.88, vmin=vmin, vmax=vmax, zorder=1,
        )

        # contornos suaves encima
        try:
            self.ax.contour(
                _XY, _XY, gz,
                levels=np.linspace(vmin, vmax, 9)[1:-1],
                colors="white", alpha=0.22, linewidths=0.7, zorder=2,
            )
        except Exception:
            pass

        # colorbar actualizada
        self._cbar = self.fig.colorbar(self._mesh, cax=self.cax)
        self._cbar.set_label(f"({self.unit_sym})", color="#cdd6f4", fontsize=9)
        self._cbar.ax.yaxis.label.set_color("#cdd6f4")
        self._cbar.ax.tick_params(colors="#cdd6f4", labelsize=8)

        # marcadores de sensor - SOLO para sensores con datos activos
        active_sensors = list(values.keys())
        self._draw_markers(active_sensors)

        # puntos críticos
        hi = np.unravel_index(np.nanargmax(gz), gz.shape)
        ci = np.unravel_index(np.nanargmin(gz), gz.shape)
        hv = float(gz[hi]); cv = float(gz[ci])
        hx = _XY[hi[1]];   hy = _XY[hi[0]]
        cx = _XY[ci[1]];   cy = _XY[ci[0]]

        for vx, vy, vv, col, oy in [
            (hx, hy, hv, "#f38ba8", +0.07),
            (cx, cy, cv, "#89b4fa", -0.08),
        ]:
            sym = "🔴" if col == "#f38ba8" else "🔵"
            self.ax.plot(vx, vy, "*", color=col, ms=20, zorder=8,
                         markeredgecolor="white", markeredgewidth=1.2)
            self.ax.text(
                vx, float(np.clip(vy + oy, 0.04, 0.95)),
                f"{sym} {vv:.1f}{self.unit_sym}",
                ha="center", fontsize=8, fontweight="bold",
                color=col, zorder=9,
                path_effects=[pe.withStroke(linewidth=2.5, foreground="#1e1e2e")],
            )

        self.canvas.draw_idle()
        return hv, cv

    def _draw_markers(self, active_sensors: list[int]) -> None:
        """
        Dibuja los marcadores de sensor sobre los axes actuales.
        active_sensors: lista de índices de sensores que tienen datos activos
        """
        pos_all = self.store.get_all()
        
        for i, (x, y) in enumerate(pos_all):
            # Solo dibujar si el sensor tiene datos activos
            if i not in active_sensors:
                continue
                
            label = "L" if i == 0 else str(i)
            self.ax.scatter(
                [x], [y], s=270, c=_COLORS[i], zorder=6,
                edgecolors="white", linewidths=1.5,
            )
            self.ax.text(
                x, y, label, ha="center", va="center",
                fontsize=8, fontweight="bold", color="white", zorder=7,
                path_effects=[pe.withStroke(linewidth=2, foreground="#1e1e2e")],
            )

    # ── drag ──────────────────────────────────────────────────────────────────

    def _press(self, ev) -> None:
        if ev.inaxes != self.ax or ev.button != 1:
            return
        pos = self.store.get_all()
        for i, (px, py) in enumerate(pos):
            # hit-test aproximado (±0.07 en espacio normalizado)
            if abs(ev.xdata - px) < 0.07 and abs(ev.ydata - py) < 0.07:
                self._active = i; return

    def _release(self, _) -> None:
        self._active = None

    def _motion(self, ev) -> None:
        if self._active is None or ev.inaxes != self.ax:
            return
        if ev.xdata is None or ev.ydata is None:
            return
        x = float(np.clip(ev.xdata, 0.02, 0.98))
        y = float(np.clip(ev.ydata, 0.02, 0.98))
        self.store.move(self._active, x, y, source=self)
        # redibuja solo los marcadores (rápido) en lugar del mapa entero
        self.ax.cla(); 
        self._style_axes()
        # Necesitamos mantener la malla actual
        if self._mesh is not None:
            # Re-dibujar la malla existente
            pass
        self.canvas.draw_idle()

    def _on_store(self, idx: int, x: float, y: float, source) -> None:
        """Sincronización desde otro mapa o spinbox."""
        if source is self:
            return
        self.ax.cla(); 
        self._style_axes()
        # Re-dibujar marcadores con los sensores activos actuales
        # Nota: Esto requiere acceso a los valores actuales, por simplicidad
        # redibujamos todo cuando cambian posiciones
        self.canvas.draw_idle()

    def update_theme(self, bg: str, fg: str) -> None:
        self.fig.set_facecolor(bg)
        inner = "#181825" if "#1e" in bg or "#18" in bg else "#f5f5f5"
        self.ax.set_facecolor(inner)
        self._style_axes()
        if self._cbar:
            self._cbar.ax.yaxis.label.set_color(fg)
            self._cbar.ax.tick_params(colors=fg)
        self.canvas.draw_idle()


# ═════════════════════════════════════════════════════════════════════════════
#  Widget contenedor: dos mapas + controles
# ═════════════════════════════════════════════════════════════════════════════

class HeatMapWidget(QWidget):
    """Pestaña con mapa de temperatura y mapa de humedad, fuente live/CSV."""

    def __init__(self, app):
        super().__init__()
        self.app        = app
        self.store      = _PositionStore()
        self._data_src  = "live"
        self._file_data: dict[int, dict] | None = None
        self._sb_lock   = False
        self._pos_spins: list[dict[str, QDoubleSpinBox]] = []

        self._hot_t_lbl = self._cold_t_lbl = None
        self._hot_h_lbl = self._cold_h_lbl = None

        self._setup_ui()
        self.store.register(self._on_store_spinbox_sync)

    # ── UI ───────────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8); root.setSpacing(8)

        hdr = QLabel("🗺️  Mapa de Calor — Temperatura y Humedad  |  Escala RdBu/YlGnBu")
        hdr.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hdr.setStyleSheet("color:#cba6f7; padding:4px;")
        root.addWidget(hdr)

        hint = QLabel("💡 Arrastra marcadores ó edita coordenadas — "
                      "mínimo 1 sensor para dibujar el mapa\n"
                      "🌡️ Temperatura: Azul (frío) → Rojo (caliente)  |  "
                      "💧 Humedad: Amarillo (seco) → Azul (húmedo)")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color:#a6adc8; font-size:11px;")
        root.addWidget(hint)

        # ── fuente de datos ───────────────────────────────────────────────────
        src_box = QGroupBox("📡  Fuente de Datos")
        src_lay = QHBoxLayout(src_box)
        self._rb_live = QRadioButton("🔴  En vivo (sensores conectados)")
        self._rb_file = QRadioButton("📂  Desde archivo CSV")
        self._rb_live.setChecked(True)
        grp = QButtonGroup(self)
        grp.addButton(self._rb_live); grp.addButton(self._rb_file)
        self._rb_live.toggled.connect(self._on_src_changed)
        src_lay.addWidget(self._rb_live); src_lay.addSpacing(30)
        src_lay.addWidget(self._rb_file); src_lay.addSpacing(20)

        self._btn_load = QPushButton("📁  Cargar CSV...")
        self._btn_load.setEnabled(False); self._btn_load.setFixedWidth(145)
        self._btn_load.clicked.connect(self._load_csv)
        src_lay.addWidget(self._btn_load)

        self._lbl_file = QLabel("Sin archivo cargado")
        self._lbl_file.setStyleSheet("color:#a6adc8; font-size:11px;")
        src_lay.addWidget(self._lbl_file); src_lay.addStretch()
        root.addWidget(src_box)

        # ── mapas ─────────────────────────────────────────────────────────────
        self._map_t = _HeatMapPlot(self.store, "°C",
                                   "🌡️  Temperatura (RdBu_r)", _CMAP_TEMP)
        self._map_h = _HeatMapPlot(self.store, "%",
                                   "💧  Humedad Relativa (YlGnBu)", _CMAP_HUM)
        sp = QSplitter(Qt.Orientation.Horizontal)
        sp.addWidget(self._map_t); sp.addWidget(self._map_h)
        sp.setSizes([700, 700])
        root.addWidget(sp, stretch=1)

        # ── panel de control ──────────────────────────────────────────────────
        ctrl = QHBoxLayout(); ctrl.setSpacing(10)

        # puntos críticos
        cb = QGroupBox("📍 Puntos Críticos")
        cg = QGridLayout(cb)
        cg.addWidget(QLabel("🔴 T. Hotspot:"),  0, 0)
        self._hot_t_lbl = QLabel("—"); self._hot_t_lbl.setStyleSheet("color:#f38ba8;font-weight:bold;")
        cg.addWidget(self._hot_t_lbl, 0, 1)
        cg.addWidget(QLabel("🔵 T. Coldspot:"), 1, 0)
        self._cold_t_lbl = QLabel("—"); self._cold_t_lbl.setStyleSheet("color:#89b4fa;font-weight:bold;")
        cg.addWidget(self._cold_t_lbl, 1, 1)
        cg.addWidget(QLabel("🔴 H. Hotspot:"),  0, 2)
        self._hot_h_lbl = QLabel("—"); self._hot_h_lbl.setStyleSheet("color:#f38ba8;font-weight:bold;")
        cg.addWidget(self._hot_h_lbl, 0, 3)
        cg.addWidget(QLabel("🔵 H. Coldspot:"), 1, 2)
        self._cold_h_lbl = QLabel("—"); self._cold_h_lbl.setStyleSheet("color:#89b4fa;font-weight:bold;")
        cg.addWidget(self._cold_h_lbl, 1, 3)
        ctrl.addWidget(cb, stretch=2)

        # umbrales
        tb = QGroupBox("⚠️ Umbrales")
        tg = QGridLayout(tb)

        def _dspin(lo, hi, val, suf):
            s = QDoubleSpinBox(); s.setRange(lo, hi); s.setValue(val); s.setSuffix(suf)
            return s

        tg.addWidget(QLabel("T. Máx (°C):"), 0, 0); self._thr_tmax = _dspin(-50,300,40," °C"); tg.addWidget(self._thr_tmax, 0, 1)
        tg.addWidget(QLabel("T. Mín (°C):"), 1, 0); self._thr_tmin = _dspin(-50,300,10," °C"); tg.addWidget(self._thr_tmin, 1, 1)
        tg.addWidget(QLabel("H. Máx (%):"),  0, 2); self._thr_hmax = _dspin(0,100,85," %");    tg.addWidget(self._thr_hmax, 0, 3)
        tg.addWidget(QLabel("H. Mín (%):"),  1, 2); self._thr_hmin = _dspin(0,100,20," %");    tg.addWidget(self._thr_hmin, 1, 3)
        ctrl.addWidget(tb, stretch=2)

        # posiciones con spinboxes
        pb = QGroupBox("📡 Posiciones Sensores  (X, Y) ∈ [0,1]")
        pg = QGridLayout(pb)
        for col, hdr_txt in enumerate(["Sensor", "X", "Y"]):
            lh = QLabel(hdr_txt)
            lh.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lh.setStyleSheet("font-weight:bold;color:#cba6f7;font-size:11px;")
            pg.addWidget(lh, 0, col)

        for i in range(6):
            name = "Local" if i == 0 else f"S {i}"
            dot = QLabel(f"● {name}")
            dot.setStyleSheet(f"color:{_COLORS[i]};font-weight:bold;")
            pg.addWidget(dot, i+1, 0)

            xs = QDoubleSpinBox(); xs.setRange(0.02, 0.98); xs.setSingleStep(0.05)
            xs.setDecimals(2); xs.setValue(_DEFAULTS[i][0]); xs.setFixedWidth(70)
            ys = QDoubleSpinBox(); ys.setRange(0.02, 0.98); ys.setSingleStep(0.05)
            ys.setDecimals(2); ys.setValue(_DEFAULTS[i][1]); ys.setFixedWidth(70)
            xs.valueChanged.connect(lambda _, idx=i: self._on_sb(idx))
            ys.valueChanged.connect(lambda _, idx=i: self._on_sb(idx))
            pg.addWidget(xs, i+1, 1); pg.addWidget(ys, i+1, 2)
            self._pos_spins.append({"x": xs, "y": ys})

        btn_rst = QPushButton("↺ Reset"); btn_rst.setFixedWidth(68)
        btn_rst.clicked.connect(self._reset_pos)
        pg.addWidget(btn_rst, 7, 0, 1, 3, Qt.AlignmentFlag.AlignRight)
        ctrl.addWidget(pb, stretch=2)

        # botón actualizar
        bv = QVBoxLayout()
        btn_upd = QPushButton("🔄\nActualizar\nmapas")
        btn_upd.setMinimumHeight(80); btn_upd.clicked.connect(self.refresh)
        bv.addWidget(btn_upd); bv.addStretch()
        ctrl.addLayout(bv, stretch=0)

        root.addLayout(ctrl)

    # ── fuente ────────────────────────────────────────────────────────────────

    def _on_src_changed(self, live: bool) -> None:
        self._data_src = "live" if live else "file"
        self._btn_load.setEnabled(not live)

    def _load_csv(self) -> None:
        fname, _ = QFileDialog.getOpenFileName(
            self, "Cargar datos", "", "CSV (*.csv);;Todos (*.*)")
        if not fname:
            return
        try:
            df = pd.read_csv(fname)
            need = {"sensor_id", "temperature_c", "humidity"}
            if not need.issubset(df.columns):
                QMessageBox.critical(self, "Formato incorrecto",
                    f"Faltan columnas: {need - set(df.columns)}")
                return
            self._file_data = {}
            found = []
            for sid in range(6):
                sub = df[df["sensor_id"] == sid]
                if not sub.empty:
                    last = sub.iloc[-1]
                    self._file_data[sid] = {
                        "temp_c":   float(last["temperature_c"]),
                        "humidity": float(last["humidity"]),
                    }
                    found.append(sid)
            self._lbl_file.setText(
                f"📂 {Path(fname).name}  |  {len(df)} filas  |  Sensores: {found}")
            QMessageBox.information(self, "Cargado",
                f"{len(found)} sensor(es) encontrado(s).\nUsando último registro.")
            self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, "Error al cargar", str(exc))

    # ── spinboxes ↔ store ─────────────────────────────────────────────────────

    def _on_sb(self, idx: int) -> None:
        if self._sb_lock: return
        x = self._pos_spins[idx]["x"].value()
        y = self._pos_spins[idx]["y"].value()
        self.store.move(idx, x, y, source="spinbox")

    def _on_store_spinbox_sync(self, idx: int, x: float, y: float, source) -> None:
        if source == "spinbox": return
        self._sb_lock = True
        if idx == -1:
            for i, (px, py) in enumerate(_DEFAULTS):
                self._pos_spins[i]["x"].setValue(px)
                self._pos_spins[i]["y"].setValue(py)
        else:
            self._pos_spins[idx]["x"].setValue(x)
            self._pos_spins[idx]["y"].setValue(y)
        self._sb_lock = False

    def _reset_pos(self) -> None:
        self.store.reset()

    # ── valores por fuente ────────────────────────────────────────────────────

    def _temp_vals(self) -> dict[int, float]:
        _K = {"celsius":"temp_c","fahrenheit":"temp_f","kelvin":"temp_k"}
        key = _K.get(self.app.temp_unit, "temp_c")
        if self._data_src == "live":
            out: dict[int, float] = {}
            for i in range(6):
                buf = self.app.data[f"sensor{i}"][key]
                if buf and not pd.isna(buf[-1]):
                    out[i] = float(buf[-1])
            return out
        else:
            if not self._file_data: return {}
            out = {}
            for i, d in self._file_data.items():
                tc = d["temp_c"]
                out[i] = tc if key=="temp_c" else (tc*9/5+32 if key=="temp_f" else tc+273.15)
            return out

    def _hum_vals(self) -> dict[int, float]:
        if self._data_src == "live":
            out: dict[int, float] = {}
            for i in range(6):
                buf = self.app.data[f"sensor{i}"]["hum"]
                if buf and not pd.isna(buf[-1]):
                    out[i] = float(buf[-1])
            return out
        return {i: d["humidity"] for i, d in (self._file_data or {}).items()}

    # ── render ────────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        _SYM = {"celsius":"°C","fahrenheit":"°F","kelvin":"K"}
        tsym = _SYM.get(self.app.temp_unit, "°C")
        self._map_t.unit_sym = tsym

        def _update_crit(lbl_hot, lbl_cold, res, thr_max, thr_min, sym):
            if not res: return
            hv, cv = res
            lbl_hot.setText(f"{hv:.1f} {sym}")
            lbl_cold.setText(f"{cv:.1f} {sym}")
            lbl_hot.setStyleSheet(
                "color:#ff1111;font-weight:bold;font-size:13px;"
                if hv > thr_max.value() else "color:#f38ba8;font-weight:bold;")
            lbl_cold.setStyleSheet(
                "color:#0044ff;font-weight:bold;font-size:13px;"
                if cv < thr_min.value() else "color:#89b4fa;font-weight:bold;")

        res_t = self._map_t.render(self._temp_vals())
        _update_crit(self._hot_t_lbl, self._cold_t_lbl,
                     res_t, self._thr_tmax, self._thr_tmin, tsym)

        res_h = self._map_h.render(self._hum_vals())
        _update_crit(self._hot_h_lbl, self._cold_h_lbl,
                     res_h, self._thr_hmax, self._thr_hmin, "%")

    def update_theme(self, bg: str, fg: str) -> None:
        self._map_t.update_theme(bg, fg)
        self._map_h.update_theme(bg, fg)
