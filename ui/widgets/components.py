"""Reusable minimal UI components: StatusIndicator, SectionHeader, HairlineDivider."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from ui.icons import svg_pixmap
from ui.theme import Tokens


class HairlineDivider(QFrame):
    """1px subtle horizontal separator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("divider")
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(1)


class StatusIndicator(QWidget):
    """Minimal 6px status dot + crisp label for tool health."""

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self._active = True
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._dot = QFrame(self)
        self._dot.setFixedSize(6, 6)
        layout.addWidget(self._dot)

        self._lbl = QLabel(label, self)
        layout.addWidget(self._lbl)
        self.set_active(True)

    def set_active(self, active: bool):
        self._active = active
        self.refresh_theme()

    def refresh_theme(self):
        color = Tokens.SUCCESS if self._active else Tokens.ERROR
        text_color = Tokens.TEXT_SECONDARY if self._active else Tokens.ERROR
        self._dot.setStyleSheet(f"background-color: {color}; border-radius: 3px; border: none;")
        self._lbl.setStyleSheet(
            f"color: {text_color}; font-size: 11px; font-weight: 500; background: transparent;"
        )


class SectionHeader(QWidget):
    """Clean section header with vector icon, tracked uppercase title, and optional right widget."""

    def __init__(self, icon_name: str, title: str, right_widget: QWidget | None = None, parent=None):
        super().__init__(parent)
        self._icon_name = icon_name
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._icon_lbl = QLabel(self)
        self._icon_lbl.setFixedSize(14, 14)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._icon_lbl)

        title_lbl = QLabel(title, self)
        title_lbl.setObjectName("sectionTitle")
        layout.addWidget(title_lbl)

        layout.addStretch()
        if right_widget is not None:
            layout.addWidget(right_widget)

        self.refresh_theme()

    def refresh_theme(self):
        self._icon_lbl.setPixmap(svg_pixmap(self._icon_name, color=Tokens.TEXT_MUTED, size=13))
