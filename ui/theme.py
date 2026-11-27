"""Minimalist Night & Day theme tokens and QSS builder inspired by Linear, Arc, and modern macOS."""
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

_DARK_PALETTE: dict[str, str] = {
    "BG_APP": "#0D0F12",
    "BG_SURFACE": "#13161B",
    "BG_INPUT": "#181C22",
    "BG_HOVER": "#1E232B",
    "BG_ACTIVE": "#242A34",
    "BG_BADGE": "#1B1F27",
    "BORDER": "#232730",
    "BORDER_SUBTLE": "#1C2028",
    "BORDER_HOVER": "#323846",
    "TEXT_PRIMARY": "#F4F5F7",
    "TEXT_SECONDARY": "#9BA1A6",
    "TEXT_MUTED": "#687076",
    "TEXT_DISABLED": "#4A5056",
    "ACCENT": "#5E6AD2",
    "ACCENT_HOVER": "#6C78E0",
    "ACCENT_PRESSED": "#4E59B8",
    "ACCENT_TEXT": "#8F99F0",
    "SUCCESS": "#34D399",
    "SUCCESS_MUTED": "#122B22",
    "WARNING": "#FBBF24",
    "ERROR": "#F87171",
    "ERROR_BG": "#2A1619",
    "ERROR_BORDER": "#4B2227",
    "INFO": "#60A5FA",
}

_LIGHT_PALETTE: dict[str, str] = {
    "BG_APP": "#F6F7F9",
    "BG_SURFACE": "#FFFFFF",
    "BG_INPUT": "#F0F2F5",
    "BG_HOVER": "#E6E9EF",
    "BG_ACTIVE": "#DCE0E8",
    "BG_BADGE": "#EEF0F4",
    "BORDER": "#E2E5EC",
    "BORDER_SUBTLE": "#ECEEF3",
    "BORDER_HOVER": "#C8CEDB",
    "TEXT_PRIMARY": "#111827",
    "TEXT_SECONDARY": "#4B5563",
    "TEXT_MUTED": "#6B7280",
    "TEXT_DISABLED": "#9CA3AF",
    "ACCENT": "#5E6AD2",
    "ACCENT_HOVER": "#4E59B8",
    "ACCENT_PRESSED": "#424CA3",
    "ACCENT_TEXT": "#4E59B8",
    "SUCCESS": "#16A34A",
    "SUCCESS_MUTED": "#DCFCE7",
    "WARNING": "#D97706",
    "ERROR": "#DC2626",
    "ERROR_BG": "#FEF2F2",
    "ERROR_BORDER": "#FECACA",
    "INFO": "#2563EB",
}


class Tokens:
    """Centralized active design tokens for surfaces, borders, text, and accents."""

    MODE = "dark"

    BG_APP = _DARK_PALETTE["BG_APP"]
    BG_SURFACE = _DARK_PALETTE["BG_SURFACE"]
    BG_INPUT = _DARK_PALETTE["BG_INPUT"]
    BG_HOVER = _DARK_PALETTE["BG_HOVER"]
    BG_ACTIVE = _DARK_PALETTE["BG_ACTIVE"]
    BG_BADGE = _DARK_PALETTE["BG_BADGE"]

    BORDER = _DARK_PALETTE["BORDER"]
    BORDER_SUBTLE = _DARK_PALETTE["BORDER_SUBTLE"]
    BORDER_HOVER = _DARK_PALETTE["BORDER_HOVER"]

    TEXT_PRIMARY = _DARK_PALETTE["TEXT_PRIMARY"]
    TEXT_SECONDARY = _DARK_PALETTE["TEXT_SECONDARY"]
    TEXT_MUTED = _DARK_PALETTE["TEXT_MUTED"]
    TEXT_DISABLED = _DARK_PALETTE["TEXT_DISABLED"]

    ACCENT = _DARK_PALETTE["ACCENT"]
    ACCENT_HOVER = _DARK_PALETTE["ACCENT_HOVER"]
    ACCENT_PRESSED = _DARK_PALETTE["ACCENT_PRESSED"]
    ACCENT_TEXT = _DARK_PALETTE["ACCENT_TEXT"]

    SUCCESS = _DARK_PALETTE["SUCCESS"]
    SUCCESS_MUTED = _DARK_PALETTE["SUCCESS_MUTED"]
    WARNING = _DARK_PALETTE["WARNING"]
    ERROR = _DARK_PALETTE["ERROR"]
    ERROR_BG = _DARK_PALETTE["ERROR_BG"]
    ERROR_BORDER = _DARK_PALETTE["ERROR_BORDER"]
    INFO = _DARK_PALETTE["INFO"]

    FONT_UI = "'Segoe UI Variable', 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif"
    FONT_MONO = "'JetBrains Mono', 'Cascadia Mono', 'Consolas', monospace"

    RADIUS_SM = "4px"
    RADIUS_MD = "6px"
    RADIUS_LG = "8px"


def set_theme_mode(mode: str) -> str:
    """Switches active Tokens between 'dark' (Night) and 'light' (Day)."""
    normalized = "light" if mode == "light" else "dark"
    palette = _LIGHT_PALETTE if normalized == "light" else _DARK_PALETTE
    Tokens.MODE = normalized
    for key, val in palette.items():
        setattr(Tokens, key, val)
    return normalized


def build_stylesheet(mode: str | None = None) -> str:
    """Generates the application-wide Qt StyleSheet from active Tokens."""
    if mode is not None:
        set_theme_mode(mode)
    t = Tokens
    return f"""
QMainWindow, QDialog, QWidget {{
    background-color: {t.BG_APP};
    color: {t.TEXT_PRIMARY};
    font-family: {t.FONT_UI};
    font-size: 13px;
}}

/* Section & Panel Surfaces */
QFrame#panel {{
    background-color: {t.BG_SURFACE};
    border: 1px solid {t.BORDER};
    border-radius: {t.RADIUS_LG};
}}

QFrame#metaStrip {{
    background-color: {t.BG_INPUT};
    border: 1px solid {t.BORDER};
    border-radius: {t.RADIUS_MD};
}}

QFrame#divider {{
    background-color: {t.BORDER_SUBTLE};
    border: none;
    max-height: 1px;
    min-height: 1px;
}}

QFrame#bottomBar {{
    background-color: {t.BG_SURFACE};
    border-top: 1px solid {t.BORDER};
    border-left: none;
    border-right: none;
    border-bottom: none;
}}

QFrame#topBar {{
    background-color: {t.BG_APP};
    border-bottom: 1px solid {t.BORDER};
}}

/* Typography Roles */
QLabel#brandTitle {{
    color: {t.TEXT_PRIMARY};
    font-size: 14px;
    font-weight: 600;
    letter-spacing: -0.2px;
    background: transparent;
}}

QLabel#sectionTitle {{
    color: {t.TEXT_SECONDARY};
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    background: transparent;
}}

QLabel#fieldLabel {{
    color: {t.TEXT_SECONDARY};
    font-size: 12px;
    font-weight: 500;
    background: transparent;
}}

QLabel#mutedText {{
    color: {t.TEXT_MUTED};
    font-size: 11px;
    background: transparent;
}}

QLabel#monoBadge {{
    color: {t.TEXT_PRIMARY};
    background-color: {t.BG_INPUT};
    border: 1px solid {t.BORDER};
    border-radius: {t.RADIUS_SM};
    padding: 2px 8px;
    font-family: {t.FONT_MONO};
    font-size: 11px;
    font-weight: 500;
}}

QLabel#monoText {{
    color: {t.TEXT_MUTED};
    font-family: {t.FONT_MONO};
    font-size: 11px;
    background: transparent;
}}

/* Inputs */
QLineEdit {{
    background-color: {t.BG_INPUT};
    color: {t.TEXT_PRIMARY};
    border: 1px solid {t.BORDER};
    border-radius: {t.RADIUS_MD};
    padding: 4px 10px;
    font-size: 13px;
    min-height: 28px;
    selection-background-color: {t.ACCENT};
    selection-color: #FFFFFF;
}}
QLineEdit#monoInput {{
    font-family: {t.FONT_MONO};
    font-size: 12px;
    padding: 3px 8px;
}}
QLineEdit:hover {{
    border-color: {t.BORDER_HOVER};
}}
QLineEdit:focus {{
    border: 1px solid {t.ACCENT};
    background-color: {t.BG_SURFACE};
}}
QLineEdit:disabled {{
    background-color: {t.BG_APP};
    color: {t.TEXT_DISABLED};
    border-color: {t.BORDER_SUBTLE};
}}

/* Dropdowns */
QComboBox {{
    background-color: {t.BG_INPUT};
    color: {t.TEXT_PRIMARY};
    border: 1px solid {t.BORDER};
    border-radius: {t.RADIUS_MD};
    padding: 4px 10px;
    min-height: 28px;
    font-size: 12px;
}}
QComboBox:hover {{
    border-color: {t.BORDER_HOVER};
    background-color: {t.BG_HOVER};
}}
QComboBox:focus {{
    border-color: {t.ACCENT};
}}
QComboBox:disabled {{
    background-color: {t.BG_APP};
    color: {t.TEXT_DISABLED};
    border-color: {t.BORDER_SUBTLE};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox QAbstractItemView {{
    background-color: {t.BG_SURFACE};
    border: 1px solid {t.BORDER_HOVER};
    border-radius: {t.RADIUS_MD};
    selection-background-color: {t.BG_ACTIVE};
    selection-color: {t.TEXT_PRIMARY};
    color: {t.TEXT_PRIMARY};
    padding: 4px;
    outline: none;
}}

/* Buttons */
QPushButton {{
    background-color: {t.BG_INPUT};
    color: {t.TEXT_PRIMARY};
    border: 1px solid {t.BORDER};
    border-radius: {t.RADIUS_MD};
    padding: 4px 12px;
    font-weight: 500;
    font-size: 12px;
    min-height: 28px;
}}
QPushButton:hover {{
    background-color: {t.BG_HOVER};
    border-color: {t.BORDER_HOVER};
}}
QPushButton:pressed {{
    background-color: {t.BG_ACTIVE};
}}
QPushButton:focus {{
    border-color: {t.ACCENT};
}}
QPushButton:disabled {{
    background-color: {t.BG_APP};
    color: {t.TEXT_DISABLED};
    border-color: {t.BORDER_SUBTLE};
}}

QPushButton#ghostBtn {{
    background-color: transparent;
    color: {t.TEXT_SECONDARY};
    border: 1px solid transparent;
    border-radius: {t.RADIUS_SM};
    padding: 3px 8px;
    font-size: 12px;
    min-height: 24px;
}}
QPushButton#ghostBtn:hover {{
    background-color: {t.BG_HOVER};
    color: {t.TEXT_PRIMARY};
    border-color: {t.BORDER};
}}

QPushButton#pillBtn {{
    background-color: {t.BG_INPUT};
    color: {t.TEXT_SECONDARY};
    border: 1px solid {t.BORDER};
    border-radius: {t.RADIUS_SM};
    padding: 2px 8px;
    font-family: {t.FONT_MONO};
    font-size: 11px;
    font-weight: 500;
    min-height: 22px;
}}
QPushButton#pillBtn:hover {{
    background-color: {t.BG_HOVER};
    border-color: {t.BORDER_HOVER};
    color: {t.TEXT_PRIMARY};
}}

QPushButton#primaryBtn {{
    background-color: {t.ACCENT};
    color: #FFFFFF;
    border: 1px solid {t.ACCENT};
    border-radius: {t.RADIUS_MD};
    padding: 5px 18px;
    font-weight: 600;
    font-size: 13px;
    min-height: 30px;
}}
QPushButton#primaryBtn:hover {{
    background-color: {t.ACCENT_HOVER};
    border-color: {t.ACCENT_HOVER};
}}
QPushButton#primaryBtn:pressed {{
    background-color: {t.ACCENT_PRESSED};
}}
QPushButton#primaryBtn:disabled {{
    background-color: {t.BG_INPUT};
    color: {t.TEXT_DISABLED};
    border-color: {t.BORDER_SUBTLE};
}}

QPushButton#dangerBtn {{
    background-color: transparent;
    color: {t.TEXT_SECONDARY};
    border: 1px solid {t.BORDER};
    border-radius: {t.RADIUS_MD};
    padding: 5px 14px;
    font-weight: 500;
    font-size: 12px;
    min-height: 30px;
}}
QPushButton#dangerBtn:hover {{
    background-color: {t.ERROR_BG};
    color: {t.ERROR};
    border-color: {t.ERROR_BORDER};
}}
QPushButton#dangerBtn:disabled {{
    color: {t.TEXT_DISABLED};
    border-color: {t.BORDER_SUBTLE};
    background-color: transparent;
}}

QPushButton#iconBtn {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: {t.RADIUS_SM};
    padding: 2px;
    min-height: 22px;
}}
QPushButton#iconBtn:hover {{
    background-color: {t.ERROR_BG};
    border-color: {t.ERROR_BORDER};
}}

/* Tables (Queue & Diagnostics) */
QTableWidget {{
    background-color: transparent;
    border: none;
    gridline-color: transparent;
    outline: none;
    selection-background-color: {t.BG_HOVER};
    selection-color: {t.TEXT_PRIMARY};
    font-size: 12px;
}}
QTableWidget::item {{
    padding: 6px 8px;
    border-bottom: 1px solid {t.BORDER_SUBTLE};
}}
QHeaderView::section {{
    background-color: transparent;
    color: {t.TEXT_MUTED};
    padding: 6px 8px;
    border: none;
    border-bottom: 1px solid {t.BORDER};
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

/* Log Viewer */
QPlainTextEdit {{
    background-color: {t.BG_APP};
    color: {t.TEXT_SECONDARY};
    border: 1px solid {t.BORDER_SUBTLE};
    border-radius: {t.RADIUS_MD};
    padding: 8px;
    font-family: {t.FONT_MONO};
    font-size: 11px;
}}

/* Menus */
QMenu {{
    background-color: {t.BG_SURFACE};
    border: 1px solid {t.BORDER_HOVER};
    border-radius: {t.RADIUS_MD};
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 14px 6px 10px;
    border-radius: {t.RADIUS_SM};
    color: {t.TEXT_PRIMARY};
    font-size: 12px;
}}
QMenu::item:selected {{
    background-color: {t.BG_HOVER};
}}
QMenu::separator {{
    height: 1px;
    background: {t.BORDER_SUBTLE};
    margin: 4px 6px;
}}

/* Splitter */
QSplitter::handle {{
    background-color: {t.BORDER_SUBTLE};
    width: 1px;
}}
QSplitter::handle:hover {{
    background-color: {t.ACCENT};
}}

/* Flat Progress Bar */
QProgressBar {{
    background-color: {t.BG_INPUT};
    border: none;
    border-radius: 2px;
    text-align: center;
    color: transparent;
    height: 4px;
    max-height: 4px;
}}
QProgressBar::chunk {{
    background-color: {t.ACCENT};
    border-radius: 2px;
}}

/* ScrollArea & ScrollBars */
QScrollArea {{
    background-color: transparent;
    border: none;
}}
QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {t.BORDER};
    min-height: 24px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{
    background: {t.BORDER_HOVER};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    border: none;
    background: none;
}}
QScrollBar:horizontal {{
    height: 6px;
    background: transparent;
}}
QScrollBar::handle:horizontal {{
    background: {t.BORDER};
    border-radius: 3px;
}}

/* Status Bar */
QStatusBar {{
    background-color: {t.BG_APP};
    color: {t.TEXT_MUTED};
    border-top: 1px solid {t.BORDER_SUBTLE};
    font-size: 11px;
    padding: 3px 12px;
}}

QToolTip {{
    background-color: {t.BG_SURFACE};
    color: {t.TEXT_PRIMARY};
    border: 1px solid {t.BORDER_HOVER};
    border-radius: {t.RADIUS_SM};
    padding: 4px 8px;
    font-size: 11px;
}}
"""


def apply_palette(app: QApplication, mode: str | None = None) -> None:
    """Applies the active QPalette so native widgets and popups match Tokens."""
    if mode is not None:
        set_theme_mode(mode)
    t = Tokens
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(t.BG_APP))
    p.setColor(QPalette.ColorRole.WindowText, QColor(t.TEXT_PRIMARY))
    p.setColor(QPalette.ColorRole.Base, QColor(t.BG_INPUT))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(t.BG_SURFACE))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(t.BG_SURFACE))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor(t.TEXT_PRIMARY))
    p.setColor(QPalette.ColorRole.Text, QColor(t.TEXT_PRIMARY))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor(t.TEXT_MUTED))
    p.setColor(QPalette.ColorRole.BrightText, QColor(t.TEXT_PRIMARY))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(t.TEXT_PRIMARY))
    p.setColor(QPalette.ColorRole.Button, QColor(t.BG_INPUT))
    p.setColor(QPalette.ColorRole.Highlight, QColor(t.ACCENT))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(t.TEXT_DISABLED))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(t.TEXT_DISABLED))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(t.TEXT_DISABLED))
    app.setPalette(p)


def apply_dark_palette(app: QApplication) -> None:
    """Backward-compatible alias for applying the active palette."""
    apply_palette(app)
