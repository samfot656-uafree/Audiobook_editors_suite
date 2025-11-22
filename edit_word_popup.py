# -*- coding: utf-8 -*-
"""
Попап для редагування слова, вставки наголосу та збереження.

Встановлює колір поля редагування слова залежно від заряду батареї. Кольори кнопок відповідно до День-ніч.

список кнопок залежить від self.editor_name
"""
import sys
import os
from pathlib import Path


from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock

# Додаємо шляхи для імпортів
sys.path.insert(0, '/storage/emulated/0/a0_sb2_book_editors_suite')
sys.path.insert(0, '/storage/emulated/0/a0_sb2_book_editors_suite/book_editors_suite')


# Project imports
from book_editors_suite.core.base_editor import BaseEditor
from book_editors_suite.core.config_manager import get_config_manager
from book_editors_suite.core.tts_manager import TTSManager
from book_editors_suite.core.file_manager import FileManager
from book_editors_suite.core.text_processor import TextProcessor
from book_editors_suite.core.logging_manager import LoggingManager
#from book_editors_suite.ui.popups.edit_word_popup import EditWordPopup
from book_editors_suite.ui.popups.extra_buttons_popup import ExtraButtonsPopup
from book_editors_suite.ui.themes import ThemeManager
from book_editors_suite.utils.helpers import WORD_RE


class EditWordPopup(Popup):
    """Попап для редагування слова, вставки наголосу та збереження"""

#-------------------------------------------    
    def __init__(self, parent_app, original_word, editor_name, **kwargs):
        super().__init__(**kwargs)
        self.parent_app = parent_app
        self.editor_name = editor_name
        self.config = parent_app.config
        self.accent_char = '\u0301'
        self.original_word = original_word
        
# для налагодження
#        self.editor_name = 'accent_editor'
#        self.editor_name = 'voice_tags_editor'
#        self.editor_name = 'sound_effects_editor'
#        self.title = f"{self.editor_name} \nРедагування: {original_word}"

        self.title = f"Редагування: {original_word}"
        self.size_hint = (0.98, 0.88)

        # Отримуємо налаштування з конфігурації
        try:
            # Для всіх редакторів тепер використовуємо base_editor
            config_data = self.parent_app.base_editor.config_manager.data
            bbtn_font_size = config_data.get('BBTN_FONT_SIZE', 42)
            text_widget_font_size=config_data.get('TEXT_WIDGET_FONT_SIZE', 66)
            bbtn_height = config_data.get('BBTN_HEIGHT', 150)
        except AttributeError:
            # Резервні значення
            bbtn_font_size = 56
            text_widget_font_size= 56
            bbtn_height = 150
 
        root = BoxLayout(orientation='vertical', spacing=8, padding=8)
        
        # Рядок кнопок
        btn_row = BoxLayout(size_hint_y=None, height=bbtn_height, spacing=8)
        self.btn_listen = Button(text="Слухати", font_size=bbtn_font_size)
        self.btn_insert = Button(text="Наголос", font_size=bbtn_font_size)
        self.btn_save_both = Button(text="Сл+текст", font_size=bbtn_font_size)
        self.btn_save_text = Button(text="У текст", font_size=bbtn_font_size)
        self.btn_cancel = Button(text="Назад", font_size=bbtn_font_size)
  
        # список кнопок залежить від self.editor_name      
        if self.editor_name == 'accent_editor':
            for b in (self.btn_listen, self.btn_insert, self.btn_save_both, self.btn_save_text, self.btn_cancel):
            	btn_row.add_widget(b)
        
        elif self.editor_name == 'voice_tags_editor' or self.editor_name == 'sound_effects_editor':
            for b in (self.btn_listen, self.btn_insert, self.btn_save_text, self.btn_cancel):
            	btn_row.add_widget(b)            	
            	
        root.add_widget(btn_row)

        # Поле редагування
        self.edit_input = TextInput(text=original_word, font_size=text_widget_font_size+20, multiline=False)
        root.add_widget(self.edit_input)

        # Рядок з інформацією (годинник та батарея)
        info_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=80, spacing=12)
        self.clock_label = Label(text=f"Час: {self._get_clock_str()}", font_size=bbtn_font_size, halign='left', valign='middle')
        self.clock_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        
        batt = self._get_battery_percent()
        batt_txt = f"{batt}%" if batt >= 0 else "—"
        self.batt_label = Label(text=f"Заряд: {batt_txt}", font_size=bbtn_font_size, halign='right', valign='middle')
        self.batt_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        
        info_row.add_widget(self.clock_label)
        info_row.add_widget(self.batt_label)
        root.add_widget(info_row)

        # Прив'язка функцій кнопок
        self.btn_listen.bind(on_press=self.on_listen_word)
        self.btn_insert.bind(on_press=self.on_insert_accent)
        if self.editor_name == 'accent_editor':
        	self.btn_save_both.bind(on_press=self.on_save_dict_and_text)
        self.btn_save_text.bind(on_press=self.on_save_text_only)
        self.btn_cancel.bind(on_press=lambda *_: self.dismiss())

        self.content = root
        Clock.schedule_once(lambda *_: self.apply_theme_from_app(), 0)

#-------------------------------------------        
    def _get_clock_str(self):
        """Повертає поточний час у форматі HH:MM."""
        from datetime import datetime
        return datetime.now().strftime("%H:%M")

#-------------------------------------------    
    def _get_battery_percent(self):
        """Повертає відсоток заряду батареї або -1 якщо не доступно."""
        try:
            from jnius import autoclass
            BatteryManager = autoclass('android.os.BatteryManager')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            
            context = PythonActivity.mActivity
            battery_manager = context.getSystemService(context.BATTERY_SERVICE)
            battery_level = battery_manager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
            return battery_level
        except Exception:
            return -1

#-------------------------------------------
    def apply_theme_from_app(self):
        """Встановлює колір поля редагування слова залежно від заряду батареї. Кольори кнопок відповідно до День-ніч"""
        batt = self._get_battery_percent()
        colors = self.parent_app.get_theme_colors()
        
        if batt >= 0:
        	self.edit_input.cursor_color = colors["cursor_bat_color"]
        #	self.edit_input.cursor_color = (0.03, 0.85, 0.53, 1)
        	
        	if batt < 25:
        	       self.edit_input.background_color = colors["batt_25"]
        	       self.edit_input.cursor_color = colors["cursor_bat_color"]
        	       self.batt_label.color = colors["batt_25"]
        	
        	elif batt < 30:
        	       self.edit_input.background_color = colors["batt_30"]
        	       self.edit_input.cursor_color = colors["cursor_bat_color"]
        	       self.batt_label.color = colors["batt_30"]
        	
        	else:
        	       self.edit_input.background_color = colors["input_bg"]
        	       self.edit_input.foreground_color = colors["input_fg"]
        	       self.edit_input.cursor_color = colors["cursor_color"]
        	       self.batt_label.color = colors["cursor_bat_color"]
      
        # Застосування кольорів до кнопок та міток
        self.batt_label.background_color = colors["button_bg"]
        for widget in (self.btn_listen, self.btn_insert, self.btn_save_both, 
                      self.btn_save_text, self.btn_cancel, self.clock_label):
            if hasattr(widget, 'background_normal'):
                widget.background_normal = ""
                widget.background_color = colors["button_bg"]
                widget.color = colors["button_fg"]
            else:
                # Для Label встановлюємо тільки колір тексту
                widget.color = colors["button_fg"]
        
        try:
            self.edit_input.cursor_color = colors["cursor_bat_color"]
         #   self.edit_input.cursor_color = (0.83, 0.85, 0.53, 1)
        except Exception:
            pass

#-------------------------------------------
    def on_insert_accent(self, *_):
        """Вставляє символ наголосу в поточну позицію курсора."""
        txt = self._strip_combining_acute(self.edit_input.text)
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

#-------------------------------------------
    def _strip_combining_acute(self, text: str) -> str:
        """Видаляє комбінуючі наголоси з тексту."""
        return text.replace('\u0301', '')

#-------------------------------------------
    def on_listen_word(self, *_):
        """Відтворює слово через TTS."""
        text = self.edit_input.text.strip()
        if text:
            self.parent_app.base_editor.tts_manager.safe_tts_speak(text)

#-------------------------------------------
    def on_save_dict_and_text(self, *_):
        """Зберігає слово в словник та замінює в тексті."""
        new_word = self.edit_input.text.strip()
        if not new_word:
            self.dismiss()
            return
        
        # Зберігаємо в словник нижнім регістром
        key = self._strip_combining_acute(self.original_word).lower()
        self.parent_app.accents[key] = new_word.lower()
        #success = self.base_editor.file_manager.save_accents(self.accents)
        self.parent_app.base_editor.file_manager.save_accents(self.parent_app.accents)
        
        # Додаємо в текст у поточному регістрі
        replaced = self._match_casing(self.original_word, new_word)
        self.parent_app.replace_word_in_current_paragraph(self.original_word, replaced)
        
        self.parent_app.base_editor.logger.info(f"💾 Збережено в словник та текст: '{self.original_word}' -> '{replaced}'")
        self.dismiss()

#-------------------------------------------
    def on_save_text_only(self, *_):
        """Зберігає слово тільки в тексті (без словника)."""
        new_word = self.edit_input.text.strip()
        if not new_word:
            self.dismiss()
            return
        
        replaced = self._match_casing(self.original_word, new_word)
        self.parent_app.replace_word_in_current_paragraph(self.original_word, replaced)
        
        self.parent_app.base_editor.logger.info(f"💾 Збережено тільки в текст: '{self.original_word}' -> '{replaced}'")
        self.dismiss()

#-------------------------------------------
    def _match_casing(self, original: str, new_word: str) -> str:
        """Відповідає регістру оригінального слова."""
        if not original or not new_word:
            return new_word
            
        if original.isupper():
            return new_word.upper()
        elif original[0].isupper():
            return new_word[0].upper() + new_word[1:].lower()
        else:
            return new_word.lower()
 #-------------------------------------------           