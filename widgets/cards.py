from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from constants import ALL_DAYS, CARD_BTN, DELETE_BTN, DONE_BTN, SEVERITY_LABELS
from models import ActionItem


class HoverInfoLabel(QLabel):

    def __init__(self, text: str, desc: str = "", parent=None):
        super().__init__(text, parent)
        self.setToolTip(desc)
        self.setStyleSheet("""
            QLabel {
                color: #e8edf3; font-size: 14px;
                padding: 10px 12px;
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 14px;
            }
            QLabel:hover {
                border: 1px solid rgba(255,138,0,0.7);
                background: rgba(255,138,0,0.08);
            }
        """)


class ActionCard(QFrame):

    edit_clicked   = Signal(object)
    toggle_clicked = Signal(object)
    delete_clicked = Signal(object)
    done_clicked   = Signal(object)

    def __init__(self, action: ActionItem, parent=None):
        super().__init__(parent)
        self.action = action
        self.setObjectName("actionCard")
        self.setStyleSheet("""
            QFrame#actionCard {
                background: #171a21;
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 18px;
            }
            QFrame#actionCard:hover { border: 1px solid rgba(255,138,0,0.35); }
            QLabel { color: #f2f4f8; }
        """)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        # Заголовок
        top = QHBoxLayout()
        lbl_title = QLabel(self.action.title)
        lbl_title.setStyleSheet("font-size: 17px; font-weight: 700;")
        self.dot = QLabel("●")
        self.dot.setStyleSheet(f"color: {self.action.intensity_color()}; font-size: 18px;")
        self.done_lbl = QLabel(self._done_text())
        self.done_lbl.setStyleSheet("color: #9aa4b2; font-size: 12px;")
        top.addWidget(lbl_title)
        top.addStretch(1)
        top.addWidget(self.done_lbl)
        top.addWidget(self.dot)
        root.addLayout(top)

        # Срок / дни / мета
        lbl_expiry = QLabel(f"Срок: {self.action.expiry_text()}")
        lbl_expiry.setStyleSheet("color: #9aa4b2; font-size: 13px;")
        root.addWidget(lbl_expiry)

        lbl_days = QLabel(self._days_text())
        lbl_days.setStyleSheet("color: #9aa4b2; font-size: 13px;")
        root.addWidget(lbl_days)

        meta = QLabel(self._meta_text())
        meta.setWordWrap(True)
        meta.setStyleSheet("color: #cfd6df; font-size: 13px;")
        root.addWidget(meta)

        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: rgba(255,255,255,0.08);")
        root.addWidget(line)

        # Кнопки
        btns = QHBoxLayout()
        self.done_btn   = QPushButton("Выполнено")
        self.edit_btn   = QPushButton("Настроить")
        self.toggle_btn = QPushButton(self._toggle_label())
        self.delete_btn = QPushButton("Удалить")

        self.done_btn.setStyleSheet(DONE_BTN)
        self.edit_btn.setStyleSheet(CARD_BTN)
        self.toggle_btn.setStyleSheet(CARD_BTN)
        self.delete_btn.setStyleSheet(DELETE_BTN)

        for b in (self.done_btn, self.edit_btn, self.toggle_btn, self.delete_btn):
            b.setCursor(Qt.PointingHandCursor)
            b.setMinimumHeight(34)

        self.done_btn.clicked.connect(lambda: self.done_clicked.emit(self.action))
        self.edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.action))
        self.toggle_btn.clicked.connect(lambda: self.toggle_clicked.emit(self.action))
        self.delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.action))

        for b in (self.done_btn, self.edit_btn, self.toggle_btn, self.delete_btn):
            btns.addWidget(b)
        root.addLayout(btns)

    # ── Публичный API ──────────────────────────────────────────────────────────

    def update_visuals(self) -> None:
        self.dot.setStyleSheet(
            f"color: {self.action.intensity_color()}; font-size: 18px;"
        )
        self.toggle_btn.setText(self._toggle_label())
        self.done_lbl.setText(self._done_text())

    # ── Вспомогательные методы ────────────────────────────────────────────────

    def _toggle_label(self) -> str:
        return "Отключить" if self.action.enabled else "Включить"

    def _done_text(self) -> str:
        a = self.action
        return f" {a.done_today} сегодня  /  {a.done_total} всего"

    def _days_text(self) -> str:
        a = self.action
        if a.date_mode == "every_day":
            return "Дни: каждый день"
        if a.date_mode == "specific":
            d = a.specific_date
            return f"Дата: {d.strftime('%d.%m.%Y') if d else '—'}"
        if not a.active_days:
            return "Дни: не выбраны"
        if len(a.active_days) == 7:
            return "Дни: каждый день"
        names = [ALL_DAYS[i] for i in sorted(a.active_days)]
        return "Дни: " + ", ".join(names)

    def _meta_text(self) -> str:
        a = self.action
        reminder = (
            f"каждые {a.reminder_from_min} мин"
            if a.reminder_type == "fixed"
            else f"от {a.reminder_from_min} до {a.reminder_to_min} мин"
        )
        repetitions = (
            f"{a.repetitions_from} раз"
            if a.repetitions_type == "fixed"
            else f"от {a.repetitions_from} до {a.repetitions_to} раз"
        )
        return (
            f"Серьёзность: {SEVERITY_LABELS[a.severity]}\n"
            f"Частота: {reminder}\n"
            f"Активность: {a.activity_start.strftime('%H:%M')}–{a.activity_end.strftime('%H:%M')}\n"
            f"Повторов сегодня: {a.today_count()} ({repetitions})"
        )