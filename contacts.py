from pathlib import Path

#Цвета
PRIMARY      = "#ff8a00"
PRIMARY_DARK = "#d86f00"
BG           = "#111318"
TEXT         = "#f2f4f8"
MUTED        = "#9aa4b2"
GRAY         = "#4b5563"
GREEN        = "#2ecc71"
YELLOW       = "#f1c40f"
RED          = "#e74c3c"

#Хранилище
SAVE_PATH = Path.home() / ".taskpulse_actions.json"

# Локализация
WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
ALL_DAYS    = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

SEVERITY_LABELS = {
    1: "Обычное уведомление",
    2: "Полноэкранное с отменой",
    3: "Полноэкранное без отмены",
}

#Общие стили кнопок
CARD_BTN = """
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
DELETE_BTN = """
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
DONE_BTN = """
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
INPUT_STYLE = """
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