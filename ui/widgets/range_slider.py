"""Dual-handle range slider for visual clip trimming."""
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QMouseEvent, QPaintEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ui.theme import Tokens


class RangeSlider(QWidget):
    """
    Minimalist dual-handle range slider for video clipping.
    - Left handle adjusts Start time.
    - Right handle adjusts End time.
    - Middle active bar can be dragged to slide the selected window.
    - Clicking the track jumps the nearest handle.
    - Emits rangeChanged(float, float) in seconds.
    """

    rangeChanged = Signal(float, float)
    lowChanged = Signal(float)
    highChanged = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._min_val = 0.0
        self._max_val = 600.0  # 10 min default until video duration loads
        self._low_val = 0.0
        self._high_val = 60.0  # default 1 min selection
        self._min_gap = 1.0    # 1 second minimum clip length

        self._handle_r = 6.5
        self._hover_target: str | None = None
        self._active_target: str | None = None
        self._drag_start_x = 0.0
        self._drag_start_low = 0.0
        self._drag_start_high = 0.0

    def setRange(self, min_val: float, max_val: float):
        self._min_val = max(0.0, float(min_val))
        self._max_val = max(self._min_val + self._min_gap, float(max_val))
        self._low_val = max(self._min_val, min(self._low_val, self._max_val - self._min_gap))
        self._high_val = max(self._low_val + self._min_gap, min(self._high_val, self._max_val))
        self.update()

    def setValues(self, low: float, high: float):
        low = max(self._min_val, min(float(low), self._max_val - self._min_gap))
        high = max(low + self._min_gap, min(float(high), self._max_val))
        if abs(low - self._low_val) > 0.01 or abs(high - self._high_val) > 0.01:
            self._low_val = low
            self._high_val = high
            self.update()

    def setLow(self, low: float):
        self.setValues(low, self._high_val)

    def setHigh(self, high: float):
        self.setValues(self._low_val, high)

    def low(self) -> float:
        return self._low_val

    def high(self) -> float:
        return self._high_val

    def _val_to_x(self, val: float) -> float:
        pad = self._handle_r + 4.0
        track_w = max(1.0, float(self.width()) - 2.0 * pad)
        span = max(0.001, self._max_val - self._min_val)
        ratio = max(0.0, min(1.0, (val - self._min_val) / span))
        return pad + ratio * track_w

    def _x_to_val(self, x: float) -> float:
        pad = self._handle_r + 4.0
        track_w = max(1.0, float(self.width()) - 2.0 * pad)
        ratio = max(0.0, min(1.0, (x - pad) / track_w))
        return self._min_val + ratio * (self._max_val - self._min_val)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        pos = event.position()
        x = pos.x()
        y = pos.y()
        cy = self.height() / 2.0

        x_low = self._val_to_x(self._low_val)
        x_high = self._val_to_x(self._high_val)

        dist_low = abs(x - x_low)
        dist_high = abs(x - x_high)
        hit_tol = self._handle_r + 6.0

        if dist_low <= hit_tol and dist_low <= dist_high:
            self._active_target = "low"
        elif dist_high <= hit_tol:
            self._active_target = "high"
        elif x_low < x < x_high and abs(y - cy) <= 11.0:
            self._active_target = "bar"
            self._drag_start_x = x
            self._drag_start_low = self._low_val
            self._drag_start_high = self._high_val
        else:
            if x < x_low:
                self._active_target = "low"
                new_low = max(self._min_val, min(self._x_to_val(x), self._high_val - self._min_gap))
                self._low_val = new_low
                self.rangeChanged.emit(self._low_val, self._high_val)
                self.lowChanged.emit(self._low_val)
            elif x > x_high:
                self._active_target = "high"
                new_high = min(self._max_val, max(self._x_to_val(x), self._low_val + self._min_gap))
                self._high_val = new_high
                self.rangeChanged.emit(self._low_val, self._high_val)
                self.highChanged.emit(self._high_val)
            else:
                self._active_target = "low" if dist_low <= dist_high else "high"

        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position()
        x = pos.x()
        y = pos.y()
        cy = self.height() / 2.0

        if self._active_target is None:
            x_low = self._val_to_x(self._low_val)
            x_high = self._val_to_x(self._high_val)
            dist_low = abs(x - x_low)
            dist_high = abs(x - x_high)
            hit_tol = self._handle_r + 6.0

            old_hover = self._hover_target
            if dist_low <= hit_tol and dist_low <= dist_high:
                self._hover_target = "low"
            elif dist_high <= hit_tol:
                self._hover_target = "high"
            elif x_low < x < x_high and abs(y - cy) <= 11.0:
                self._hover_target = "bar"
            else:
                self._hover_target = None

            if self._hover_target != old_hover:
                self.setCursor(
                    Qt.CursorShape.SizeHorCursor
                    if self._hover_target == "bar"
                    else Qt.CursorShape.PointingHandCursor
                )
                self.update()
            return

        if self._active_target == "low":
            new_val = self._x_to_val(x)
            new_low = max(self._min_val, min(new_val, self._high_val - self._min_gap))
            if abs(new_low - self._low_val) > 0.01:
                self._low_val = new_low
                self.rangeChanged.emit(self._low_val, self._high_val)
                self.lowChanged.emit(self._low_val)
                self.update()

        elif self._active_target == "high":
            new_val = self._x_to_val(x)
            new_high = min(self._max_val, max(new_val, self._low_val + self._min_gap))
            if abs(new_high - self._high_val) > 0.01:
                self._high_val = new_high
                self.rangeChanged.emit(self._low_val, self._high_val)
                self.highChanged.emit(self._high_val)
                self.update()

        elif self._active_target == "bar":
            delta_val = self._x_to_val(x) - self._x_to_val(self._drag_start_x)
            dur = self._drag_start_high - self._drag_start_low
            new_low = self._drag_start_low + delta_val
            new_high = self._drag_start_high + delta_val

            if new_low < self._min_val:
                new_low = self._min_val
                new_high = new_low + dur
            elif new_high > self._max_val:
                new_high = self._max_val
                new_low = new_high - dur

            if abs(new_low - self._low_val) > 0.01 or abs(new_high - self._high_val) > 0.01:
                self._low_val = new_low
                self._high_val = new_high
                self.rangeChanged.emit(self._low_val, self._high_val)
                self.lowChanged.emit(self._low_val)
                self.highChanged.emit(self._high_val)
                self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._active_target = None
        self.update()

    def leaveEvent(self, event):
        self._hover_target = None
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pad = self._handle_r + 4.0
        w = float(self.width())
        h = float(self.height())
        cy = h / 2.0
        track_h = 4.0
        track_y = cy - track_h / 2.0
        track_w = max(1.0, w - 2.0 * pad)

        # 1. Flat muted groove track
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(Tokens.BORDER)))
        painter.drawRoundedRect(QRectF(pad, track_y, track_w, track_h), 2.0, 2.0)

        # 2. Restrained solid accent span
        x_low = self._val_to_x(self._low_val)
        x_high = self._val_to_x(self._high_val)
        span_w = max(0.0, x_high - x_low)

        span_color = QColor(Tokens.ACCENT_HOVER if self._hover_target == "bar" or self._active_target == "bar" else Tokens.ACCENT)
        painter.setBrush(QBrush(span_color))
        painter.drawRoundedRect(QRectF(x_low, track_y, span_w, track_h), 2.0, 2.0)

        # 3. Minimal crisp handles
        for target, x_pos in (("low", x_low), ("high", x_high)):
            is_hover = self._hover_target == target
            is_active = self._active_target == target
            r = self._handle_r

            if is_active or is_hover:
                ring_color = QColor(Tokens.ACCENT)
                ring_color.setAlpha(70 if is_active else 45)
                painter.setBrush(QBrush(ring_color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(x_pos, cy), r + 3.5, r + 3.5)

            painter.setBrush(QBrush(QColor("#FFFFFF")))
            border_color = Tokens.ACCENT if (is_active or is_hover) else Tokens.BORDER_HOVER
            painter.setPen(QPen(QColor(border_color), 1.75))
            painter.drawEllipse(QPointF(x_pos, cy), r, r)

        painter.end()
