from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import Optional, List

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QInputDialog, QLabel, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QStackedWidget, QToolButton,
    QVBoxLayout, QWidget,
)

from data import ActionItem, load_actions, save_actions
from widgets.cards import ActionCard
from widgets.schedule import SchedulePanel
from widgets.pulse import PulseWidget
from widgets.add_action import AddActionPage
from widgets.lock import LockDialog, OverlayBlocker

PRIMARY      = "#ff8a00"
BG           = "#111318"
TEXT         = "#f2f4f8"
MUTED        = "#9aa4b2"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TaskPulse")
        self.resize(1280, 780)
        self.setMinimumSize(1100, 700)

        self.actions: List[ActionItem]            = load_actions()
        self.is_running                           = False
        self.locked_until: Optional[datetime]     = None
        self.continuous_start: Optional[datetime] = None
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

        self.session_stat_lbl = QLabel("Выполнено за сессию: 0")
        self.session_stat_lbl.setStyleSheet("color: #9aa4b2; font-size: 13px;")
        sl.addWidget(self.session_stat_lbl)

        self.pulse = PulseWidget()
        sl.addWidget(self.pulse, 1)

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

    # запуск / блокировка

    def toggle_running(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.continuous_start = datetime.now()
        else:
            self.continuous_start = None
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

    # обновление

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
        best = min(active, key=lambda a: a.done_today / max(1, a.today_count()))
        ratio = best.done_today / max(1, best.today_count())
        if ratio >= 1.0:
            self.next_action_lbl.setText("Все задачи на сегодня выполнены!")
        else:
            self.next_action_lbl.setText(
                f"Следующее: {best.title}  "
                f"({best.done_today}/{best.today_count()})"
            )

    # тики

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