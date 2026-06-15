from __future__ import annotations

from datetime import date, time, timedelta
from typing import List, Tuple

from PySide6.QtCore import Qt, QPoint, QSize
from PySide6.QtWidgets import (
    QCalendarWidget, QFrame, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QToolButton, QVBoxLayout, QWidget,
)

from constants import ALL_DAYS, WEEKDAYS_RU
from models import ActionItem

_TB_STYLE = """
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


class SchedulePanel(QFrame):
    """Боковая панель расписания с навигацией по датам."""

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

        self._selected_date = date.today()
        self._build_ui()
        self.update_date_label()

    # ── Построение UI ──────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        # Навигация по дате
        header = QHBoxLayout()
        self.prev_btn     = self._tool_btn("←")
        self.next_btn     = self._tool_btn("→")
        self.calendar_btn = self._tool_btn("📅")
        self.date_label   = QLabel()
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

        # Всплывающий календарь
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

    # ── Публичный API ──────────────────────────────────────────────────────────

    def current_date(self) -> date:
        return self._selected_date

    def set_date(self, d: date) -> None:
        self._selected_date = d
        self.calendar.setSelectedDate(d)
        self.update_date_label()

    def shift_days(self, delta: int) -> None:
        self.set_date(self._selected_date + timedelta(days=delta))

    def update_date_label(self) -> None:
        iso = self._selected_date.isoweekday() - 1
        self.date_label.setText(
            f"{WEEKDAYS_RU[iso]}, {self._selected_date.strftime('%d.%m.%Y')}"
        )

    def show_calendar_popup(self, anchor: QWidget) -> None:
        self.calendar.move(
            anchor.mapToGlobal(anchor.rect().bottomLeft()) + QPoint(0, 6)
        )
        self.calendar.show()

    def refresh(self, actions: List[ActionItem]) -> None:
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
            t  = QLabel(act.title)
            t.setStyleSheet("font-weight: 700; font-size: 14px;")
            t2 = QLabel(t_str)
            t2.setStyleSheet(f"color: {act.intensity_color()}; font-size: 13px;")
            lay.addWidget(t)
            lay.addWidget(t2)
            item.setSizeHint(QSize(10, 66))
            self.list.addItem(item)
            self.list.setItemWidget(item, w)

    # ── Внутренние методы ──────────────────────────────────────────────────────

    def _calendar_selected(self, qdate) -> None:
        self._selected_date = qdate.toPython()
        self.update_date_label()
        self.calendar.hide()

    def _build_slots(
        self, actions: List[ActionItem]
    ) -> List[Tuple[str, ActionItem]]:
        d = self._selected_date
        raw: List[Tuple[int, str, ActionItem]] = []

        for act in actions:
            if not act.is_active_on(d):
                continue
            count = act.today_count()
            win   = self._mins_between(act.activity_start, act.activity_end)
            if count <= 0 or win <= 0:
                continue
            start = self._t2m(act.activity_start)
            if count == 1:
                raw.append((start, self._m2t(start).strftime("%H:%M"), act))
                continue
            step = max(1, win // max(1, count - 1))
            for i in range(count):
                m = min(start + i * step, start + win)
                raw.append((m, self._m2t(m).strftime("%H:%M"), act))

        raw.sort(key=lambda x: x[0])
        return [(t, a) for _, t, a in raw]

    @staticmethod
    def _mins_between(a: time, b: time) -> int:
        am = a.hour * 60 + a.minute
        bm = b.hour * 60 + b.minute
        if bm <= am:
            bm += 1440
        return bm - am

    @staticmethod
    def _t2m(t: time) -> int:
        return t.hour * 60 + t.minute

    @staticmethod
    def _m2t(m: int) -> time:
        m %= 1440
        return time(m // 60, m % 60)

    @staticmethod
    def _tool_btn(text: str) -> QToolButton:
        btn = QToolButton()
        btn.setText(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(34, 34)
        btn.setStyleSheet(_TB_STYLE)
        return btn