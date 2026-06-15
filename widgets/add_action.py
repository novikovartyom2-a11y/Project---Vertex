from __future__ import annotations

from datetime import datetime, date, time
from typing import Optional, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QCheckBox, QPushButton, QScrollArea, QTimeEdit, QVBoxLayout,
    QWidget,
)

from widgets.intbox import IntBox
from data import ActionItem

PRIMARY = "#ff8a00"
ALL_DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

_INPUT_STYLE = """
    QLineEdit, QComboBox, QTimeEdit, QDateEdit {
        background: #111318; color: #f2f4f8;
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 10px; padding: 8px 10px; min-height: 18px;
    }
    QComboBox::drop-down { border: none; width: 20px; }
    QComboBox QAbstractItemView {
        background: #171a21; color: #f2f4f8;
        selection-background-color: #ff8a00;
    }
"""


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


class AddActionPage(QWidget):
    save_clicked   = Signal(object)
    cancel_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._edit_uid: Optional[str] = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        self.page_title = QLabel("Добавить новое действие")
        self.page_title.setStyleSheet("font-size: 24px; font-weight: 800; color: #f2f4f8;")
        root.addWidget(self.page_title)

        sub = QLabel("Наводи курсор на пункты — появляется подсказка")
        sub.setStyleSheet("color: #9aa4b2; font-size: 13px;")
        root.addWidget(sub)

        content = QHBoxLayout()
        content.setSpacing(18)
        root.addLayout(content, 1)

        # форма
        left = QFrame()
        left.setStyleSheet("background: #171a21; border-radius: 18px;")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(18, 18, 18, 18)
        ll.setSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        form_widget = QWidget()
        form = QFormLayout(form_widget)
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setSpacing(10)
        form.setVerticalSpacing(12)
        scroll.setWidget(form_widget)
        ll.addWidget(scroll, 1)

        def s(w):
            w.setStyleSheet(_INPUT_STYLE)
            return w

        def hl(t, d=""):
            return HoverInfoLabel(t, d)

        self.title_edit = s(QLineEdit())
        self.title_edit.setPlaceholderText("Например: Размяться")
        form.addRow(hl("Название", "Что нужно сделать?"), self.title_edit)

        self.severity = s(QComboBox())
        self.severity.addItems([
            "1 — Обычное уведомление",
            "2 — Полноэкранное с отменой",
            "3 — Полноэкранное без отмены",
        ])
        form.addRow(hl("Строгость", "1 — тихое. 2 — полный экран с кнопкой отмены. 3 — без отмены"), self.severity)

        self.time_limit = IntBox(1, 9999, 15)
        form.addRow(hl("Время на выполнение (мин)", "Таймер для режимов 2 и 3"), self.time_limit)

        self.reminder_mode = s(QComboBox())
        self.reminder_mode.addItems(["Фиксированный интервал", "Диапазон интервала"])
        self.reminder_from = IntBox(1, 9999, 40)
        self.reminder_to   = IntBox(1, 9999, 60)
        form.addRow(hl("Частота", "Интервал между уведомлениями"), self.reminder_mode)
        form.addRow(QLabel(""), self._pair(self.reminder_from, self.reminder_to))

        self.activity_start = s(QTimeEdit())
        self.activity_start.setDisplayFormat("HH:mm")
        self.activity_start.setTime(time(9, 0))
        self.activity_end = s(QTimeEdit())
        self.activity_end.setDisplayFormat("HH:mm")
        self.activity_end.setTime(time(18, 0))
        form.addRow(hl("Период активности", "Окно, в котором приходят уведомления"),
                    self._pair(self.activity_start, self.activity_end))

        self.repetitions_mode = s(QComboBox())
        self.repetitions_mode.addItems(["Фиксированное количество", "Диапазон количества"])
        self.repetitions_from = IntBox(1, 9999, 3)
        self.repetitions_to   = IntBox(1, 9999, 5)
        form.addRow(hl("Количество напоминаний", "Сколько раз в день"),
                    self._pair(self.repetitions_from, self.repetitions_to))

        self.expiry_mode = s(QComboBox())
        self.expiry_mode.addItems(["Всегда", "До даты"])
        self.expiry_date_edit = s(QDateEdit())
        self.expiry_date_edit.setCalendarPopup(True)
        self.expiry_date_edit.setDate(datetime.now().date())
        self.expiry_date_edit.setDisplayFormat("dd.MM.yyyy")
        form.addRow(hl("Срок действия", "До какой даты актуально"),
                    self._pair(self.expiry_mode, self.expiry_date_edit))

        self.date_mode_combo = s(QComboBox())
        self.date_mode_combo.addItems(["По дням недели", "Конкретная дата", "Каждый день"])
        form.addRow(hl("Режим дат", "Как задать расписание"), self.date_mode_combo)

        self.specific_date_edit = s(QDateEdit())
        self.specific_date_edit.setCalendarPopup(True)
        self.specific_date_edit.setDate(datetime.now().date())
        self.specific_date_edit.setDisplayFormat("dd.MM.yyyy")
        form.addRow(hl("Конкретная дата", "На какой день запланировать"), self.specific_date_edit)

        days_widget = QWidget()
        days_lay = QHBoxLayout(days_widget)
        days_lay.setContentsMargins(0, 0, 0, 0)
        days_lay.setSpacing(6)
        self.day_checks: List[QCheckBox] = []
        for name in ALL_DAYS:
            cb = QCheckBox(name)
            cb.setChecked(True)
            cb.setStyleSheet("""
                QCheckBox { color: #f2f4f8; font-size: 13px; }
                QCheckBox::indicator { width: 16px; height: 16px;
                    background: #111318; border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; }
                QCheckBox::indicator:checked { background: #ff8a00; border-color: #ff8a00; }
            """)
            cb.stateChanged.connect(self.update_preview)
            self.day_checks.append(cb)
            days_lay.addWidget(cb)
        days_lay.addStretch(1)
        self.days_row_label = hl("Дни недели", "Выберите дни, когда активно действие")
        form.addRow(self.days_row_label, days_widget)

        content.addWidget(left, 2)

        # предпросмотр
        right = QFrame()
        right.setStyleSheet("background: #171a21; border-radius: 18px;")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(18, 18, 18, 18)
        rl.setSpacing(12)

        pt = QLabel("Предпросмотр")
        pt.setStyleSheet("font-size: 18px; font-weight: 700;")
        rl.addWidget(pt)

        self.preview = QLabel()
        self.preview.setWordWrap(True)
        self.preview.setStyleSheet("""
            QLabel { color: #dfe6ee;
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 14px; padding: 14px; }
        """)
        rl.addWidget(self.preview)

        _btn_base = """
            QPushButton {
                background: rgba(255,255,255,0.06); color: #f2f4f8;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px; padding: 10px 16px;
            }
            QPushButton:hover { background: rgba(255,138,0,0.16); border-color: rgba(255,138,0,0.45); }
        """
        btns = QHBoxLayout()
        self.save_btn   = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")
        for b in (self.save_btn, self.cancel_btn):
            b.setCursor(Qt.PointingHandCursor)
            b.setMinimumHeight(42)
            b.setStyleSheet(_btn_base)
        self.save_btn.setStyleSheet(_btn_base + f"QPushButton {{ background: {PRIMARY}; color: white; }}")
        btns.addWidget(self.save_btn)
        btns.addWidget(self.cancel_btn)
        rl.addStretch(1)
        rl.addLayout(btns)
        content.addWidget(right, 1)

        for w in (self.title_edit, self.severity, self.time_limit,
                  self.reminder_mode, self.reminder_from, self.reminder_to,
                  self.activity_start, self.activity_end,
                  self.repetitions_mode, self.repetitions_from, self.repetitions_to,
                  self.expiry_mode, self.expiry_date_edit,
                  self.date_mode_combo, self.specific_date_edit):
            for sig in ("valueChanged", "currentIndexChanged", "timeChanged", "dateChanged", "textChanged"):
                if hasattr(w, sig):
                    getattr(w, sig).connect(self.update_preview)

        self.severity.currentIndexChanged.connect(self._sync_severity)
        self.reminder_mode.currentIndexChanged.connect(self._sync_reminder_mode)
        self.repetitions_mode.currentIndexChanged.connect(self._sync_rep_mode)
        self.expiry_mode.currentIndexChanged.connect(self._sync_expiry)
        self.date_mode_combo.currentIndexChanged.connect(self._sync_date_mode)
        self.save_btn.clicked.connect(self._emit_save)
        self.cancel_btn.clicked.connect(self.cancel_clicked.emit)

        self._sync_severity()
        self._sync_reminder_mode()
        self._sync_rep_mode()
        self._sync_expiry()
        self._sync_date_mode()
        self.update_preview()

    def _sync_severity(self):
        self.time_limit.setEnabled(self.severity.currentIndex() >= 1)
        self.update_preview()

    def _sync_reminder_mode(self):
        self.reminder_to.setVisible(self.reminder_mode.currentIndex() == 1)
        self.update_preview()

    def _sync_rep_mode(self):
        self.repetitions_to.setVisible(self.repetitions_mode.currentIndex() == 1)
        self.update_preview()

    def _sync_expiry(self):
        self.expiry_date_edit.setEnabled(self.expiry_mode.currentIndex() == 1)
        self.update_preview()

    def _sync_date_mode(self):
        idx = self.date_mode_combo.currentIndex()
        self.specific_date_edit.setVisible(idx == 1)
        self.days_row_label.setVisible(idx == 0)
        for cb in self.day_checks:
            cb.setVisible(idx == 0)
        self.update_preview()

    def update_preview(self):
        title  = self.title_edit.text().strip() or "Без названия"
        sev    = self.severity.currentIndex() + 1
        sev_map = ["Обычное уведомление", "Полноэкранное с отменой", "Полноэкранное без отмены"]
        reminder = (
            f"каждые {self.reminder_from.value()} мин"
            if self.reminder_mode.currentIndex() == 0
            else f"от {self.reminder_from.value()} до {self.reminder_to.value()} мин"
        )
        reps = (
            f"{self.repetitions_from.value()} раз"
            if self.repetitions_mode.currentIndex() == 0
            else f"от {self.repetitions_from.value()} до {self.repetitions_to.value()} раз"
        )
        expiry = (
            "Всегда" if self.expiry_mode.currentIndex() == 0
            else self.expiry_date_edit.date().toPython().strftime("%d.%m.%Y")
        )
        tl  = f"{self.time_limit.value()} мин" if sev >= 2 else "не требуется"
        self.preview.setText(
            f"Название: {title}\n"
            f"Строгость: {sev_map[sev-1]}\n"
            f"Время на выполнение: {tl}\n"
            f"Частота: {reminder}\n"
            f"Активность: {self.activity_start.time().toPython().strftime('%H:%M')}–"
            f"{self.activity_end.time().toPython().strftime('%H:%M')}\n"
            f"Количество: {reps}\n"
            f"Срок: {expiry}\n"
            f"Дни: {self._days_preview()}"
        )

    def _days_preview(self) -> str:
        idx = self.date_mode_combo.currentIndex()
        if idx == 2: return "каждый день"
        if idx == 1: return self.specific_date_edit.date().toPython().strftime("%d.%m.%Y")
        checked = [ALL_DAYS[i] for i, cb in enumerate(self.day_checks) if cb.isChecked()]
        return ", ".join(checked) if checked else "не выбраны"

    def load_for_edit(self, action: ActionItem):
        self._edit_uid = action.uid
        self.page_title.setText("Редактировать действие")
        self.title_edit.setText(action.title)
        self.severity.setCurrentIndex(action.severity - 1)
        self.time_limit.setValue(action.time_limit_minutes or 15)
        self.reminder_mode.setCurrentIndex(0 if action.reminder_type == "fixed" else 1)
        self.reminder_from.setValue(action.reminder_from_min)
        self.reminder_to.setValue(action.reminder_to_min)
        self.activity_start.setTime(action.activity_start)
        self.activity_end.setTime(action.activity_end)
        self.repetitions_mode.setCurrentIndex(0 if action.repetitions_type == "fixed" else 1)
        self.repetitions_from.setValue(action.repetitions_from)
        self.repetitions_to.setValue(action.repetitions_to)
        self.expiry_mode.setCurrentIndex(0 if action.expiry_mode == "always" else 1)
        if action.expiry_date:
            self.expiry_date_edit.setDate(action.expiry_date)
        if action.date_mode == "specific":
            self.date_mode_combo.setCurrentIndex(1)
            if action.specific_date:
                self.specific_date_edit.setDate(action.specific_date)
        elif action.date_mode == "every_day":
            self.date_mode_combo.setCurrentIndex(2)
        else:
            self.date_mode_combo.setCurrentIndex(0)
            for i, cb in enumerate(self.day_checks):
                cb.setChecked(i in action.active_days)
        self._sync_severity(); self._sync_reminder_mode(); self._sync_rep_mode()
        self._sync_expiry(); self._sync_date_mode(); self.update_preview()

    def reset_for_new(self):
        self._edit_uid = None
        self.page_title.setText("Добавить новое действие")
        self.title_edit.clear()
        self.severity.setCurrentIndex(0)
        self.time_limit.setValue(15)
        self.reminder_mode.setCurrentIndex(0)
        self.reminder_from.setValue(40)
        self.reminder_to.setValue(60)
        self.activity_start.setTime(time(9, 0))
        self.activity_end.setTime(time(18, 0))
        self.repetitions_mode.setCurrentIndex(0)
        self.repetitions_from.setValue(3)
        self.repetitions_to.setValue(5)
        self.expiry_mode.setCurrentIndex(0)
        self.expiry_date_edit.setDate(datetime.now().date())
        self.date_mode_combo.setCurrentIndex(0)
        self.specific_date_edit.setDate(datetime.now().date())
        for cb in self.day_checks:
            cb.setChecked(True)
        self._sync_severity(); self._sync_reminder_mode(); self._sync_rep_mode()
        self._sync_expiry(); self._sync_date_mode(); self.update_preview()

    def get_action(self) -> ActionItem:
        import uuid
        dm_idx = self.date_mode_combo.currentIndex()
        if dm_idx == 0:
            date_mode = "weekdays"
            active_days = [i for i, cb in enumerate(self.day_checks) if cb.isChecked()]
            specific_date = None
        elif dm_idx == 1:
            date_mode = "specific"
            active_days = list(range(7))
            specific_date = self.specific_date_edit.date().toPython()
        else:
            date_mode = "every_day"
            active_days = list(range(7))
            specific_date = None

        return ActionItem(
            uid               = self._edit_uid or str(uuid.uuid4()),
            title             = self.title_edit.text().strip() or "Без названия",
            severity          = self.severity.currentIndex() + 1,
            time_limit_minutes= self.time_limit.value() if self.severity.currentIndex() >= 1 else None,
            reminder_type     = "fixed" if self.reminder_mode.currentIndex() == 0 else "range",
            reminder_from_min = self.reminder_from.value(),
            reminder_to_min   = self.reminder_to.value(),
            activity_start    = self.activity_start.time().toPython(),
            activity_end      = self.activity_end.time().toPython(),
            repetitions_type  = "fixed" if self.repetitions_mode.currentIndex() == 0 else "range",
            repetitions_from  = self.repetitions_from.value(),
            repetitions_to    = self.repetitions_to.value(),
            expiry_mode       = "always" if self.expiry_mode.currentIndex() == 0 else "until",
            expiry_date       = None if self.expiry_mode.currentIndex() == 0 else self.expiry_date_edit.date().toPython(),
            active_days       = active_days,
            specific_date     = specific_date,
            date_mode         = date_mode,
        )

    def _emit_save(self):
        self.save_clicked.emit(self.get_action())

    @staticmethod
    def _pair(a: QWidget, b: QWidget) -> QWidget:
        box = QWidget()
        lay = QHBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.addWidget(a)
        lay.addWidget(b)
        return box