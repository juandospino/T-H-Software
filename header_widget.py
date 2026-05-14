"""
header_widget.py — Encabezado personalizado con iconos y título centrado.
Permite editar el icono del programa, el título y mostrar dos logos al lado.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QFileDialog, QMessageBox, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QFont, QIcon
from PyQt6.QtCore import Qt


class HeaderWidget(QWidget):
    """
    Encabezado centrado con estructura:
    [Logo Izq] [Icono + Título] [Logos Derechos] [Botón Tema]
    
    El título está centrado con iconos a los lados.
    Permite editar el icono principal y cargar logos.
    """

    def __init__(self, parent=None, title_text: str = "Monitor de T°H", 
                 icon_path: str | Path | None = None,
                 left_logos: list[tuple[Path | str, int]] | None = None,
                 right_logos: list[tuple[Path | str, int]] | None = None):
        super().__init__(parent)
        self.setObjectName("HeaderWidget")
        
        self._icon_path = Path(icon_path) if icon_path else None
        self._title_text = title_text
        self._left_logos = left_logos or []
        self._right_logos = right_logos or []
        
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(16, 10, 16, 10)
        self._layout.setSpacing(14)
        
        self._icon_lbl = None
        self._title_lbl = None
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        # Sección izquierda: logos
        if self._left_logos:
            for logo_path, size in self._left_logos:
                self._add_logo(logo_path, size)
            self._layout.addSpacing(10)

        # Centro: icono + título (centrado)
        center_layout = QHBoxLayout()
        center_layout.setSpacing(16)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        # Icono principal (editable)
        if self._icon_path and self._icon_path.exists():
            self._icon_lbl = QLabel()
            px = QPixmap(str(self._icon_path))
            if not px.isNull():
                px = px.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
                self._icon_lbl.setPixmap(px)
                self._icon_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
                self._icon_lbl.setToolTip("Click para cambiar icono")
                self._icon_lbl.mousePressEvent = self._on_icon_click
                center_layout.addWidget(self._icon_lbl)
        
        # Título en grande
        self._title_lbl = QLabel(self._title_text)
        self._title_lbl.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
        center_layout.addWidget(self._title_lbl)
        
        self._layout.addLayout(center_layout, stretch=1)
        
        # Sección derecha: logos
        if self._right_logos:
            self._layout.addSpacing(10)
            for logo_path, size in self._right_logos:
                self._add_logo(logo_path, size)
        
        self._layout.addStretch()

    def _add_logo(self, logo_path: Path | str, size: int) -> None:
        """Agrega un logo al layout."""
        try:
            px = QPixmap(str(logo_path))
            if not px.isNull():
                px = px.scaled(size, size, 
                              Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
                lbl = QLabel()
                lbl.setPixmap(px)
                lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
                self._layout.addWidget(lbl)
        except Exception as e:
            print(f"[HeaderWidget] Error cargando logo {logo_path}: {e}")

    def _on_icon_click(self, event) -> None:
        """Permite cambiar el icono haciendo click."""
        fname, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Icono", "",
            "Imágenes (*.png *.jpg *.jpeg *.ico);;Todos (*.*)")
        if fname:
            if self.set_icon(fname):
                QMessageBox.information(self, "Éxito", "Icono actualizado.")
            else:
                QMessageBox.critical(self, "Error", "No se pudo cargar la imagen.")

    def set_title_color(self, color: str) -> None:
        """Cambia el color del título."""
        self._title_lbl.setStyleSheet(f"color: {color};")

    def add_theme_button(self, on_click_callback) -> QPushButton:
        """Agrega un botón de tema al encabezado."""
        btn = QPushButton("☀️ Modo Claro")
        btn.setObjectName("ThemeBtn")
        btn.setFixedWidth(135)
        btn.clicked.connect(on_click_callback)
        self._layout.addWidget(btn)
        return btn

    def set_title_text(self, text: str) -> None:
        """Actualiza el texto del título."""
        self._title_text = text
        self._title_lbl.setText(text)

    def set_icon(self, icon_path: str | Path) -> bool:
        """
        Cambia el icono principal.
        Retorna True si fue exitoso, False si hubo error.
        """
        try:
            path = Path(icon_path)
            if not path.exists():
                return False
            px = QPixmap(str(path))
            if px.isNull():
                return False
            self._icon_path = path
            # Actualizar el label del icono
            if self._icon_lbl:
                px = px.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
                self._icon_lbl.setPixmap(px)
            return True
        except Exception as e:
            print(f"[HeaderWidget] Error al establecer icono: {e}")
            return False

    def update_theme(self, bg: str, fg: str) -> None:
        """Actualiza el tema del encabezado."""
        self.setStyleSheet(f"""
            QWidget#HeaderWidget {{
                background: {bg};
                border-bottom: 1px solid {fg}22;
            }}
        """)
        self.set_title_color(fg)
