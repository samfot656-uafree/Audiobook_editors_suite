# -*- coding: utf-8 -*-
"""
Accent editor + TTS for Android (Kivy + Pyjnius).
Працює в Pydroid3.

Екрани:
- Вікно редагування тексту:
    Слухати | Пауза | Правити слово | Наступний абзац | ...
    (панель тексту)

- Вікно редагування слова:
    Слухати | Наголос | Сл+текст | В текст | Назад
    (панель слова)

- Вікно додаткових кнопок:
    До txt | До mp3 | День-ніч | Сортувати словник | Назад

Важливо:
- Авто-додавання наголосів зі словника: якщо у слові вже є U+0301 – залишаємо як є.
- Ручні правки у текст вставляються з правильним підбором регістру.
- У словник зберігаємо НИЖНІЙ регістр: "без_наголосу": "з_наголосом" (обидва lower()).
- Клавіатура перекриває низ, не зсуває розкладку: Window.softinput_mode="below_target".
"""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock

from jnius import autoclass
import json
import os
import re
from datetime import datetime
from gtts import gTTS

import shutil
import logging
from pathlib import Path
import sys
from typing import Optional, List, Tuple


# ---- Шляхи ----
ACCENTS_FILE = "/storage/emulated/0/Documents/pidgotovka_knigi/jsons/accents_probl.json"

INPUT_FILE   = "/storage/emulated/0/Documents/pidgotovka_knigi/txt/Чекаючий.1.1.txt"

OUT_TXT_FOLDER   = "/storage/emulated/0/Documents/pidgotovka_knigi/txt"

OUT_MP3_FOLDER = "/storage/emulated/0/Documents/Out_mp3"


# ---- Android Java via Pyjnius ----
TextToSpeech   = autoclass('android.speech.tts.TextToSpeech')
Locale         = autoclass('java.util.Locale')
HashMap        = autoclass('java.util.HashMap')
PythonActivity = autoclass('org.kivy.android.PythonActivity')

# --- ДОДАНО для батареї/інтентів ---
Context        = autoclass('android.content.Context')
BatteryManager = autoclass('android.os.BatteryManager')
Intent         = autoclass('android.content.Intent')
IntentFilter   = autoclass('android.content.IntentFilter')

# ---- Регулярка для слів з комбінованим наголосом та апострофом ----
# ОНОВЛЕНО: допускає наголос після будь-якої літери (в т.ч. останньої)
WORD_RE = re.compile(
    r"(?:[^\W\d_](?:\u0301)?)+(?:'(?:[^\W\d_](?:\u0301)?)+)*",
    flags=re.UNICODE
)

# ----------------- Допоміжні функції ------------
#-------------------------------------------------
def strip_combining_acute(s: str) -> str:
    """Видаляє комбінований наголос"""
    return s.replace('\u0301', '')

#-------------------------------------------------
def timestamp() -> str:
        """Повертає поточний час у форматі dd_mm_rrrr_gg_hh"""
        return datetime.now().strftime("%d_%m_%Y_%H_%M")
        
#------------------------------------------------- 
def match_casing(original: str, replacement: str) -> str:
    """
    Підбирає регістр replacement під оригінал:
    - ВСІ великі -> усе велике
    - Перша буква велика -> лише перша велика
    """
    if not replacement:
        return replacement
    letters = [ch for ch in original if ch.isalpha()]
    if letters and all(ch.isupper() for ch in letters):
        return replacement.upper()
    first_alpha_idx = next((i for i, ch in enumerate(original) if ch.isalpha()), None)
    if first_alpha_idx is not None and original[first_alpha_idx].isupper():
        rep_list = list(replacement)
        for j, ch in enumerate(rep_list):
            if ch.isalpha():
                rep_list[j] = ch.upper()
                break
        return "".join(rep_list)
    return replacement

#-------------------------------------------------
def get_clock_str() -> str:
    """Поточний час ГГ:ХХ"""
    try:
        return datetime.now().strftime("%H:%M")
    except Exception:
        return "--:--"

#-------------------------------------------------
def get_battery_percent() -> int:
    """
    Повертає заряд батареї у %.
    Спершу через BatteryManager.getIntProperty, якщо недоступно — через ACTION_BATTERY_CHANGED.
    """
    try:
        activity = PythonActivity.mActivity
        bm = activity.getSystemService(Context.BATTERY_SERVICE)
        val = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        if isinstance(val, (int, float)) and 0 <= int(val) <= 100:
            return int(val)
    except Exception as e:
        print("Battery via BatteryManager error:", e)
    try:
        activity = PythonActivity.mActivity
        intent = activity.registerReceiver(None, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
        scale = intent.getIntExtra(BatteryManager.EXTRA_SCALE, -1)
        if level >= 0 and scale > 0:
            return int(level * 100 / scale)
    except Exception as e:
        print("Battery via ACTION_BATTERY_CHANGED error:", e)
    return -1

# ----------------- TTS -----------------
def init_tts():
    try:
        tts = TextToSpeech(PythonActivity.mActivity, None)
        try:
            tts.setLanguage(Locale.forLanguageTag("uk-UA"))
        except Exception:
            try:
                tts.setLanguage(Locale("uk"))
            except Exception:
                pass
        return tts
    except Exception as e:
        print("Error init TTS:", e)
        return None

#-------------------------------------------------
def safe_tts_speak(tts, text: str):
    if text and tts:
        try:
            params = HashMap()
            params.put("volume", "1.0")
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, params)
        except Exception as e:
            print("TTS speak error:", e)

#-------------------------------------------------
def stop_tts(tts):
    if tts:
        try:
            tts.stop()
        except Exception as e:
            print("TTS stop error:", e)
# ----------------- Попап редагування слова ---
class EditWordPopup(Popup):
    """Попап для редагування слова, вставки наголосу та збереження"""

#-------------------------------------------------        
    def __init__(self, main_app, original_word, **kwargs):
        super().__init__(**kwargs)
        self.main_app = main_app
        self.original_word = original_word
        self.title = f"Редагування: {original_word}"
        self.size_hint = (0.98, 0.88)

        root = BoxLayout(orientation='vertical', spacing=8, padding=8)
        btn_row = BoxLayout(size_hint_y=None, height=160, spacing=8)
        self.btn_listen = Button(text="Слухати", font_size=42)
        self.btn_insert = Button(text="Наголос", font_size=42)
        self.btn_save_both = Button(text="Сл+текст", font_size=42)
        self.btn_save_text = Button(text="В текст", font_size=42)
        self.btn_cancel   = Button(text="Назад", font_size=42)
        for b in (self.btn_listen, self.btn_insert, self.btn_save_both, self.btn_save_text, self.btn_cancel):
            btn_row.add_widget(b)
        root.add_widget(btn_row)

        self.edit_input = TextInput(text=original_word, font_size=72, multiline=False)
        root.add_widget(self.edit_input)

        # ---  контейнер з годинником і батареєю під полем редагування ---
        info_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=80, spacing=12)
        self.clock_label = Label(text=f"Час: {get_clock_str()}", font_size=36, halign='left', valign='middle')
        self.clock_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        batt = get_battery_percent()
        batt_txt = f"{batt}%" if batt >= 0 else "—"
        self.batt_label = Label(text=f"Батарея: {batt_txt}", font_size=36, halign='right', valign='middle')
        self.batt_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        info_row.add_widget(self.clock_label)
        info_row.add_widget(self.batt_label)
        root.add_widget(info_row)

        # Прив'язка функцій кнопок
        self.btn_listen.bind(on_press=self.on_listen_word)
        self.btn_insert.bind(on_press=self.on_insert_accent)
        self.btn_save_both.bind(on_press=self.on_save_dict_and_text)
        self.btn_save_text.bind(on_press=self.on_save_text_only)
        self.btn_cancel.bind(on_press=lambda *_: self.dismiss())

        self.content = root
        Clock.schedule_once(lambda *_: self.apply_theme_from_app(), 0)
        
#-------------------------------------------------
    def apply_theme_from_app(self):
                """Встановлює колір поля редагування слова залежно від заряду батареї. Кольори кнопок відповідно до День-ніч"""
                batt = get_battery_percent()
                colors = self.main_app.get_theme_colors()
                if batt >= 0:
                	self.edit_input.cursor_color = (0.03, 0.85, 0.53 ,1)
                	if batt < 25:
                		self.edit_input.background_color = (1, 0.2, 0.2, 1)
                	elif batt < 30:
                		self.edit_input.background_color = (1, 0.6, 0.6, 1)
                	else:
                		self.edit_input.background_color = colors["input_bg"]
                		self.edit_input.foreground_color = colors["input_fg"]
                
                for b in (self.btn_listen, self.btn_insert, self.btn_save_both, self.btn_save_text, self.btn_cancel, self.batt_label, self.clock_label):
                	b.background_normal = ""
                	b.background_color = colors["button_bg"]
                	b.color = colors["button_fg"]
                
                try:
                    self.edit_input.cursor_color = (0.03, 0.85, 0.53 ,1)
                except Exception:
                    pass

#-------------------------------------------------
    def on_insert_accent(self, *_):
        txt = strip_combining_acute(self.edit_input.text)
        try:
            pos = self.edit_input.cursor_index()
        except Exception:
            pos = len(txt)
        new = txt[:pos] + '\u0301' + txt[pos:]
        self.edit_input.text = new
        try:
            self.edit_input.cursor = (pos + 1, 0)
        except Exception:
            pass

#-------------------------------------------------
    def on_listen_word(self, *_):
        text = self.edit_input.text.strip()
        if text:
            safe_tts_speak(self.main_app.tts, text)

#-------------------------------------------------
    def on_save_dict_and_text(self, *_):
        new_word = self.edit_input.text.strip()
        if not new_word:
            self.dismiss()
            return
        # Зберігаємо в словник нижнім регістром
        key = strip_combining_acute(self.original_word).lower()
        self.main_app.accents[key] = new_word.lower()
        self.main_app.save_accents()
        # Додаємо в текст у поточному регістрі
        replaced = match_casing(self.original_word, new_word)
        self.main_app.replace_word_in_current_paragraph(self.original_word, replaced)
        self.dismiss()

#-------------------------------------------------
    def on_save_text_only(self, *_):
        new_word = self.edit_input.text.strip()
        if not new_word:
            self.dismiss()
            return
        replaced = match_casing(self.original_word, new_word)
        self.main_app.replace_word_in_current_paragraph(self.original_word, replaced)
        self.dismiss()


# ----------------- Попап додаткових кнопок -----------------
class ExtraButtonsPopup(Popup):
    """Вікно для рідко використовуваних кнопок"""

#-------------------------------------------------        
    def __init__(self, main_app, **kwargs):
        super().__init__(**kwargs)
        self.main_app = main_app
        self.title = "Додаткові кнопки"
        self.size_hint = (0.95, 0.8)

        root = BoxLayout(orientation='vertical', spacing=8, padding=8)

        # Ряд кнопок зверху
        btn_row = BoxLayout(size_hint_y=None, height=150, spacing=8)
        self.btn_save_txt = Button(text="До txt", font_size=42)
        self.btn_save_mp3 = Button(text="До mp3", font_size=42)
        self.btn_theme    = Button(text="День-ніч", font_size=42)
        self.btn_sort_dict= Button(text="Сортуй", font_size=42)
        self.btn_back     = Button(text="Назад", font_size=42)
        for b in (self.btn_save_txt, self.btn_save_mp3, self.btn_theme, self.btn_sort_dict, self.btn_back):
            btn_row.add_widget(b)
        root.add_widget(btn_row)
# кнопки зверху
        root.add_widget(Label())  
# порожній простір під кнопками
        self.content = root

        # Прив'язка кнопок
        self.btn_save_txt.bind(on_press=self.on_save_txt)
        self.btn_save_mp3.bind(on_press=self.on_save_mp3)
        self.btn_theme.bind(on_press=self.on_toggle_theme)
        self.btn_sort_dict.bind(on_press=self.on_sort_dict)
        self.btn_back.bind(on_press=lambda *_: self.dismiss())

        Clock.schedule_once(lambda *_: self.apply_theme_from_app(), 0)

#-------------------------------------------------
    def apply_theme_from_app(self):
        colors = self.main_app.get_theme_colors()
        for b in (self.btn_save_txt, self.btn_save_mp3, self.btn_theme, self.btn_sort_dict, self.btn_back):
            b.background_normal = ""
            b.background_color = colors["button_bg"]
            b.color = colors["button_fg"]

#-------------------------------------------------
    def on_save_txt(self, *_):
        self.main_app.save_full_text()
        self.dismiss()

#-------------------------------------------------
    def on_save_mp3(self, *_):
        self.main_app.save_full_mp3()
        self.dismiss()

#-------------------------------------------------
    def on_toggle_theme(self, *_):
        self.main_app.toggle_theme()
        self.dismiss()

#-------------------------------------------------
    def on_sort_dict(self, *_):
        """Сортування словника за ключами"""
        self.main_app.accents = dict(sorted(self.main_app.accents.items()))
        self.main_app.save_accents()
        Popup(title="Словник відсортовано", content=Label(text="Словник успішно відсортовано"),
              size_hint=(0.8,0.3)).open()

# ----------------- Основний додаток -----------------
class AccentApp(App):
    
#-------------------------------------------------    
    def build(self):
        Window.softinput_mode = "below_target"

        self.accents = self.load_accents()
        self.text_for_correction = []
        self.fixed_text = []
        self.current_idx = -1
        self.selected_word = None
        self.tts = self.init_tts()
        self.theme_mode = "day"

        root = BoxLayout(orientation='vertical', spacing=28, padding=28)

        # Верхній ряд кнопок
        top_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=150, spacing=8)
        self.btn_listen  = Button(text="Слухати", font_size=42)
        self.btn_pause   = Button(text="Пауза", font_size=42)
        self.btn_edit    = Button(text="Правити", font_size=42, disabled=True)
        self.btn_next    = Button(text="Наступний", font_size=42)
        self.btn_extra   = Button(text="...", font_size=42)
        for b in (self.btn_listen, self.btn_pause, self.btn_edit, self.btn_next, self.btn_extra):
            top_row.add_widget(b)
        root.add_widget(top_row)

        # TextInput для тексту
        self.text_input = TextInput(font_size=72, multiline=True)
        self.text_input.bind(on_touch_down=self.on_text_touch)
        root.add_widget(self.text_input)

        # Прив'язка кнопок
        self.btn_listen.bind(on_press=lambda *_: self.listen_current_paragraph())
        self.btn_pause.bind(on_press=lambda *_: self.stop_tts())
        self.btn_edit.bind(on_press=self.open_edit_popup)
        self.btn_next.bind(on_press=lambda *_: self.go_next_paragraph())
        self.btn_extra.bind(on_press=lambda *_: ExtraButtonsPopup(self).open())

        # Авто-завантаження тексту
        Clock.schedule_once(lambda *_: self.open_and_prepare_text(), 0.1)
        Clock.schedule_once(lambda *_: self.apply_theme(), 0)

        return root

    # ---------- Тема день/ніч ----------
    def get_theme_colors(self):
        if self.theme_mode == "day":
            return dict(button_bg=(0.5,0.5,0.5,1), button_fg=(1,1,1,1),
                        input_bg=(1,1,1,1), input_fg=(0,0,0,1))
        else:
            return dict(button_bg=(0,0,0,1), button_fg=(0.6,0.85,1,1),
                        input_bg=(0,0,0,1), input_fg=(0,0,1,1))

#-------------------------------------------------
    def apply_theme(self):
        colors = self.get_theme_colors()
        for b in (self.btn_listen, self.btn_pause, self.btn_edit, self.btn_next, self.btn_extra):
            b.background_normal = ""
            b.background_color = colors["button_bg"]
            b.color = colors["button_fg"]
        self.text_input.background_color = colors["input_bg"]
        self.text_input.foreground_color = colors["input_fg"]
        
        self.text_input.cursor_color = (0.03, 0.85, 0.53 ,1)
        Window.clearcolor = colors["input_bg"]

#-------------------------------------------------
    def toggle_theme(self):
        self.stop_tts()
        self.theme_mode = "night" if self.theme_mode == "day" else "day"
        self.apply_theme()

    # ---------- Словник ----------
    def load_accents(self):
        if os.path.exists(ACCENTS_FILE):
            try:
                with open(ACCENTS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data
            except Exception as e:
                print("Error loading accents.json:", e)
        return {}

#-------------------------------------------------
    def save_accents(self):
        try:
            with open(ACCENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.accents, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Error saving accents:", e)

    # ---------- TTS ----------
    def init_tts(self):
        try:
            tts = TextToSpeech(PythonActivity.mActivity, None)
            try:
                tts.setLanguage(Locale.forLanguageTag("uk-UA"))
            except Exception:
                try:
                    tts.setLanguage(Locale("uk"))
                except Exception:
                    pass
            return tts
        except Exception as e:
            print("Error init TTS:", e)
            return None

#-------------------------------------------------
    def safe_tts_speak(self, text: str):
        if text and self.tts:
            try:
                params = HashMap()
                params.put("volume", "1.0")
                self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, params)
            except Exception as e:
                print("TTS speak error:", e)

#-------------------------------------------------
    def stop_tts(self):
        if self.tts:
            try:
                self.tts.stop()
            except Exception as e:
                print("TTS stop error:", e)

#-------------------------------------------------
    def listen_current_paragraph(self):
        text = self.text_input.text.strip()
        if text:
            self.safe_tts_speak(text)
            
    # ---------- Текст ----------
    def open_and_prepare_text(self):
        """Завантажує текст, додає наголоси з словника автоматично, зберігаючи ручні зміни"""
        if not os.path.exists(INPUT_FILE):
            Popup(title="Помилка", content=Label(text=f"Файл не знайдено:\n{INPUT_FILE}"),
                  size_hint=(0.9, 0.35)).open()
            return
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            raw = f.read()
            

        # Авто-додавання наголосів зі словника
#-------------------------------------------------        
        def repl(m):
            token = m.group(0)
            if '\u0301' in token:
                return token
            key = strip_combining_acute(token).lower()
            val = self.accents.get(key)
            return match_casing(token, val) if val else token

        accented_text = WORD_RE.sub(repl, raw)
        paragraphs = accented_text.split("\n")
        self.text_for_correction = paragraphs
        self.fixed_text = []
        self.current_idx = -1

        # Початковий абзац
        i = 0
        while i < len(self.text_for_correction) and self.text_for_correction[i] == "":
            self.fixed_text.append("")
            i += 1
        if i < len(self.text_for_correction):
            self.current_idx = i
            self.text_input.text = self.text_for_correction[self.current_idx]
        else:
            self.current_idx = len(self.text_for_correction)
            self.text_input.text = ""
            Popup(title="Готово", content=Label(text="Текст порожній."), size_hint=(0.7,0.3)).open()
        self.clear_selection_state()
        
#-------------------------------------------------
    def go_next_paragraph(self):
        self.stop_tts()
        if self.current_idx == -1 or self.current_idx >= len(self.text_for_correction):
            return
        self.fixed_text.append(self.text_input.text)
        self.current_idx += 1
        while self.current_idx < len(self.text_for_correction) and self.text_for_correction[self.current_idx] == "":
            self.fixed_text.append("")
            self.current_idx += 1
        if self.current_idx < len(self.text_for_correction):
            self.text_input.text = self.text_for_correction[self.current_idx]
        else:
            self.text_input.text = ""
            Popup(title="Кінець", content=Label(text="Досягнуто кінця тексту."), size_hint=(0.7,0.3)).open()
        self.clear_selection_state()
        
#-------------------------------------------------
    def build_full_text(self) -> str:
        parts = list(self.fixed_text)
        if 0 <= self.current_idx < len(self.text_for_correction):
            parts.append(self.text_input.text)
            parts.extend(self.text_for_correction[self.current_idx+1:])
        return "\n".join(parts)

    # ---------- Виділення слова ----------
    def on_text_touch(self, instance, touch):
        if not instance.collide_point(*touch.pos):
            return False
        Clock.schedule_once(lambda *_: self.detect_word_at_cursor(), 0.01)
        return False

#-------------------------------------------------
    def _is_letter(self, ch: str) -> bool:
        return bool(re.match(r"[^\W\d_]", ch, flags=re.UNICODE))
        
#-------------------------------------------------
    def detect_word_at_cursor(self):
        """Визначає слово під курсором"""
        try:
            idx = self.text_input.cursor_index()
        except Exception:
            idx = None
        if idx is None:
            self.clear_selection_state()
            return
        text = self.text_input.text
        if not text:
            self.clear_selection_state()
            return
        if idx >= len(text) or not self._is_letter(text[idx:idx+1]):
            i = min(idx, len(text)-1)
            while i >= 0 and not self._is_letter(text[i:i+1]):
                i -= 1
            if i < 0:
                self.clear_selection_state()
                return
            idx = i

        # Знаходження початку слова
        start = idx
        while start > 0:
            prev_char = text[start-1]
            if self._is_letter(prev_char) or prev_char == '\u0301':
                start -= 1
                continue
            if prev_char == "'" and start-2 >= 0 and self._is_letter(text[start-2]) and self._is_letter(text[start]):
                start -= 1
                continue
            break

        # Знаходження кінця слова
        end = idx + 1
        while end < len(text):
            next_char = text[end]
            if self._is_letter(next_char) or next_char == '\u0301':
                end += 1
                continue
            if next_char == "'" and end+1 < len(text) and self._is_letter(text[end-1]) and self._is_letter(text[end+1]):
                end += 1
                continue
            break

        word = text[start:end]
        if WORD_RE.fullmatch(word):
            self.selected_word = word
            self.btn_edit.disabled = False
        else:
            self.clear_selection_state()

#-------------------------------------------------
    def clear_selection_state(self):
        self.selected_word = None
        self.btn_edit.disabled = True

#-------------------------------------------------
    def open_edit_popup(self, *_):
        if not self.selected_word:
            return
        EditWordPopup(self, self.selected_word).open()

#-------------------------------------------------
    def replace_word_in_current_paragraph(self, old_word: str, new_word: str):
        if self.current_idx == -1 or self.current_idx >= len(self.text_for_correction):
            return
        text = self.text_input.text
        replaced_text = text.replace(old_word, new_word)
        self.text_input.text = replaced_text

# ----------------- Вікно додаткових кнопок -----------------
class ExtraButtonsPopup(Popup):
    """Вікно для рідко використовуваних кнопок"""
    
#-------------------------------------------------    
    def __init__(self, main_app, **kwargs):
        super().__init__(**kwargs)
        self.main_app = main_app
        self.title = "Додаткові кнопки"
        self.size_hint = (0.95, 0.8)

        root = BoxLayout(orientation='vertical', spacing=8, padding=8)

        # Ряд кнопок угорі
        btn_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=150, spacing=8)
        self.btn_save_txt = Button(text="До txt", font_size=42)
        self.btn_save_mp3 = Button(text="До mp3", font_size=42)
        self.btn_sort_dict = Button(text="Сортуй", font_size=42)
        self.btn_theme    = Button(text="День-ніч", font_size=42)
        self.btn_back     = Button(text="Назад", font_size=42)
        for b in (self.btn_save_txt, self.btn_save_mp3, self.btn_sort_dict, self.btn_theme, self.btn_back):
            btn_row.add_widget(b)
        root.add_widget(btn_row)

# кнопки зверху
        root.add_widget(Label())  # порожній простір під кнопками

        self.content = root

        # Прив'язка кнопок
        self.btn_save_txt.bind(on_press=self.on_save_txt)
        self.btn_save_mp3.bind(on_press=self.on_save_mp3)
        self.btn_sort_dict.bind(on_press=self.on_sort_dict)
        self.btn_theme.bind(on_press=self.on_toggle_theme)
        self.btn_back.bind(on_press=lambda *_: self.dismiss())

        Clock.schedule_once(lambda *_: self.apply_theme_from_app(), 0)
        
#-------------------------------------------------
    def apply_theme_from_app(self):
        colors = self.main_app.get_theme_colors()
        for b in (self.btn_save_txt, self.btn_save_mp3, self.btn_sort_dict, self.btn_theme, self.btn_back):
            b.background_normal = ""
            b.background_color = colors["button_bg"]
            b.color = colors["button_fg"]

#-------------------------------------------------
    def on_save_txt(self, *_):
        self.main_app.save_full_text()
        self.dismiss()

#-------------------------------------------------
    def on_save_mp3(self, *_):
        self.main_app.save_full_mp3()
        self.dismiss()

#-------------------------------------------------
    def on_sort_dict(self, *_):
        self.main_app.accents = dict(sorted(self.main_app.accents.items()))
        self.main_app.save_accents()
        Popup(title="Словник", content=Label(text="Словник відсортовано"), size_hint=(0.7,0.3)).open()
        
#-------------------------------------------------
    def on_toggle_theme(self, *_):
        self.main_app.toggle_theme()
        self.dismiss()


# ----------------- Основні функції збереження в AccentApp -----------------

def save_full_text(self):
    """Зберігає весь текст у TXT"""
    self.stop_tts()
    content = self.build_full_text()
    try:
            with open(INPUT_FILE, "w", encoding="utf-8") as f:
            	f.write(content)
            Popup(title="Збережено", content=Label(text=f"TXT збережено:\n{INPUT_FILE}"),
            size_hint=(0.9,0.35)).open()
    except Exception as e:
    	Popup(title="Помилка збереження", content=Label(text=str(e)), size_hint=(0.9,0.35)).open()

#-------------------------------------------------
def save_full_mp3(self):
    """Зберігає весь текст у MP3 через gTTS"""
    self.stop_tts()
    content = self.build_full_text().strip()
    if not content:
        return
    t = timestamp()
    
      # Переконаємося, що папка існує
    os.makedirs(OUT_MP3_FOLDER, exist_ok=True)
    # Отримуємо назву без розширення  
    inp_f_name = (Path(INPUT_FILE).name)
    out_f_name = f"{inp_f_name}_змін_{t}.mp3"
 # Формуємо повну назву файлу   
    out_f_path = os.path.join(OUT_MP3_FOLDER, out_f_name)   
         
    try:
        tts = gTTS(text=content, lang="uk")
        tts.save(out_f_path)
        Popup(title="MP3 збережено", content=Label(text=f"MP3 збережено:\n{OUT_MP3_FOLDER}\n {out_f_name}"),
              size_hint=(0.9,0.35)).open()
    except Exception as e:
        Popup(title="Помилка gTTS", content=Label(text=str(e)), size_hint=(0.9,0.45)).open()

# Прив'язка функцій до класу
AccentApp.save_full_text = save_full_text
AccentApp.save_full_mp3 = save_full_mp3


# ----------------- Запуск додатку -----------------
if __name__ == "__main__":
    AccentApp().run()
