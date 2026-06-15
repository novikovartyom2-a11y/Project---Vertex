from __future__ import annotations

import math

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget

PRIMARY = "#ff8a00"
BG      = "#111318"
GRAY    = "#4b5563"


class PulseWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active = False
        self.t = 0.0
        self.setMinimumHeight(220)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(30)

    def set_active(self, active: bool):
        self.active = active
        self.update()

    def _tick(self):
        self.t += 0.03
        if self.active or int(self.t * 10) % 3 == 0:
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        painter.fillRect(rect, QColor(BG))
        cx, cy = rect.center().x(), rect.center().y()
        base_color = QColor(PRIMARY if self.active else GRAY)
        rings  = 7 if self.active else 4
        max_r  = min(rect.width(), rect.height()) // 2 - 16
        for i in range(rings):
            phase  = self.t * (2.1 if self.active else 0.8) + i * 0.7
            radius = 40 + i * (max_r / rings) * (0.75 if self.active else 0.6)
            pulse  = 0.5 + 0.5 * math.sin(phase)
            alpha  = int((70 if self.active else 35) + pulse * (90 if self.active else 25))
            c = QColor(base_color)
            c.setAlpha(alpha)
            painter.setPen(Qt.NoPen)
            painter.setBrush(c)
            painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
        orb = QColor(PRIMARY if self.active else "#6b7280")
        orb.setAlpha(220 if self.active else 160)
        painter.setBrush(orb)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - 48, cy - 48, 96, 96)
        glow = QColor("#ffffff")
        glow.setAlpha(40 if self.active else 18)
        painter.setBrush(glow)
        painter.drawEllipse(cx - 22, cy - 22, 44, 44)