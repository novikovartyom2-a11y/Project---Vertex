from __future__ import annotations

import json
import math
import random
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from pathlib import Path
from typing import Optional, List

from PySide6.QtCore import Qt, QTimer, QSize, Signal, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter, QIntValidator
from PySide6.QtWidgets import (
    QApplication, QCalendarWidget, QComboBox, QDateEdit, QDialog, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QSizePolicy, QStackedWidget,
    QTimeEdit, QToolButton, QVBoxLayout, QWidget, QFormLayout, QCheckBox,
    QInputDialog,
)

PRIMARY      = "#ff8a00"
PRIMARY_DARK = "#d86f00"
BG           = "#111318"
TEXT         = "#f2f4f8"
MUTED        = "#9aa4b2"
GRAY         = "#4b5563"
GREEN        = "#2ecc71"
YELLOW       = "#f1c40f"
RED          = "#e74c3c"

SAVE_PATH = Path.home() / ".taskpulse_actions.json"
WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
ALL_DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

# виджет числа с кнопками +/- и ручным вводом
class IntBox(QWidget):
    valueChanged = Signal(int)

    def __init__(self, min_val=1, max_val=9999, value=1, suffix="", parent=None):
        super().__init__(parent)
        self._min = min_val
        self._max = max_val
        self._val = value
        self._suffix = suffix

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._edit = QLineEdit(str(value))
        self._edit.setValidator(QIntValidator(min_val, max_val))
        self._edit.setAlignment(Qt.AlignCenter)
        self._edit.setStyleSheet(_INPUT_STYLE + "QLineEdit { border-radius: 0; border-right: none; }")
        self._edit.setMinimumWidth(60)
        self._edit.editingFinished.connect(self._on_edit)

        btn_style = """
            QPushButton {
                background: #1e2130; color: #f2f4f8;
                border: 1px solid rgba(255,255,255,0.10);
                padding: 0; min-width: 28px; min-height: 34px; font-size: 16px;
            }
            QPushButton:hover { background: rgba(255,138,0,0.25); color: #ff8a00; }
            QPushButton:pressed { background: rgba(255,138,0,0.4); }
        """
        self._minus = QPushButton("−")
        self._minus.setStyleSheet(btn_style + "QPushButton { border-radius: 10px 0 0 10px; }")
        self._plus  = QPushButton("+")
        self._plus.setStyleSheet(btn_style + "QPushButton { border-radius: 0 10px 10px 0; border-left: none; }")

        self._minus.clicked.connect(lambda: self.setValue(self._val - 1))
        self._plus.clicked.connect(lambda: self.setValue(self._val + 1))

        lay.addWidget(self._minus)
        lay.addWidget(self._edit, 1)
        lay.addWidget(self._plus)

        self._update_display()

    def _on_edit(self):
        try:
            v = int(self._edit.text())
        except ValueError:
            v = self._val
        self.setValue(v)

    def _update_display(self):
        self._edit.setText(str(self._val))
        self._minus.setEnabled(self._val > self._min)
        self._plus.setEnabled(self._val < self._max)

    def setValue(self, v: int):
        v = max(self._min, min(self._max, v))
        if v != self._val:
            self._val = v
            self._update_display()
            self.valueChanged.emit(self._val)

    def value(self) -> int:
        return self._val

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self._edit.setEnabled(enabled)
        self._minus.setEnabled(enabled and self._val > self._min)
        self._plus.setEnabled(enabled and self._val < self._max)

    def setVisible(self, visible: bool):
        super().setVisible(visible)

#данные

def _time_to_str(t: time) -> str:
    return t.strftime("%H:%M")

def _str_to_time(s: str) -> time:
    h, m = map(int, s.split(":"))
    return time(h, m)

def _date_to_str(d: Optional[date]) -> Optional[str]:
    return d.isoformat() if d else None

def _str_to_date(s: Optional[str]) -> Optional[date]:
    return date.fromisoformat(s) if s else None

def save_actions(actions: List[ActionItem]) -> None:
    data = []
    for a in actions:
        data.append({
            "uid":                a.uid,
            "title":              a.title,
            "severity":           a.severity,
            "time_limit_minutes": a.time_limit_minutes,
            "reminder_type":      a.reminder_type,
            "reminder_from_min":  a.reminder_from_min,
            "reminder_to_min":    a.reminder_to_min,
            "activity_start":     _time_to_str(a.activity_start),
            "activity_end":       _time_to_str(a.activity_end),
            "repetitions_type":   a.repetitions_type,
            "repetitions_from":   a.repetitions_from,
            "repetitions_to":     a.repetitions_to,
            "expiry_mode":        a.expiry_mode,
            "expiry_date":        _date_to_str(a.expiry_date),
            "active_days":        a.active_days,
            "specific_date":      _date_to_str(a.specific_date),
            "date_mode":          a.date_mode,
            "enabled":            a.enabled,
            "created_at":         a.created_at.isoformat(),
        })
    SAVE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def load_actions() -> List[ActionItem]:
    if not SAVE_PATH.exists():
        return []
    try:
        data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
        result = []
        for d in data:
            result.append(ActionItem(
                uid               = d.get("uid", str(uuid.uuid4())),
                title             = d["title"],
                severity          = d["severity"],
                time_limit_minutes= d.get("time_limit_minutes"),
                reminder_type     = d["reminder_type"],
                reminder_from_min = d["reminder_from_min"],
                reminder_to_min   = d["reminder_to_min"],
                activity_start    = _str_to_time(d["activity_start"]),
                activity_end      = _str_to_time(d["activity_end"]),
                repetitions_type  = d["repetitions_type"],
                repetitions_from  = d["repetitions_from"],
                repetitions_to    = d["repetitions_to"],
                expiry_mode       = d["expiry_mode"],
                expiry_date       = _str_to_date(d.get("expiry_date")),
                active_days       = d.get("active_days", list(range(7))),
                specific_date     = _str_to_date(d.get("specific_date")),
                date_mode         = d.get("date_mode", "weekdays"),
                enabled           = d.get("enabled", True),
                created_at        = datetime.fromisoformat(d["created_at"]),
            ))
        return result
    except Exception:
        return []

@dataclass
class ActionItem:
    uid:               str
    title:             str
    severity:          int
    time_limit_minutes: Optional[int]
    reminder_type:     str
    reminder_from_min: int
    reminder_to_min:   int
    activity_start:    time
    activity_end:      time
    repetitions_type:  str
    repetitions_from:  int
    repetitions_to:    int
    expiry_mode:       str
    expiry_date:       Optional[date]
    active_days:       List[int]
    specific_date:     Optional[date]
    date_mode:         str
    enabled:           bool = True
    created_at:        datetime = field(default_factory=datetime.now)
    # статистика выполнения
    done_today:        int = 0
    done_total:        int = 0

    def today_count(self) -> int:
        if self.repetitions_type == "fixed":
            return self.repetitions_from
        return random.randint(self.repetitions_from, self.repetitions_to)

    def expiry_text(self) -> str:
        if self.expiry_mode == "always":
            return "Всегда"
        return self.expiry_date.strftime("%d.%m.%Y") if self.expiry_date else "Не задано"

    def intensity_color(self) -> str:
        count = self.today_count()
        if count <= 3:  return GREEN
        if count <= 6:  return YELLOW
        return RED

    def is_active_on(self, d: date) -> bool:
        if not self.enabled:
            return False
        if self.expiry_mode == "until" and self.expiry_date and d > self.expiry_date:
            return False
        if self.date_mode == "every_day":
            return True
        if self.date_mode == "specific":
            return self.specific_date == d if self.specific_date else False
        return (d.isoweekday() - 1) in self.active_days


# стили

_CARD_BTN = """
    QPushButton {
        background: rgba(255,255,255,0.06); color: #f2f4f8;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px; padding: 7px 12px;
    }
    QPushButton:hover {
        background: rgba(255,138,0,0.16);
        border: 1px solid rgba(255,138,0,0.45);
    }
"""
_DELETE_BTN = """
    QPushButton {
        background: rgba(231,76,60,0.12); color: #e74c3c;
        border: 1px solid rgba(231,76,60,0.25);
        border-radius: 10px; padding: 7px 12px;
    }
    QPushButton:hover {
        background: rgba(231,76,60,0.28);
        border: 1px solid rgba(231,76,60,0.6);
    }
"""
_DONE_BTN = """
    QPushButton {
        background: rgba(46,204,113,0.12); color: #2ecc71;
        border: 1px solid rgba(46,204,113,0.25);
        border-radius: 10px; padding: 7px 12px;
    }
    QPushButton:hover {
        background: rgba(46,204,113,0.28);
        border: 1px solid rgba(46,204,113,0.6);
    }
"""
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


# таблица

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


# активная карточка

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

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        top = QHBoxLayout()
        lbl_title = QLabel(action.title)
        lbl_title.setStyleSheet("font-size: 17px; font-weight: 700;")
        self.dot = QLabel("●")
        self.dot.setStyleSheet(f"color: {action.intensity_color()}; font-size: 18px;")
        # счётчик выполнений
        self.done_lbl = QLabel(f {action.done_today} сегодня  /  {action.done_total} всего")
        self.done_lbl.setStyleSheet("color: #9aa4b2; font-size: 12px;")
        top.addWidget(lbl_title)
        top.addStretch(1)
        top.addWidget(self.done_lbl)
        top.addWidget(self.dot)
        root.addLayout(top)

        lbl_expiry = QLabel(f"Срок: {action.expiry_text()}")
        lbl_expiry.setStyleSheet("color: #9aa4b2; font-size: 13px;")
        root.addWidget(lbl_expiry)

        lbl_days = QLabel(self._days_text())
        lbl_days.setStyleSheet("color: #9aa4b2; font-size: 13px;")
        root.addWidget(lbl_days)

        meta = QLabel(self._meta_text())
        meta.setWordWrap(True)
        meta.setStyleSheet("color: #cfd6df; font-size: 13px;")
        root.addWidget(meta)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: rgba(255,255,255,0.08);")
        root.addWidget(line)

        btns = QHBoxLayout()
        self.done_btn   = QPushButton("Выполнено")
        self.edit_btn   = QPushButton("Настроить")
        self.toggle_btn = QPushButton("Отключить" if action.enabled else "Включить")
        self.delete_btn = QPushButton("Удалить")
        self.done_btn.setStyleSheet(_DONE_BTN)
        self.edit_btn.setStyleSheet(_CARD_BTN)
        self.toggle_btn.setStyleSheet(_CARD_BTN)
        self.delete_btn.setStyleSheet(_DELETE_BTN)
        for b in (self.done_btn, self.edit_btn, self.toggle_btn, self.delete_btn):
            b.setCursor(Qt.PointingHandCursor)
            b.setMinimumHeight(34)
        self.done_btn.clicked.connect(lambda: self.done_clicked.emit(self.action))
        self.edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.action))
        self.toggle_btn.clicked.connect(lambda: self.toggle_clicked.emit(self.action))
        self.delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.action))
        btns.addWidget(self.done_btn)
        btns.addWidget(self.edit_btn)
        btns.addWidget(self.toggle_btn)
        btns.addWidget(self.delete_btn)
        root.addLayout(btns)

        self.update_visuals()

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
        sev_map = {1: "Обычное уведомление", 2: "Полноэкранное с отменой", 3: "Полноэкранное без отмены"}
        reminder = (
            f"каждые {a.reminder_from_min} мин" if a.reminder_type == "fixed"
            else f"от {a.reminder_from_min} до {a.reminder_to_min} мин"
        )
        repetitions = (
            f"{a.repetitions_from} раз" if a.repetitions_type == "fixed"
            else f"от {a.repetitions_from} до {a.repetitions_to} раз"
        )
        return (
            f"Серьёзность: {sev_map[a.severity]}\n"
            f"Частота: {reminder}\n"
            f"Активность: {a.activity_start.strftime('%H:%M')}–{a.activity_end.strftime('%H:%M')}\n"
            f"Повторов сегодня: {a.today_count()} ({repetitions})"
        )

    def update_visuals(self):
        self.dot.setStyleSheet(f"color: {self.action.intensity_color()}; font-size: 18px;")
        self.toggle_btn.setText("Отключить" if self.action.enabled else "Включить")
        self.done_lbl.setText(f" {self.action.done_today} сегодня  /  {self.action.done_total} всего")

class SchedulePanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("schedulePanel")
        self.setStyleSheet("""
            QFrame#schedulePanel {
                background: #151922;
                border-left: 1px solid rgba(255,255,255,0.08);
            }
            QLabel { color: #f2f4f8; }
        """)
        self.setMinimumWidth(340)
        self.setMaximumWidth(420)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        self.prev_btn     = QToolButton()
        self.next_btn     = QToolButton()
        self.calendar_btn = QToolButton()
        _tb_style = """
            QToolButton {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 10px; color: #f2f4f8;
            }
            QToolButton:hover {
                background: rgba(255,138,0,0.16);
                border-color: rgba(255,138,0,0.45);
            }
        """
        for b in (self.prev_btn, self.next_btn, self.calendar_btn):
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedSize(34, 34)
            b.setStyleSheet(_tb_style)
        self.prev_btn.setText("←")
        self.next_btn.setText("→")
        self.calendar_btn.setText("📅")

        self.date_label = QLabel()
        self.date_label.setStyleSheet("font-size: 18px; font-weight: 700;")

        header.addWidget(self.prev_btn)
        header.addWidget(self.calendar_btn)
        header.addStretch(1)
        header.addWidget(self.date_label)
        header.addStretch(1)
        header.addWidget(self.next_btn)
        root.addLayout(header)

        sub = QLabel("График задач на выбранный день")
        sub.setStyleSheet("color: #9aa4b2; font-size: 13px;")
        root.addWidget(sub)

        self.list = QListWidget()
        self.list.setStyleSheet("""
            QListWidget { background: transparent; border: none; }
            QListWidget::item { margin: 0; padding: 0; }
        """)
        root.addWidget(self.list, 1)

        self.calendar = QCalendarWidget()
        self.calendar.setWindowFlags(Qt.Popup)
        self.calendar.setGridVisible(True)
        self.calendar.setStyleSheet("""
            QCalendarWidget { background: #171a21; color: #f2f4f8;
                border: 1px solid rgba(255,255,255,0.12); border-radius: 12px; }
            QCalendarWidget QToolButton { background: transparent; color: #f2f4f8; }
            QCalendarWidget QAbstractItemView {
                selection-background-color: #ff8a00; selection-color: white;
                background: #171a21; color: #f2f4f8; }
        """)
        self.calendar.clicked.connect(self._calendar_selected)
        self._selected_date = date.today()
        self.update_date_label()

    def current_date(self) -> date:
        return self._selected_date

    def set_date(self, d: date):
        self._selected_date = d
        self.calendar.setSelectedDate(d)
        self.update_date_label()

    def shift_days(self, delta: int):
        self.set_date(self._selected_date + timedelta(days=delta))

    def update_date_label(self):
        iso = self._selected_date.isoweekday() - 1
        self.date_label.setText(f"{WEEKDAYS_RU[iso]}, {self._selected_date.strftime('%d.%m.%Y')}")

    def _calendar_selected(self, qdate):
        self._selected_date = qdate.toPython()
        self.update_date_label()
        self.calendar.hide()

    def show_calendar_popup(self, anchor: QWidget):
        self.calendar.move(anchor.mapToGlobal(anchor.rect().bottomLeft()) + QPoint(0, 6))
        self.calendar.show()

    def refresh(self, actions: List[ActionItem]):
        self.list.clear()
        slots = self._build_slots(actions)
        if not slots:
            item = QListWidgetItem()
            lbl  = QLabel("На этот день задач нет")
            lbl.setStyleSheet("color: #9aa4b2; padding: 18px;")
            lbl.setAlignment(Qt.AlignCenter)
            item.setSizeHint(lbl.sizeHint() + QSize(10, 20))
            self.list.addItem(item)
            self.list.setItemWidget(item, lbl)
            return

        for t_str, act in slots:
            item = QListWidgetItem()
            w = QFrame()
            w.setStyleSheet("""
                QFrame { background: rgba(255,255,255,0.04);
                    border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; }
            """)
            lay = QVBoxLayout(w)
            lay.setContentsMargins(12, 10, 12, 10)
            t = QLabel(act.title)
            t.setStyleSheet("font-weight: 700; font-size: 14px;")
            t2 = QLabel(t_str)
            t2.setStyleSheet(f"color: {act.intensity_color()}; font-size: 13px;")
            lay.addWidget(t)
            lay.addWidget(t2)
            item.setSizeHint(QSize(10, 66))
            self.list.addItem(item)
            self.list.setItemWidget(item, w)

    def _build_slots(self, actions):
        d = self._selected_date
        slots = []
        for act in actions:
            if not act.is_active_on(d):
                continue
            count = act.today_count()
            win = self._mins_between(act.activity_start, act.activity_end)
            if count <= 0 or win <= 0:
                continue
            start = self._t2m(act.activity_start)
            if count == 1:
                slots.append((start, self._m2t(start).strftime("%H:%M"), act))
                continue
            step = max(1, win // max(1, count - 1))
            for i in range(count):
                m = min(start + i * step, start + win)
                slots.append((m, self._m2t(m).strftime("%H:%M"), act))
        slots.sort(key=lambda x: x[0])
        return [(t, a) for _, t, a in slots]

    @staticmethod
    def _mins_between(a: time, b: time) -> int:
        am = a.hour * 60 + a.minute
        bm = b.hour * 60 + b.minute
        if bm <= am: bm += 1440
        return bm - am

    @staticmethod
    def _t2m(t: time) -> int:
        return t.hour * 60 + t.minute

    @staticmethod
    def _m2t(m: int) -> time:
        m %= 1440
        return time(m // 60, m % 60)


# новое действие

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

        # Название
        self.title_edit = s(QLineEdit())
        self.title_edit.setPlaceholderText("Например: Размяться")
        form.addRow(hl("Название", "Что нужно сделать?"), self.title_edit)

        # Строгость
        self.severity = s(QComboBox())
        self.severity.addItems([
            "1 — Обычное уведомление",
            "2 — Полноэкранное с отменой",
            "3 — Полноэкранное без отмены",
        ])
        form.addRow(hl("Строгость", "1 — тихое. 2 — полный экран с кнопкой отмены. 3 — без отмены"), self.severity)

        # Таймер
        self.time_limit = IntBox(1, 9999, 15)
        form.addRow(hl("Время на выполнение (мин)", "Таймер для режимов 2 и 3"), self.time_limit)

        # Частота
        self.reminder_mode = s(QComboBox())
        self.reminder_mode.addItems(["Фиксированный интервал", "Диапазон интервала"])
        self.reminder_from = IntBox(1, 9999, 40)
        self.reminder_to   = IntBox(1, 9999, 60)
        form.addRow(hl("Частота", "Интервал между уведомлениями"), self.reminder_mode)
        form.addRow(QLabel(""), self._pair(self.reminder_from, self.reminder_to))

        # Период активности
        self.activity_start = s(QTimeEdit())
        self.activity_start.setDisplayFormat("HH:mm")
        self.activity_start.setTime(time(9, 0))
        self.activity_end = s(QTimeEdit())
        self.activity_end.setDisplayFormat("HH:mm")
        self.activity_end.setTime(time(18, 0))
        form.addRow(hl("Период активности", "Окно, в котором приходят уведомления"),
                    self._pair(self.activity_start, self.activity_end))

        # Количество повторений
        self.repetitions_mode = s(QComboBox())
        self.repetitions_mode.addItems(["Фиксированное количество", "Диапазон количества"])
        self.repetitions_from = IntBox(1, 9999, 3)
        self.repetitions_to   = IntBox(1, 9999, 5)
        form.addRow(hl("Количество напоминаний", "Сколько раз в день),
                    self._pair(self.repetitions_from, self.repetitions_to))

        # Срок действия
        self.expiry_mode = s(QComboBox())
        self.expiry_mode.addItems(["Всегда", "До даты"])
        self.expiry_date_edit = s(QDateEdit())
        self.expiry_date_edit.setCalendarPopup(True)
        self.expiry_date_edit.setDate(datetime.now().date())
        self.expiry_date_edit.setDisplayFormat("dd.MM.yyyy")
        form.addRow(hl("Срок действия", "До какой даты актуально"),
                    self._pair(self.expiry_mode, self.expiry_date_edit))

        # Режим дат
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

        # сигналы
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


# блокировка

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
        lay.addWidget(QLabel(f"Приложение продолжит работать в фоне, интерфейс будет недоступен {minutes} минут",
                             wordWrap=True, styleSheet="color: #cfd6df;"))
        btns = QHBoxLayout()
        ok = QPushButton("ОК", styleSheet=f"background: {PRIMARY}; color: white; border-radius: 10px; padding: 10px;")
        cancel = QPushButton("Отмена", styleSheet="background: rgba(255,255,255,0.06); color: #f2f4f8; border-radius: 10px; padding: 10px;")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok); btns.addWidget(cancel)
        lay.addLayout(btns)


# блок

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

#пульсация

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


# главная

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TaskPulse")
        self.resize(1280, 780)
        self.setMinimumSize(1100, 700)

        self.actions: List[ActionItem]        = load_actions()
        self.is_running                       = False
        self.locked_until: Optional[datetime] = None
        self.continuous_start: Optional[datetime] = None
        # статистика сессии — новое
        self.session_done = 0

        central = QWidget()
        self.setCentralWidget(central)
        main = QHBoxLayout(central)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        self.stack = QStackedWidget()
        main.addWidget(self.stack, 1)

        self.schedule_panel = SchedulePanel()
        main.addWidget(self.schedule_panel)
        self.panel_anim = QPropertyAnimation(self.schedule_panel, b"maximumWidth", self)
        self.panel_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.panel_anim.setDuration(260)

        self.main_page = QWidget()
        self.main_page.setStyleSheet(f"background: {BG}; color: {TEXT};")
        self._build_main_page()

        self.add_page = AddActionPage()
        self.add_page.cancel_clicked.connect(self._cancel_edit)

        self.stack.addWidget(self.main_page)
        self.stack.addWidget(self.add_page)
        self.stack.setCurrentWidget(self.main_page)

        self.overlay = OverlayBlocker(self.centralWidget())
        self.overlay.raise_()

        self._build_timers()
        self._apply_theme()
        self._refresh_actions()
        self._refresh_schedule()

        self.schedule_panel.prev_btn.clicked.connect(lambda: self._shift_date(-1))
        self.schedule_panel.next_btn.clicked.connect(lambda: self._shift_date(1))
        self.schedule_panel.calendar_btn.clicked.connect(
            lambda: self.schedule_panel.show_calendar_popup(self.schedule_panel.calendar_btn)
        )
        self._resize_overlay()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_overlay()

    def _resize_overlay(self):
        if self.overlay and self.centralWidget():
            self.overlay.setGeometry(self.centralWidget().rect())

    def _build_timers(self):
        t1 = QTimer(self)
        t1.timeout.connect(self._tick_ui)
        t1.start(1000)
        t2 = QTimer(self)
        t2.timeout.connect(self._tick_lock)
        t2.start(500)

    def _apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow {{ background: {BG}; }}
            QLabel       {{ color: {TEXT}; }}
            QPushButton  {{ font-size: 14px; }}
            QScrollArea  {{ border: none; background: transparent; }}
            QLineEdit, QComboBox, QDateEdit, QTimeEdit {{ font-size: 13px; }}
        """)

    def _build_main_page(self):
        layout = QVBoxLayout(self.main_page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # топ
        top = QHBoxLayout()
        vb  = QVBoxLayout()
        lbl = QLabel("TaskPulse")
        lbl.setStyleSheet("font-size: 28px; font-weight: 900;")
        sub = QLabel("Управление расписанием и действиями")
        sub.setStyleSheet(f"color: {MUTED}; font-size: 13px;")
        vb.addWidget(lbl); vb.addWidget(sub)
        top.addLayout(vb)
        top.addStretch(1)

        _tb = """
            QPushButton {
                background: rgba(255,255,255,0.06); color: #f2f4f8;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px; padding: 8px 14px;
            }
            QPushButton:hover { background: rgba(255,138,0,0.14); border-color: rgba(255,138,0,0.42); }
        """
        self.add_action_btn   = QPushButton("Добавить действие")
        self.lock_btn         = QPushButton("Блокировать")
        self.toggle_panel_btn = QPushButton("Скрыть панель")
        for b in (self.add_action_btn, self.lock_btn, self.toggle_panel_btn):
            b.setCursor(Qt.PointingHandCursor)
            b.setMinimumHeight(40)
            b.setStyleSheet(_tb)
        self.add_action_btn.clicked.connect(self._open_add)
        self.lock_btn.clicked.connect(self.request_lock)
        self.toggle_panel_btn.clicked.connect(self._toggle_schedule_panel)
        top.addWidget(self.add_action_btn)
        top.addWidget(self.lock_btn)
        top.addWidget(self.toggle_panel_btn)
        layout.addLayout(top)

        body = QHBoxLayout()
        body.setSpacing(16)
        layout.addLayout(body, 1)

        left = QVBoxLayout()
        left.setSpacing(16)
        body.addLayout(left, 2)

        # карточка Старт/Стоп
        status = QFrame()
        status.setStyleSheet("QFrame { background: #171a21; border: 1px solid rgba(255,255,255,0.06); border-radius: 20px; }")
        sl = QVBoxLayout(status)
        sl.setContentsMargins(18, 18, 18, 18)
        sl.setSpacing(14)

        head = QHBoxLayout()
        ht = QLabel("Сессия работы")
        ht.setStyleSheet("font-size: 20px; font-weight: 800;")
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #ff8a00;")
        head.addWidget(ht); head.addStretch(1); head.addWidget(self.timer_label)
        sl.addLayout(head)

        # строка статистики сессии
        self.session_stat_lbl = QLabel("Выполнено за сессию: 0")
        self.session_stat_lbl.setStyleSheet("color: #9aa4b2; font-size: 13px;")
        sl.addWidget(self.session_stat_lbl)

        self.pulse = PulseWidget()
        sl.addWidget(self.pulse, 1)

        # подсказка под анимацией
        self.next_action_lbl = QLabel("Нажмите Старт чтобы начать сессию")
        self.next_action_lbl.setStyleSheet(
            "color: #ff8a00; font-size: 13px; font-weight: 600; "
            "background: rgba(255,138,0,0.08); border-radius: 10px; padding: 8px 12px;"
        )
        self.next_action_lbl.setWordWrap(True)
        sl.addWidget(self.next_action_lbl)

        controls = QHBoxLayout()
        self.start_stop_btn = QPushButton("Старт")
        self.start_stop_btn.setMinimumHeight(48)
        self.start_stop_btn.setCursor(Qt.PointingHandCursor)
        self.start_stop_btn.clicked.connect(self.toggle_running)

        self.lock_local_btn = QPushButton("Блок интерфейса")
        self.lock_local_btn.setMinimumHeight(48)
        self.lock_local_btn.clicked.connect(self.request_lock)
        self.lock_local_btn.setCursor(Qt.PointingHandCursor)
        self.lock_local_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.06); color: #f2f4f8;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 14px; font-size: 14px; font-weight: 700; padding: 10px 16px;
            }
            QPushButton:hover { background: rgba(255,138,0,0.14); border-color: rgba(255,138,0,0.45); }
        """)
        controls.addWidget(self.start_stop_btn, 2)
        controls.addWidget(self.lock_local_btn, 1)
        sl.addLayout(controls)
        left.addWidget(status, 3)

        # список действий
        af = QFrame()
        af.setStyleSheet("QFrame { background: #171a21; border: 1px solid rgba(255,255,255,0.06); border-radius: 20px; }")
        afl = QVBoxLayout(af)
        afl.setContentsMargins(18, 18, 18, 18)
        afl.setSpacing(12)
        row = QHBoxLayout()
        lbl2 = QLabel("Действия")
        lbl2.setStyleSheet("font-size: 20px; font-weight: 800;")
        row.addWidget(lbl2); row.addStretch(1)
        afl.addLayout(row)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")
        self.actions_container = QWidget()
        self.actions_layout    = QVBoxLayout(self.actions_container)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(12)
        self.actions_layout.addStretch(1)
        self.scroll.setWidget(self.actions_container)
        afl.addWidget(self.scroll, 1)
        left.addWidget(af, 4)

        # правый блок
        right = QVBoxLayout()
        right.setSpacing(16)
        body.addLayout(right, 1)

        info = QFrame()
        info.setStyleSheet("QFrame { background: #171a21; border: 1px solid rgba(255,255,255,0.06); border-radius: 20px; }")
        il = QVBoxLayout(info)
        il.setContentsMargins(18, 18, 18, 18)
        il.setSpacing(12)
        il.addWidget(QLabel("Сводка", styleSheet="font-size: 20px; font-weight: 800;"))
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setStyleSheet("color: #cfd6df; font-size: 13px; line-height: 1.4;")
        il.addWidget(self.summary)
        right.addWidget(info)

        quick = QFrame()
        quick.setStyleSheet("QFrame { background: #171a21; border: 1px solid rgba(255,255,255,0.06); border-radius: 20px; }")
        ql = QVBoxLayout(quick)
        ql.setContentsMargins(18, 18, 18, 18)
        ql.setSpacing(10)
        ql.addWidget(QLabel("Подсказки", styleSheet="font-size: 20px; font-weight: 800;"))
        tips = QLabel(
            "> Старт — включает таймер сессии и анимацию\n"
            "> «Выполнено» — отметить что сделали задачу\n"
            "> Блокировка скрывает интерфейс на N минут\n"
            "> Панель расписания открывается справа\n"
            "> Счётчик сессии сбрасывается при Стоп\n"
        )
        tips.setWordWrap(True)
        tips.setStyleSheet("color: #cfd6df; font-size: 13px;")
        ql.addWidget(tips)
        right.addWidget(quick)
        right.addStretch(1)

        self._update_lock_button_visibility()
        self._update_status_ui()

    # навигация

    def _shift_date(self, delta: int):
        self.schedule_panel.shift_days(delta)
        self._refresh_schedule()

    def _toggle_schedule_panel(self):
        if self.schedule_panel.isVisible():
            self.schedule_panel.setVisible(False)
            self.toggle_panel_btn.setText("Открыть панель")
        else:
            self.schedule_panel.setVisible(True)
            self.schedule_panel.setMaximumWidth(0)
            self.panel_anim.stop()
            self.panel_anim.setStartValue(0)
            self.panel_anim.setEndValue(380)
            self.panel_anim.start()
            self.toggle_panel_btn.setText("Скрыть панель")

    # добавление / редактирование

    def _open_add(self):
        self.add_page.reset_for_new()
        try: self.add_page.save_clicked.disconnect()
        except Exception: pass
        self.add_page.save_clicked.connect(self._save_new_action)
        self.stack.setCurrentWidget(self.add_page)

    def _save_new_action(self, action: ActionItem):
        self.actions.append(action)
        save_actions(self.actions)
        self.stack.setCurrentWidget(self.main_page)
        self._refresh_actions()
        self._refresh_schedule()

    def _cancel_edit(self):
        self.stack.setCurrentWidget(self.main_page)

    def _edit_action(self, action: ActionItem):
        self.add_page.load_for_edit(action)
        try: self.add_page.save_clicked.disconnect()
        except Exception: pass
        target_uid = action.uid

        def save_replace(new_action: ActionItem):
            for i, a in enumerate(self.actions):
                if a.uid == target_uid:
                    # сохраняем счётчики
                    new_action.done_today = a.done_today
                    new_action.done_total = a.done_total
                    self.actions[i] = new_action
                    break
            else:
                self.actions.append(new_action)
            save_actions(self.actions)
            self.stack.setCurrentWidget(self.main_page)
            self._refresh_actions()
            self._refresh_schedule()
            try: self.add_page.save_clicked.disconnect(save_replace)
            except Exception: pass

        self.add_page.save_clicked.connect(save_replace)
        self.stack.setCurrentWidget(self.add_page)

    def _toggle_action(self, action: ActionItem):
        action.enabled = not action.enabled
        save_actions(self.actions)
        self._refresh_actions()
        self._refresh_schedule()

    def _delete_action(self, action: ActionItem):
        reply = QMessageBox.question(
            self, "Удаление",
            f"Удалить действие «{action.title}»?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.actions = [a for a in self.actions if a.uid != action.uid]
            save_actions(self.actions)
            self._refresh_actions()
            self._refresh_schedule()

    def _mark_done(self, action: ActionItem):
        if not self.is_running:
            QMessageBox.information(self, "Отметка", "Сначала включите режим Старт")
            return
        action.done_today += 1
        action.done_total += 1
        self.session_done += 1
        save_actions(self.actions)
        self._refresh_actions()
        self._update_summary()

    #запуск / блокировка

    def toggle_running(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.continuous_start = datetime.now()
        else:
            self.continuous_start = None
            # сбрасываем счётчик выполнений за сессию
            self.session_done = 0
            for a in self.actions:
                a.done_today = 0
            save_actions(self.actions)
            self._refresh_actions()
        self._update_status_ui()

    def request_lock(self):
        if not self.is_running:
            QMessageBox.information(self, "Блокировка", "Сначала включите режим Старт")
            return
        dialog = LockDialog(30, self)
        if dialog.exec() == QDialog.Accepted:
            minutes, ok = QInputDialog.getInt(
                self, "Время блокировки",
                "На сколько минут заблокировать интерфейс?",
                30, 1, 1440, 1,
            )
            if ok:
                self.locked_until = datetime.now() + timedelta(minutes=minutes)
                self.overlay.show()
                self.overlay.raise_()
                self._tick_lock()

    #обновление

    def _refresh_actions(self):
        while self.actions_layout.count() > 0:
            item = self.actions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.actions:
            empty = QLabel("Пока нет действий. Нажмите «Добавить действие»")
            empty.setStyleSheet("color: #9aa4b2; padding: 20px; background: rgba(255,255,255,0.03); border-radius: 14px;")
            empty.setWordWrap(True)
            self.actions_layout.addWidget(empty)
        else:
            for action in self.actions:
                card = ActionCard(action)
                card.edit_clicked.connect(self._edit_action)
                card.toggle_clicked.connect(self._toggle_action)
                card.delete_clicked.connect(self._delete_action)
                card.done_clicked.connect(self._mark_done)
                self.actions_layout.addWidget(card)

        self.actions_layout.addStretch(1)
        self._update_summary()

    def _refresh_schedule(self):
        self.schedule_panel.refresh(self.actions)

    def _update_summary(self):
        total   = len(self.actions)
        enabled = sum(1 for a in self.actions if a.enabled)
        locked  = bool(self.locked_until and self.locked_until > datetime.now())
        total_done = sum(a.done_total for a in self.actions)
        self.summary.setText(
            f"Всего действий: {total}\n"
            f"Активных: {enabled}\n"
            f"Режим Старт: {'включён' if self.is_running else 'выключен'}\n"
            f"Блокировка: {'активна' if locked else 'нет'}\n"
            f"Выполнено всего: {total_done}"
        )

    def _update_lock_button_visibility(self):
        self.lock_btn.setVisible(self.is_running)
        self.lock_local_btn.setVisible(self.is_running)

    def _update_status_ui(self):
        if self.is_running:
            self.start_stop_btn.setText("Стоп")
            self.start_stop_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {PRIMARY}; color: white; border: none;
                    border-radius: 14px; font-size: 15px; font-weight: 800; padding: 10px 16px;
                }}
                QPushButton:hover {{ background: #ff9e27; }}
            """)
        else:
            self.start_stop_btn.setText("Старт")
            self.start_stop_btn.setStyleSheet("""
                QPushButton {
                    background: #6b7280; color: white; border: none;
                    border-radius: 14px; font-size: 15px; font-weight: 700; padding: 10px 16px;
                }
                QPushButton:hover { background: #7b8493; }
            """)
        self.pulse.set_active(self.is_running)
        self._update_lock_button_visibility()
        self._update_summary()
        self._update_next_action()

    def _update_next_action(self):
        if not self.is_running:
            self.next_action_lbl.setText("Нажмите Старт чтобы начать сессию")
            return
        today = date.today()
        active = [a for a in self.actions if a.is_active_on(today)]
        if not active:
            self.next_action_lbl.setText("Сегодня действий нет")
            return
        # ближайшее - то у кого меньше выполнено относительно плана
        best = min(active, key=lambda a: a.done_today / max(1, a.today_count()))
        ratio = best.done_today / max(1, best.today_count())
        if ratio >= 1.0:
            self.next_action_lbl.setText("Все задачи на сегодня выполнены!")
        else:
            self.next_action_lbl.setText(
                f"Следующее: {best.title}  "
                f"({best.done_today}/{best.today_count()})"
            )

    # выполение в сесии

    def _tick_ui(self):
        if self.is_running and self.continuous_start:
            s = int((datetime.now() - self.continuous_start).total_seconds())
            self.timer_label.setText(f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}")
            self.session_stat_lbl.setText(f"Выполнено за сессию: {self.session_done}")
        else:
            self.timer_label.setText("00:00:00")
            self.session_stat_lbl.setText("Выполнено за сессию: 0")
        self._update_summary()
        self._update_next_action()
        for i in range(self.actions_layout.count()):
            w = self.actions_layout.itemAt(i).widget()
            if isinstance(w, ActionCard):
                w.update_visuals()
        self._refresh_schedule()

    def _tick_lock(self):
        if self.locked_until is None:
            self.overlay.hide()
            return
        if datetime.now() >= self.locked_until:
            self.locked_until = None
            self.overlay.hide()
            return
        remaining = self.locked_until - datetime.now()
        mins = int(remaining.total_seconds()) // 60
        secs = int(remaining.total_seconds()) % 60
        self.overlay.set_remaining(f"Осталось: {mins:02d}:{secs:02d}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

