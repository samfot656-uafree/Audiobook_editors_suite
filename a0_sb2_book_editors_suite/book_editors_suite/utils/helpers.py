# -*- coding: utf-8 -*-
"""
/storage/emulated/0/a0_sb2_book_editors_suite/book_editors_suite/utils/helpers.py

Допоміжні функції для всіх редакторів.
"""

import re
from datetime import datetime
from pathlib import Path

try:
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    BatteryManager = autoclass('android.os.BatteryManager')
    Intent = autoclass('android.content.Intent')
    IntentFilter = autoclass('android.content.IntentFilter')
except Exception:
    PythonActivity = Context = BatteryManager = Intent = IntentFilter = None

# Регулярка для слів з комбінованим наголосом та апострофом
WORD_RE = re.compile(
    r"(?:[^\W\d_](?:\u0301)?)+(?:'(?:[^\W\d_](?:\u0301)?)+)*",
    flags=re.UNICODE
)

def strip_combining_acute(s: str) -> str:
    """Видаляє комбінований наголос з рядка."""
    return s.replace('\u0301', '')

def match_casing(original: str, replacement: str) -> str:
    """Підбирає регістр заміни під оригінал."""
    if not original:
        return replacement
    if original.isupper():
        return replacement.upper()
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:].lower()
    return replacement.lower()

def get_clock_str() -> str:
    """Повертає поточний час у форматі HH:MM."""
    try:
        return datetime.now().strftime("%H:%M")
    except Exception:
        return "--:--"

def get_battery_percent() -> int:
    """
    Повертає заряд батареї у %.
    Спочатку через BatteryManager.getIntProperty, якщо недоступно - через ACTION_BATTERY_CHANGED.
    """
    try:
        if BatteryManager and PythonActivity:
            activity = PythonActivity.mActivity
            bm = activity.getSystemService(Context.BATTERY_SERVICE)
            val = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
            if isinstance(val, (int, float)) and 0 <= int(val) <= 100:
                return int(val)
    except Exception:
        pass
        
    try:
        if PythonActivity:
            activity = PythonActivity.mActivity
            intent = activity.registerReceiver(None, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
            level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
            scale = intent.getIntExtra(BatteryManager.EXTRA_SCALE, -1)
            if level >= 0 and scale > 0:
                return int(level * 100 / scale)
    except Exception:
        pass
        
    return -1

def sanitize_filename(s: str) -> str:
    """Очищує рядок для використання в назвах файлів."""
    s2 = re.sub(r"^##\s* ", "", s)
    s2 = re.sub(r"#g\d+: ? ", "", s2)
    s2 = re.sub(r"#S\d+: ? ", "", s2)
    s2 = s2.strip()
    s2 = re.sub(r"[^\w\d_-]", "_", s2)
    if not s2:
        s2 = "Глава"
    return s2