# -*- coding: utf-8 -*-
"""
Конвертор наголосів для Android (Pydroid3, оффлайн)

Вхід: текстовий файл з символом наголосу \u0301
Вихід: текстовий файл з позначенням наголосів символом '+' після наголошеної голосної

Файли:
- Вхідний: /storage/emulated/0/Documents/inputf.txt
- Вихідний: "/storage/emulated/0/Documents/Out_Plus"
#/storage/emulated/0/Documents/Plus/outputf_plus_YYYYmmdd_HHMMSS.txt
"""

import os
from datetime import datetime

# === Налаштування ===
INPUT_FILE  = "/storage/emulated/0/book_projects/доповнення13_у_нас_гості/pluses/доповнення13_у_нас_гості.txt"
#"/storage/emulated/0/Documents/Out_u0301/Ніжний маніфест_u0301.txt"
#"/storage/emulated/0/Documents/inputf.txt"
OUTPUT_DIR  = "/storage/emulated/0/book_projects/доповнення13_у_нас_гості/pluses"
ACCENT_CHAR = "\u0301"
PLUS_SIGN   = "+"
UKR_VOWELS  = "аеєиіїоуюяАЕЄИІЇОУЮЯ"

# === Перевірка наявності вхідного файлу ===
if not os.path.exists(INPUT_FILE):
    print(f"Помилка: вхідний файл не знайдено:\n{INPUT_FILE}")
    exit()

# === Читання вхідного файлу ===
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    text = f.read()

# === Конвертація наголосів ===
new_text = ""
i = 0
while i < len(text):
    ch = text[i]
    if i + 1 < len(text) and text[i + 1] == ACCENT_CHAR and ch in UKR_VOWELS:
        new_text += ch + PLUS_SIGN
        i += 2  # пропустити символ наголосу
    else:
        new_text += ch
        i += 1

# === Формування імені вихідного файлу ===
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
os.makedirs(OUTPUT_DIR, exist_ok=True)
output_file = os.path.join(OUTPUT_DIR, f"outputf_plus_{timestamp}.txt")

# === Збереження результату ===
try:
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(new_text)
    print(f"Конвертація успішна! Вихідний файл: {os.path.basename(output_file)}")
except Exception as e:
    print(f"Помилка при збереженні файлу:\n{e}")
