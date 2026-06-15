from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget

from constants import INPUT_STYLE

_BTN_STYLE = """
    QPushButton {
        background: #1e2130; color: #f2f4f8;
        border: 1px solid rgba(255,255,255,0.10);
        padding: 0; min-width: 28px; min-height: 34px; font-size: 16px;
    }
    QPushButton:hover { background: rgba(255,138,0,0.25); color: #ff8a00; }
    QPushButton:pressed { background: rgba(255,138,0,0.4); }
"""


class IntBox(QWidget):

    valueChanged = Signal(int)

    def __init__(
        self,
        min_val: int = 1,
        max_val: int = 9999,
        value:   int = 1,
        parent=None,
    ):
        super().__init__(parent)
        self._min = min_val
        self._max = max_val
        self._val = value

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._edit = QLineEdit(str(value))
        self._edit.setValidator(QIntValidator(min_val, max_val))
        self._edit.setAlignment(Qt.AlignCenter)
        self._edit.setStyleSheet(
            INPUT_STYLE + "QLineEdit { border-radius: 0; border-right: none; }"
        )
        self._edit.setMinimumWidth(60)
        self._edit.editingFinished.connect(self._on_edit)

        self._minus = QPushButton("−")
        self._minus.setStyleSheet(
            _BTN_STYLE + "QPushButton { border-radius: 10px 0 0 10px; }"
        )
        self._plus = QPushButton("+")
        self._plus.setStyleSheet(
            _BTN_STYLE + "QPushButton { border-radius: 0 10px 10px 0; border-left: none; }"
        )

        self._minus.clicked.connect(lambda: self.setValue(self._val - 1))
        self._plus.clicked.connect(lambda: self.setValue(self._val + 1))

        lay.addWidget(self._minus)
        lay.addWidget(self._edit, 1)
        lay.addWidget(self._plus)

        self._update_display()

    def value(self) -> int:
        return self._val

    def setValue(self, v: int) -> None:
        v = max(self._min, min(self._max, v))
        if v != self._val:
            self._val = v
            self._update_display()
            self.valueChanged.emit(self._val)

    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        self._edit.setEnabled(enabled)
        self._minus.setEnabled(enabled and self._val > self._min)
        self._plus.setEnabled(enabled and self._val < self._max)

    def _on_edit(self) -> None:
        try:
            v = int(self._edit.text())
        except ValueError:
            v = self._val
        self.setValue(v)

    def _update_display(self) -> None:
        self._edit.setText(str(self._val))
        self._minus.setEnabled(self._val > self._min)
        self._plus.setEnabled(self._val < self._max)