from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

PRIMARY = "#ff8a00"


class LockDialog(QDialog):
    def __init__(self, minutes: int = 30, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Блокировка")
        self.setModal(True)
        self.setMinimumWidth(360)
        self.setStyleSheet("QDialog { background: #171a21; color: #f2f4f8; } QLabel { color: #f2f4f8; }")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(12)
        lay.addWidget(QLabel("Заблокировать интерфейс?", styleSheet="font-size: 18px; font-weight: 800;"))
        lay.addWidget(QLabel(
            f"Приложение продолжит работать в фоне, интерфейс будет недоступен {minutes} минут",
            wordWrap=True, styleSheet="color: #cfd6df;",
        ))
        btns = QHBoxLayout()
        ok = QPushButton("ОК", styleSheet=f"background: {PRIMARY}; color: white; border-radius: 10px; padding: 10px;")
        cancel = QPushButton("Отмена", styleSheet="background: rgba(255,255,255,0.06); color: #f2f4f8; border-radius: 10px; padding: 10px;")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        lay.addLayout(btns)


class OverlayBlocker(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background: rgba(10,12,16,0.88);")
        self.lbl = QLabel("Доступ временно ограничен")
        self.lbl.setStyleSheet("color: white; font-size: 24px; font-weight: 800;")
        self.sub = QLabel("")
        self.sub.setStyleSheet("color: #cfd6df; font-size: 14px;")
        self.sub.setWordWrap(True)
        lay = QVBoxLayout(self)
        lay.addStretch(1)
        lay.addWidget(self.lbl, alignment=Qt.AlignCenter)
        lay.addWidget(self.sub, alignment=Qt.AlignCenter)
        lay.addStretch(1)
        self.hide()

    def set_remaining(self, text: str):
        self.sub.setText(text)