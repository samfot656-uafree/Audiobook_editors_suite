# -*- coding: utf-8 -*-
"""
Функції, що присутні в коді:
1. open_file_async() — асинхронне відкриття великих файлів (потік).
2. save_file() — ручне збереження з повідомленням (Popup) + збереження закладки (cursor та scroll_y) у config.json.
3. add_voice_tag(tag) — вставлення тегу в позицію курсора з урахуванням режиму швидкості.
4. listen_tagged_fragment() — відтворює текст між тегами #g1:…#g9: з урахуванням швидкості (slow/fast/normal).
5. init_tts() / init_tts_wrapper() / safe_tts_speak(text, speed_tag) / stop_tts() — робота з Android TTS (безпечні виклики).
6. set_speed_mode(spinner, value) — встановлення режиму швидкості (через Spinner).
7. switch_theme() / get_theme_colors() / apply_theme() / toggle_theme() — перемикач день/ніч.
8. build() — створення інтерфейсу Kivy.
9. open_and_prepare_text() — (імпліцитно) завантаження тексту з config input file (синхронно/асинхронно через open_file_async).
10. detect_word_at_cursor() — знаходження слова під курсором.
11. replace_word_in_current_paragraph(old_word, new_word) — заміна слова в тексті (коректна робота з позицією курсора).
12. utility: match_casing, get_clock_str, get_battery_percent, ConfigManager (load/ensure_folder/sanitize_name, save_bookmark, reset_bookmark).
13. _set_cursor_by_index(idx) — допоміжний метод для встановлення курсору.
14. reset_bookmark() — скидання закладки в конфіг (встановлює відкриття з початку).

Відсутні / плановані (необхідні) функції, які можуть бути додані:
1. Undo/redo — відсутні (свідомо).
2. Підсвічування синтаксису — відсутнє.
3. Автозбереження — відсутнє (свідомо).
4. Більш повна інтеграція помилок/логів (можна додати logging handlers).
5. Механізм інтерфейсу вибору файлу (файловий діалог) — залежить від середовища (Pydroid3 / Android).
"""

import os
import re
import json
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.spinner import Spinner

# Android imports (optional)
try:
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
    Locale = autoclass('java.util.Locale')
    HashMap = autoclass('java.util.HashMap')
    Context = autoclass('android.content.Context')
    BatteryManager = autoclass('android.os.BatteryManager')
    IntentFilter = autoclass('android.content.IntentFilter')
    Intent = autoclass('android.content.Intent')
except Exception:
    PythonActivity = TextToSpeech = Locale = HashMap = Context = BatteryManager = IntentFilter = Intent = None

# Constants
WORD_RE = re.compile(r"(?:[^\W\d_](?:\u0301)?)+(?:'(?:[^\W\d_](?:\u0301)?)+)*", flags=re.UNICODE)
TAG_OPEN_RE = re.compile(r"#g\d+(?:_(slow|fast))?: ?", flags=re.IGNORECASE)


# ==========================
class ConfigManager:
    """Клас для завантаження і зберігання параметрів конфігурації."""
    def __init__(self, config_file: str):
        self.config_file = Path(config_file)
        self.config_data: Optional[Dict] = None

        # дефолти
        self.config_version = "0_0_0_1"
        self.input_text_file: Path = Path("")
        self.output_folder: Path = Path("")
        self.voice_dict: Dict[str, str] = {}
        self.bbtn_font_size = 38
        self.bbtn_height = 120

        self.TEMP_FOLDER_NAME = "temp_multispeakers"

        # project paths
        self.project_root: Optional[Path] = None
        self.temp_folder: Optional[Path] = None

        # runtime
        self.current_block_text: List[str] = []
        self.current_voice_tag: str = 'g1'

        # bookmark structure: {"cursor": int, "scroll": float}
        self.bookmark = {"cursor": 0, "scroll": 1.0}
                    
        #позиція тексту
        self.tags_editor_scroll_y = 0.0
#        cfg.get("TAGS_EDITOR_SCROLL_Y", 10.0)
        self.tags_editor_cursor  = 0
    #    cfg.get("TAGS_EDITOR_CURSOR_POS", 0)

  

    # ----------------------------------------------------
    def load(self):
        """Завантажує конфіг та встановлює атрибути."""
        if not self.config_file.exists():
            # Якщо конфіг не існує — створимо базовий шаблон (щоб можна було записувати закладку)
            self.config_data = {}
            self.config_data["CONFIG_VERSION"] = self.config_version
            
            self.config_data["INPUT_TEXT_FILE"] = str(self.input_text_file)
            self.config_data["OUTPUT_FOLDER"] = str(self.output_folder)
            self.config_data["voice_dict"] = self.voice_dict
            # Не створюємо файл автоматично тут на випадок, якщо користувач хоче підставити інший шлях
            return self

        try:
            with open(self.config_file, encoding='utf-8') as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}

        self.config_data = cfg

        # основні шляхи та словники
        self.config_version = cfg.get("CONFIG_VERSION", self.config_version)


        self.input_text_file = Path(cfg.get("INPUT_TEXT_FILE", "")) if cfg.get("INPUT_TEXT_FILE") else Path("")
        self.output_folder = Path(cfg.get("OUTPUT_FOLDER", "")) if cfg.get("OUTPUT_FOLDER") else Path("")
        self.voice_dict = cfg.get("voice_dict", {}) or {}
                
     #   #позиція тексту
        self.tags_editor_scroll_y = cfg.get("TAGS_EDITOR_SCROLL_Y", 0.0)
        self.tags_editor_cursor  = cfg.get("TAGS_EDITOR_CURSOR_POS", 0)


        # bookmark
        bk = cfg.get("RTG_BOOKMARK", None)
        if isinstance(bk, dict):
            # очікуємо keys "cursor" (int) і "scroll" (float)
            try:
                c = int(bk.get("cursor", 0))
                s = float(bk.get("scroll", 1.0))
                self.bookmark = {"cursor": max(0, c), "scroll": max(0.0, min(1.0, s))}
            except Exception:
                self.bookmark = {"cursor": 0, "scroll": 1.0}
        else:
            # за замовчуванням — відкривати з початку (cursor 0)
            self.bookmark = {"cursor": 0, "scroll": 1.0}

        # встановлюємо project_root якщо це явно зазначено або беремо батьківську папку config
        self.project_root = Path(cfg.get("PROJECT_ROOT", self.config_file.parent))

        return self  # дає змогу писати: config = ConfigManager(...).load()

    # ---------- utility methods ----------
    def ensure_folder(self, path: Path):
        path.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------
    def sanitize_name(self, s: str, for_filename: bool = True) -> str:
        s2 = re.sub(r"^##\s* ", "", s)
        s2 = re.sub(r"#g\d+: ? ", "", s2)
        s2 = s2.strip()
        if for_filename:
            s2 = re.sub(r"[^\w\d_-]", "_", s2)
            if not s2:
                s2 = "Глава"
        return s2
#========= Закладка ========
    # ----------------------------------------------------
    def save_bookmark(self, cursor_idx: int, scroll_y: float):
        """Зберігає позицію курсора і прокрутки в конфіг (по ключу BOOKMARK)."""
        # намагаємося зчитати існуючий конфіг (щоб не перезаписати інші поля)
        cfg = {}
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f) or {}
            except Exception:
                cfg = {}
        # оновлюємо/вставляємо BOOKMARK
        cfg["RTG_BOOKMARK"] = {"cursor": int(max(0, cursor_idx)), "scroll": float(scroll_y)}

        cfg["TAGS_EDITOR_CURSOR_POS"] = int(max(0, cursor_idx)
        cfg["TAGS_EDITOR_SCROLL_Y"] =  float(scroll_y) 
               
        try:
            # переконаємося, що папка існує
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            # оновлюємо runtime-поле
            self.bookmark = {"cursor": int(max(0, cursor_idx)), "scroll": float(scroll_y)}

            self.tags_editor_cursor  =int(max(0, cursor_idx)
            self.tags_editor_scroll_y = float(scroll_y)
           
            
        except Exception:
            # не критично, але не падаємо
            pass

    # ----------------------------------------------------
    def reset_bookmark(self):
        """Скидає закладку (встановлює відкриття з початку)."""
        # зчитуємо існуючий конфіг
        cfg = {}
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f) or {}
            except Exception:
                cfg = {}
        cfg["RTG_BOOKMARK"] = {"cursor": 0, "scroll": 1.0}
        
        cfg["TAGS_EDITOR_CURSOR_POS"] = "TAGS_EDITOR_SCROLL_Y": 0.0
        cfg["TAGS_EDITOR_SCROLL_Y"] =  "TAGS_EDITOR_CURSOR_POS", 0

        
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            self.bookmark = {"cursor": 0, "scroll": 1.0}
            self.tags_editor_scroll_y = 0.0
            self.tags_editor_cursor  =  0

            
        except Exception:
            pass

#=========end Закладка ========
# ---------------- utility functions ----------------

# ----------------------------------------------------
def match_casing(original: str, replacement: str) -> str:
    """
    Підбирає регістр replacement під оригінал:
    - ВСІ великі -> усе велике
    - Перша буква велика -> лише перша велика
    """
    if not original:
        return replacement
    if original.isupper():
        return replacement.upper()
    if original[0].isupper():
        return replacement.capitalize()
    return replacement.lower()


# ----------------------------------------------------
def get_clock_str() -> str:
    """Поточний час ГГ:ХХ"""
    try:
        return datetime.now().strftime("%H:%M")
    except Exception:
        return "--:--"

# ----------------------------------------------------
def get_battery_percent() -> int:
    """
    Повертає заряд батареї у %.
    Якщо Android API доступне, використовує BatteryManager, інакше повертає -1.
    """
    try:
        if BatteryManager and PythonActivity:
            ctx = PythonActivity.mActivity.getSystemService(Context.BATTERY_SERVICE)
            if ctx:
                val = ctx.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
                return int(val)
    except Exception:
        pass
    return -1


# ----------------- Popup редагування слова ----------------
class EditWordPopup(Popup):
    """Вікно редагування слова."""

    def __init__(self, main_app, original_word: str, **kwargs):
        super().__init__(**kwargs)
        self.main_app = main_app
        self.config = main_app.config_manager
        self.original_word = original_word
        self.accent_char = '\u0301'
        self.title = f"Редагування: {original_word}"
        self.size_hint = (0.98, 0.88)
        Window.softinput_mode = "below_target"

        # параметри від config_manager
        self.bbtn_font_size = getattr(self.config, "bbtn_font_size", 40)
        self.bbtn_height = getattr(self.config, "bbtn_height", 120)


        root = BoxLayout(orientation='vertical', spacing=8, padding=22)
        btn_row = BoxLayout(size_hint_y=None, height=self.bbtn_height, spacing=8)
        self.btn_listen = Button(text="Слухати", font_size=self.bbtn_font_size)
        self.btn_insert = Button(text="Наголос", font_size=self.bbtn_font_size)
        self.btn_save_text = Button(text="В текст", font_size=self.bbtn_font_size)
        self.btn_cancel = Button(text="Назад", font_size=self.bbtn_font_size)
        for b in (self.btn_listen, self.btn_insert, self.btn_save_text, self.btn_cancel):
            btn_row.add_widget(b)

        root.add_widget(btn_row)

        self.edit_input = TextInput(text=original_word, font_size=100, multiline=False)
        root.add_widget(self.edit_input)

        info_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=self.bbtn_height, spacing=12)
        self.clock_label = Label(text=f"Час: {get_clock_str()}", font_size=self.bbtn_font_size)
        batt = get_battery_percent()
        batt_txt = f"{batt}%" if batt >= 0 else "—"
        self.batt_label = Label(text=f"Заряд: {batt_txt}", font_size=self.bbtn_font_size)
        info_row.add_widget(self.clock_label)
        info_row.add_widget(self.batt_label)
        root.add_widget(info_row)

        self.btn_listen.bind(on_press=self.on_listen_word)
        self.btn_insert.bind(on_press=self.on_insert_accent)
        self.btn_save_text.bind(on_press=self.on_save_text_only)
        self.btn_cancel.bind(on_press=lambda *_: self.dismiss())

        self.content = root
        # встановлюємо колір input залежно від батареї
        self.update_input_bg_color()

    # ----------------------------------------------------
    def on_insert_accent(self, *_):
        txt = self.strip_combining_acute(self.edit_input.text)
        try:
            pos = self.edit_input.cursor_index()
        except Exception:
            pos = len(txt)
        new = txt[:pos] + self.accent_char + txt[pos:]
        self.edit_input.text = new
        try:
            self.edit_input.cursor = self.edit_input.get_cursor_from_index(pos + 1)
        except Exception:
            pass

    # ----------------------------------------------------
    def strip_combining_acute(self, s: str) -> str:
        """Видаляє комбінований наголос"""
        if not s:
            return s
        return s.replace('\u0301', '')

    # ----------------------------------------------------
    def on_save_text_only(self, *_):
        new_word = self.edit_input.text.strip()
        if not new_word:
            self.dismiss()
            return
        replaced = match_casing(self.original_word, new_word)
        self.main_app.replace_word_in_current_paragraph(self.original_word, replaced)
        self.dismiss()

    # ----------------------------------------------------
    def on_listen_word(self, *_):
        # просте відтворення слова — можна зв'язати з TTS
        try:
            self.main_app.safe_tts_speak(self.edit_input.text, "normal")
        except Exception:
            pass
       
# ----------------------------------------------------
    def update_input_bg_color(self, *_):
        """Встановлює колір поля редагування слова залежно від заряду батареї. Кнопок відповідно до День-ніч"""
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
        
        
        for b in (self.btn_listen, self.btn_insert, self.btn_save_text, self.btn_cancel, self.batt_label, self.clock_label):
                b.background_normal = ""
                b.background_color = colors["button_bg"]
                b.color = colors["button_fg"]
            
                try:
                    self.edit_input.cursor_color = (0.03, 0.85, 0.53 ,1)
                except Exception:
                    pass


# ----------------- Popup додаткових кнопок -----------------
class ExtraButtonsPopup(Popup):
    """Вікно додаткових кнопок."""

    def __init__(self, main_app, **kwargs):
        super().__init__(**kwargs)
        self.main_app = main_app
        self.config = main_app.config_manager
        self.title = "Додаткові кнопки"
        self.size_hint = (0.95, 0.5)
        Window.softinput_mode = "below_target"

        self.bbtn_font_size = getattr(self.config, "bbtn_font_size", 40)
        self.bbtn_height = getattr(self.config, "bbtn_height", 120)

        root = BoxLayout(orientation='vertical', spacing=8, padding=22)
        btn_row = BoxLayout(size_hint_y=None, height=self.bbtn_height, spacing=8)
        self.btn_open = Button(text="Відкрити", font_size=self.bbtn_font_size)
        self.btn_open.bind(on_press=lambda *_: (self.open_file_async(), self.dismiss()))
        self.btn_save_txt = Button(text="До txt", font_size=self.bbtn_font_size)
        self.btn_theme = Button(text="День-ніч", font_size=self.bbtn_font_size)
        self.btn_reset_bm = Button(text="Закладку 0", font_size=self.bbtn_font_size)
        self.btn_back = Button(text="Назад", font_size=self.bbtn_font_size)
        for b in (self.btn_open, self.btn_save_txt, self.btn_theme, self.btn_reset_bm, self.btn_back):
            btn_row.add_widget(b)
        root.add_widget(btn_row)
        root.add_widget(Label())
        self.content = root

        self.btn_save_txt.bind(on_press=lambda *_: (self.main_app.save_file(), self.dismiss()))
        self.btn_theme.bind(on_press=lambda *_: (self.main_app.toggle_theme(), self.dismiss()))
        self.btn_reset_bm.bind(on_press=lambda *_: (self._on_reset_bm(), self.dismiss()))
        self.btn_back.bind(on_press=lambda *_: self.dismiss())

        
        
        Clock.schedule_once(lambda *_: self.apply_theme_from_app(), 0)

    def apply_theme_from_app(self):
        colors = self.main_app.get_theme_colors()
        for b in (self.btn_open, self.btn_save_txt, self.btn_theme, self.btn_reset_bm, self.btn_back):
            b.background_normal = ""
            b.background_color = colors["button_bg"]
            b.color = colors["button_fg"]


    # ----------------------------------------------------
    def open_file_async(self):
        self.main_app.open_file_async()

    # ----------------------------------------------------
    def _on_reset_bm(self):
        self.main_app.reset_bookmark()


# ========================
class VoiceTagEditor(App):
    """Основний клас застосунку — оптимізований та виправлений."""

    def __init__(self, config_file="config_json", **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ConfigManager(config_file).load()
        # UI та стан
        self.text_widget: Optional[TextInput] = None
        self.current_speed = "normal"
        self.theme_mode = "day"
        self.status_label = None
        self.tts = None

        # стан додатку
        self.fixed_text = []
        self.current_idx = -1
        self.accent_char = '\u0301'

        # виділене слово та контексти
        self.text_before_selected_word = ""
        self.selected_word = None
        self.text_after_selected_word = ""

        # UI-параметри будуть ініціалізовані в build()
        self.bbtn_font_size = getattr(self.config_manager, "bbtn_font_size", 38)
        self.bbtn_height = getattr(self.config_manager, "bbtn_height", 120)
        self.voice_buttons: List[Button] = []
        self.current_file = self.config_manager.input_text_file

    # ----------------- Асинхронне відкриття -----------------
    def open_file_async(self, *args):
        def load_file(path):
            try:
                # читаємо потоково, але зберігаємо повністю у пам'ять (можна змінити на chunked display)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                Clock.schedule_once(lambda dt: self.set_text(content), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: Popup(title="Помилка", content=Label(text=str(e)), size_hint=(0.9, 0.35)).open(), 0)

        if not self.current_file or not Path(self.current_file).exists():
            Popup(title="Помилка", content=Label(text="Файл не вказаний або не існує"), size_hint=(0.9, 0.35)).open()
            return
        t = threading.Thread(target=load_file, args=(self.current_file,), daemon=True)
        t.start()

    # ----------------------------------------------------
    def set_text(self, text):
        if self.text_widget:
            # зберігаємо зміст
            self.text_widget.text = text

            # відновлюємо позицію прокрутки і курсору, якщо в конфі є закладка (cursor > 0)
            bk = getattr(self.config_manager, "bookmark", {"cursor": 0, "scroll": 1.0})
            cursor_pos = int(bk.get("cursor", 0))
            scroll_pos = float(bk.get("scroll", 1.0))
            # Якщо курсор = 0 — відкривати з початку. Інакше відновлюємо.
            if cursor_pos > 0:
                # трошки почекаємо, щоб відобразилися всі властивості віджета
                Clock.schedule_once(lambda dt: self._set_cursor_and_scroll(cursor_pos, scroll_pos), 0.08)
            else:
                # гарантуємо що прокрутка встановлена на початок/верх (scroll=1.0 — верх)
                Clock.schedule_once(lambda dt: self._set_cursor_and_scroll(0, 1.0), 0.05)

    # ----------------- Збереження -----------------

    def save_file(self, *args):
        if not self.current_file:
            Popup(title="Помилка", content=Label(text="Файл не вказаний"), size_hint=(0.9, 0.35)).open()
            return
        try:
            if not self.text_widget or self.text_widget.text == "":
                Popup(title="Помилка", content=Label(text="Текстове поле порожнє"), size_hint=(0.9, 0.35)).open()
                return

            # Записуємо текст у файл
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(self.text_widget.text if self.text_widget else "")

            # Зберігаємо закладку: cursor index і scroll_y
            try:
                cursor_idx = self.text_widget.cursor_index()
            except Exception:
                cursor_idx = 0
            try:
                scroll_y = float(getattr(self.text_widget, "scroll_y", 1.0))
            except Exception:
                scroll_y = 1.0

            # Збереження в config.json
            self.config_manager.save_bookmark(int(cursor_idx), float(scroll_y))

            popap_text = f"Файл збережено:\n{self.current_file}"
            Popup(title="Збережено", content=Label(text=popap_text), size_hint=(0.9, 0.35)).open()
        except Exception as e:
            Popup(title="Помилка збереження", content=Label(text=str(e)), size_hint=(0.9, 0.35)).open()

    # ----------------- Додавання тегів -----------------

    def add_voice_tag(self, tag):
        speed = self.current_speed
        if speed.lower() == "normal":
            full_tag = f"\n#{tag}: "
        else:
            full_tag = f"\n#{tag}_{speed.lower()}: "
        ti = self.text_widget
        if not ti:
            return
        try:
            cursor = ti.cursor_index()
        except Exception:
            cursor = len(ti.text)
        ti.text = ti.text[:cursor] + full_tag + ti.text[cursor:]
        # перемістити курсор після вставленого тексту
        Clock.schedule_once(lambda dt: self._set_cursor_by_index(cursor + len(full_tag)), 0)

    # ----------------------------------------------------
    def _set_cursor_by_index(self, idx: int):
        if not self.text_widget:
            return
        try:
            self.text_widget.cursor = self.text_widget.get_cursor_from_index(idx)
        except Exception:
            try:
                # fallback: якщо get_cursor_from_index недоступний
                self.text_widget.cursor_index = idx
            except Exception:
                pass

    def _set_cursor_and_scroll(self, cursor_idx: int, scroll_y: float):
        """Встановлює курсор і прокрутку (scroll_y)."""
        if not self.text_widget:
            return
        try:
            # курсор
            self._set_cursor_by_index(int(cursor_idx))
        except Exception:
            pass
        try:
            # scroll_y: TextInput використовує значення від 0..1 (1 - top)
            # деякі версії можуть вимагати schedule
            self.text_widget.scroll_y = float(scroll_y)
        except Exception:
            pass

    # ----------------- Прослуховування фрагмента -----------------
    def listen_tagged_fragment(self, *args):
        if not self.tts:
            self.tts = self.init_tts()
        try:
            idx = self.text_widget.cursor_index()
        except Exception:
            idx = 0
        text = self.text_widget.text or ""
        # знаходимо всі відкриваючі теги
        opens = list(TAG_OPEN_RE.finditer(text))

        start_pos, start_speed = 0, "normal"
        for m in opens:
            if m.start() <= idx:
                start_pos = m.end()
                grp = m.group(1)
                start_speed = grp if grp else "normal"
            else:
                break

        end_pos = len(text)
        for m in opens:
            if m.start() > idx:
                end_pos = m.start()
                break

        fragment = text[start_pos:end_pos].strip()
        if fragment:
            self.safe_tts_speak(fragment, start_speed)
        else:
            self.show_status("Текст між тегами не знайдено")

    # ----------------- TTS -----------------
    def init_tts(self):
        if not TextToSpeech or not PythonActivity:
            return None
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
        except Exception:
            return None

    # ----------------------------------------------------
    def init_tts_wrapper(self):
        self.tts = self.init_tts()

    # ----------------------------------------------------
    def safe_tts_speak(self, text: str, speed_tag: str = "normal"):
        """Уніфікований метод для озвучення з налаштуванням швидкості."""
        if not text or not self.tts:
            return
        try:
            params = HashMap() if HashMap else None
            if params:
                params.put("volume", "1.0")
            # Визначення швидкості
            st = (speed_tag or "normal").lower()
            try:
                if st == "slow":
                    self.tts.setSpeechRate(0.8)
                elif st == "fast":
                    self.tts.setSpeechRate(1.2)
                else:
                    self.tts.setSpeechRate(1.0)
            except Exception:
                pass
            if params:
                self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, params)
            else:
                # fallback: some TTS bindings accept None for params
                self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None)
        except Exception:
            # не критично для UX, лог можна додати
            pass

    # ----------------------------------------------------
    def stop_tts(self, *args):
        if self.tts:
            try:
                self.tts.stop()
            except Exception:
                pass

    # ----------------- Режим швидкості -----------------
    def set_speed_mode(self, spinner, value):
        # Spinner дає текст із великої літери, зберігаємо як Normal/Slow/Fast
        self.current_speed = value

    # ----------------- Інтерфейс -----------------
    def build(self):
        colors = self.get_theme_colors()
        Window.softinput_mode = "below_target"
        cfg = self.config_manager

        # кеш параметрів
        self.bbtn_font_size = cfg.bbtn_font_size
        self.bbtn_height = cfg.bbtn_height
        self.current_file = cfg.input_text_file

        layout = BoxLayout(orientation="vertical", spacing=5, padding=22)

        # Верхня панель кнопок
        top_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=self.bbtn_height, spacing=8)

        self.speed_spinner = Spinner(
            text="normal",
            values=("slow", "normal", "fast"),
            font_size=self.bbtn_font_size,
            size_hint_x=None, width=self.bbtn_height,
        )
        self.speed_spinner.bind(text=self.set_speed_mode)

        self.btn_listen = Button(text="Слухати", font_size=self.bbtn_font_size)
        self.btn_listen.bind(on_press=self.listen_tagged_fragment)

        self.btn_pause = Button(text="Пауза", font_size=self.bbtn_font_size)
        self.btn_edit = Button(text="Правити", font_size=self.bbtn_font_size, disabled=True)
        self.btn_extra = Button(text=". . .", font_size=self.bbtn_font_size)

        for b in (self.speed_spinner, self.btn_listen, self.btn_pause, self.btn_edit, self.btn_extra):
            top_row.add_widget(b)

        # Панель голосів
        gvoices = list(cfg.voice_dict.keys())
        rows = max(1, (len(gvoices) + 2) // 3)
        self.voice_grid = GridLayout(cols=3, size_hint_y=None, height=rows * self.bbtn_height, spacing=8)
        self.voice_buttons = []

        def make_voice_button(tag):
            display = f"{cfg.voice_dict.get(tag, '')} {tag}"
            b = Button(text=display, font_size=self.bbtn_font_size)
            b.bind(on_release=lambda inst, t=tag: self.add_voice_tag(t))
            return b

        if gvoices:
            for tag in gvoices:
                b = make_voice_button(tag)
                self.voice_grid.add_widget(b)
                self.voice_buttons.append(b)
        else:
            self.voice_grid.add_widget(Label(text="Голосів немає", font_size=self.bbtn_font_size))

        # Текстове поле
        self.text_widget = TextInput(
            text="", multiline=True,
            font_size=58
        )
        # застосуємо кольори
        self.apply_theme_to_widgets(colors)
        self.text_widget.bind(on_touch_down=self.on_text_touch)

        layout.add_widget(top_row)
        layout.add_widget(self.voice_grid)
        layout.add_widget(self.text_widget)

        # Прив'язки кнопок
        self.btn_pause.bind(on_press=lambda *_: self.stop_tts())
        self.btn_edit.bind(on_press=self.open_edit_popup)
        self.btn_extra.bind(on_press=lambda *_: ExtraButtonsPopup(self).open())

        # Ініціалізація TTS та тема
        Clock.schedule_once(lambda *_: self.init_tts_wrapper(), 0.1)
        Clock.schedule_once(lambda *_: self.apply_theme(), 0.0)

        return layout

    # ----------------------------------------------------
    def apply_theme_to_widgets(self, colors):
        # Викликається під час build() перед створенням self.text_widget (також викликається пізніше)
        # встановлюємо початкові кольори
        try:
            self.text_widget.background_color = colors["input_bg"]
            self.text_widget.foreground_color = colors["input_fg"]
        except Exception:
            pass

    # ---------------- Тема день/ніч -----------------
    def get_theme_colors(self):
        if self.theme_mode == "day":
            return dict(button_bg=(0.5, 0.5, 0.5, 1), button_fg=(1, 1, 1, 1),
                        input_bg=(1, 1, 1, 1), input_fg=(0, 0, 0, 1))
        else:
            return dict(button_bg=(0, 0, 0, 1), button_fg=(0, 0.3, 0.5, 1),
                        input_bg=(0, 0, 0, 1), input_fg=(0, 0, 0.7, 1))

    # ----------------------------------------------------
    def apply_theme(self):
        colors = self.get_theme_colors()
        # кнопки верхньої панелі
        widgets = []
        try:
            widgets = [self.speed_spinner, self.btn_listen, self.btn_pause, self.btn_edit, self.btn_extra]
        except Exception:
            widgets = []
        for b in widgets:
            try:
                b.background_normal = ""
                b.background_color = colors["button_bg"]
                b.color = colors["button_fg"]
            except Exception:
                pass
        # голосові кнопки
        for b in self.voice_buttons:
            try:
                b.background_normal = ""
                b.background_color = colors["button_bg"]
                b.color = colors["button_fg"]
            except Exception:
                pass
        # текстове поле
        if self.text_widget:
            try:
                self.text_widget.background_color = colors["input_bg"]
                self.text_widget.foreground_color = colors["input_fg"]
                self.text_widget.cursor_color = ((0.03, 0.85, 0.53 ,1))
            except Exception:
                pass
        # spinner окремо
        try:
            self.speed_spinner.background_color = colors['button_bg']
            self.speed_spinner.color = colors['button_fg']
        except Exception:
            pass
        try:
            Window.clearcolor = colors["input_bg"]
        except Exception:
            pass

    # ----------------------------------------------------
    def toggle_theme(self):
        self.theme_mode = "night" if self.theme_mode == "day" else "day"
        self.apply_theme()

    # ----------------- Текст / файл ---------------

    # ----------------- Виділення слова -----------
    def _is_letter(self, ch: str) -> bool:
        return bool(re.match(r"[^\W\d_]", ch, flags=re.UNICODE))

    # ----------------------------------------------------
    def detect_word_at_cursor(self):
        try:
            idx = self.text_widget.cursor_index()
        except Exception:
            idx = len(self.text_widget.text) if self.text_widget and self.text_widget.text else 0
        text = self.text_widget.text or ""
        start, end = idx, idx
        # рух ліворуч
        while start > 0 and (self._is_letter(text[start - 1]) or text[start - 1] == self.accent_char):
            start -= 1
        # рух праворуч
        while end < len(text) and (self._is_letter(text[end]) or text[end] == self.accent_char):
            end += 1
        word = text[start:end]
        if WORD_RE.fullmatch(word):
            self.text_before_selected_word = text[:start]
            self.text_after_selected_word = text[end:]
            self.selected_word = word
            try:
                self.btn_edit.disabled = False
            except Exception:
                pass
        else:
            self.selected_word = None
            try:
                self.btn_edit.disabled = True
            except Exception:
                pass

    # ----------------------------------------------------
    def on_text_touch(self, instance, touch):
        if not instance.collide_point(*touch.pos):
            return False
        # даємо час Kivy оновити позицію курсора
        Clock.schedule_once(lambda *_: self.detect_word_at_cursor(), 0.03)
        return False

    # ----------------------------------------------------
    def open_edit_popup(self, *_):
        if self.selected_word:
            self.stop_tts()
            EditWordPopup(self, self.selected_word).open()

    # ----------------- Заміна слова -----------------
    def replace_word_in_current_paragraph(self, old_word: str, new_word: str):
        """
        Замінює виділене слово, використовуючи збережені частини тексту.
        Старанно встановлює курсор після вставки.
        """
        if not self.text_widget:
            return
        # формуємо новий текст
        new_txt = self.text_before_selected_word + new_word + self.text_after_selected_word
        self.text_widget.text = new_txt
        # ставимо курсор після вставленого слова
        new_pos = len(self.text_before_selected_word) + len(new_word)
        Clock.schedule_once(lambda dt: self._set_cursor_by_index(new_pos), 0)

    # ----------------- UI / допоміжні -----------------
    def show_status(self, txt: str):
        # Просте повідомлення (можна розширити індикатором)
        try:
            Popup(title="Повідомлення", content=Label(text=txt), size_hint=(0.9, 0.35)).open()
        except Exception:
            pass

    # ----------------- Закладки -----------------
    def reset_bookmark(self):
        """Скидає закладку в конфіг — відкривати буде з початку."""
        try:
            self.config_manager.reset_bookmark()
            Popup(title="Закладка скинута", content=Label(text="Відкриття з початку титулу буде активне."), size_hint=(0.9, 0.35)).open()
        except Exception:
            pass


# ========================
if __name__ == "__main__":
    # замініть шлях на свій конфіг при запуску локально
    cfg_path = "/storage/emulated/0/Documents/Json/config_zakl.json"
    app = VoiceTagEditor(cfg_path)
    app.run()
