from __future__ import annotations

import json
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import Optional, List

from constants import SAVE_PATH, GREEN, YELLOW, RED


# ── Вспомогательные конвертеры ────────────────────────────────────────────────

def _time_to_str(t: time) -> str:
    return t.strftime("%H:%M")

def _str_to_time(s: str) -> time:
    h, m = map(int, s.split(":"))
    return time(h, m)

def _date_to_str(d: Optional[date]) -> Optional[str]:
    return d.isoformat() if d else None

def _str_to_date(s: Optional[str]) -> Optional[date]:
    return date.fromisoformat(s) if s else None


# ── Модель ────────────────────────────────────────────────────────────────────

@dataclass
class ActionItem:
    uid:                str
    title:              str
    severity:           int
    time_limit_minutes: Optional[int]
    reminder_type:      str
    reminder_from_min:  int
    reminder_to_min:    int
    activity_start:     time
    activity_end:       time
    repetitions_type:   str
    repetitions_from:   int
    repetitions_to:     int
    expiry_mode:        str
    expiry_date:        Optional[date]
    active_days:        List[int]
    specific_date:      Optional[date]
    date_mode:          str
    enabled:            bool     = True
    created_at:         datetime = field(default_factory=datetime.now)
    done_today:         int      = 0
    done_total:         int      = 0

    # ── Бизнес-логика ─────────────────────────────────────────────────────────

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
        if count <= 3:
            return GREEN
        if count <= 6:
            return YELLOW
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


# ── Сериализация ──────────────────────────────────────────────────────────────

def _action_to_dict(a: ActionItem) -> dict:
    return {
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
    }

def _action_from_dict(d: dict) -> ActionItem:
    return ActionItem(
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
    )


def save_actions(actions: List[ActionItem]) -> None:
    SAVE_PATH.write_text(
        json.dumps([_action_to_dict(a) for a in actions], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def load_actions() -> List[ActionItem]:
    if not SAVE_PATH.exists():
        return []
    try:
        data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
        return [_action_from_dict(d) for d in data]
    except Exception:
        return []