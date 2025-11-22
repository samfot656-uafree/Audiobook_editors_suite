# -*- coding: utf-8 -*-
"""
Voice Tags Editor - оновлена версія з використанням BaseEditor
Повністю виправлена та перевірена версія з детальним логуванням
"""
#Система тегів для  ML-моделі StyleTTS2 ukrainian. Можна замінити на потрібну

import sys
import os
from pathlib import Path

sys.path.insert(0, '/storage/emulated/0/a0_sb2_book_editors_suite')
sys.path.insert(0, '/storage/emulated/0/a0_sb2_book_editors_suite/book_editors_suite')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.clock import Clock
import threading
import re

from book_editors_suite.core.base_editor import BaseEditor
from book_editors_suite.ui.popups.edit_word_popup import EditWordPopup
from book_editors_suite.ui.popups.extra_buttons_popup import ExtraButtonsPopup


class VoiceTagsEditor(App):
    """Редактор тегів голосів з використанням BaseEditor"""

    def __init__(self, book_project_name: str, input_text_file: str = None, **kwargs):
        super().__init__(**kwargs)
        self.book_project_name = book_project_name
        self.input_text_file = input_text_file
        self.app_name = "voice_tags_editor"
        
        # Використовуємо BaseEditor
        self.base_editor = BaseEditor(book_project_name, input_text_file, self.app_name)
        self.base_editor.logger.info(f"Ініціалізація VoiceTagsEditor для проекту: {book_project_name}")
        
        # Дані з конфігу
        self.voice_dict = self.base_editor.config.get('VOICE_DICT', {})
        self.pause_dict = self.base_editor.config.get('PAUSE_DICT', {})
        self.base_editor.logger.info(f"Завантажено voice_dict: {len(self.voice_dict)} голосів, pause_dict: {len(self.pause_dict)} пауз")
        
        # Стан програми
        self.current_speed = "normal"
        self.selected_word = None
        self.text_before_selected_word = ""
        self.text_after_selected_word = ""
        
        # Віджети
        self.text_widget = None
        self.voice_buttons = []
        self.btn_edit = None
        
        # Відновлюємо закладку
        self.restore_bookmark()
        self.base_editor.logger.info("Ініціалізація VoiceTagsEditor завершена успішно")

    def build(self):
        """Побудова інтерфейсу"""
        self.base_editor.logger.info("Початок побудови інтерфейсу")
        Window.softinput_mode = "below_target"
        interface = self._build_interface()
        self.base_editor.logger.info("Інтерфейс успішно побудовано")
        return interface

    def _build_interface(self):
        """Побудова інтерфейсу"""
        self.base_editor.logger.info("Створення інтерфейсу Voice Tags Editor")
        
        # Отримуємо налаштування з конфігу
        bbtn_font_size = self.base_editor.config_manager.get_common_param('BBTN_FONT_SIZE', 38)
        text_widget_font_size = self.base_editor.config_manager.get_common_param('TEXT_WIDGET_FONT_SIZE', 56)
        bbtn_height = self.base_editor.config_manager.get_common_param('BBTN_HEIGHT', 150)
        
        self.base_editor.logger.info(f"Параметри інтерфейсу: font_size={bbtn_font_size}, text_size={text_widget_font_size}, height={bbtn_height}")
            
        layout = BoxLayout(orientation="vertical", spacing=5, padding=27)

        # Верхній ряд кнопок
        top_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=bbtn_height, spacing=8)
        self.speed_spinner = Spinner(
            text="normal", 
            values=("slow", "normal", "fast"), 
            font_size=bbtn_font_size, 
            size_hint_x=None, 
            width=bbtn_height
        )
        self.speed_spinner.bind(text=self.set_speed_mode)
        self.btn_listen = Button(text="Слухати", font_size=bbtn_font_size)
        self.btn_pause = Button(text="Пауза", font_size=bbtn_font_size)
        self.btn_edit = Button(text="Правити", font_size=bbtn_font_size, disabled=True)
        self.btn_extra = Button(text=". . .", font_size=bbtn_font_size)
        
        for b in (self.speed_spinner, self.btn_listen, self.btn_pause, self.btn_edit, self.btn_extra):
            top_row.add_widget(b)
        layout.add_widget(top_row)
        self.base_editor.logger.info("Створено верхній ряд кнопок")

        # Сітка кнопок голосів
        gvoices = list(self.voice_dict.keys())
        rows = max(1, (len(gvoices) + 2) // 3)
        self.voice_grid = GridLayout(cols=3, size_hint_y=None, height=rows * bbtn_height, spacing=8)
        self.voice_buttons = []
        
        for tag in gvoices:
            display = f"{self.voice_dict.get(tag, '')} {tag}"
            b = Button(text=display, font_size=bbtn_font_size)
            b.bind(on_release=lambda inst, t=tag: self.add_voice_tag(t))
            self.voice_grid.add_widget(b)
            self.voice_buttons.append(b)
        
        layout.add_widget(self.voice_grid)
        self.base_editor.logger.info(f"Створено сітку голосів: {len(gvoices)} кнопок, {rows} рядів")

        # Текстове поле
        self.text_widget = TextInput(text="", multiline=True, font_size=text_widget_font_size)
        self.text_widget.bind(on_touch_down=self.on_text_touch)
        layout.add_widget(self.text_widget)
        self.base_editor.logger.info("Створено текстове поле")

        # Прив'язка подій
        self.btn_listen.bind(on_press=self.listen_tagged_fragment)
        self.btn_pause.bind(on_press=lambda *_: self.stop_tts())
        self.btn_edit.bind(on_press=self.open_edit_popup)
        self.btn_extra.bind(on_press=lambda *_: ExtraButtonsPopup(main_app=self, editor_name=self.app_name).open())
        self.base_editor.logger.info("Прив'язано обробники подій")

        # Автоматичні дії
        Clock.schedule_once(lambda *_: self.apply_theme(), 0.0)
        Clock.schedule_once(lambda *_: self.open_file_async(), 0.1)
        self.base_editor.logger.info("Заплановано автоматичні дії")

        return layout

    def open_file_async(self, *args):
        """Асинхронне завантаження файлу"""
        self.base_editor.logger.info("Початок асинхронного завантаження файлу")
        
        def load_file():
            try:
                input_file = self.base_editor.config.get('INPUT_TEXT_FILE', '')
                self.base_editor.logger.info(f"Спроба завантажити файл: {input_file}")
                
                if not input_file or not Path(input_file).exists():
                    self.base_editor.logger.error(f"Файл не існує або не вказаний: {input_file}")
                    Clock.schedule_once(lambda dt: self.show_error_popup("Файл не вказаний або не існує"), 0)
                    return
                
                with open(input_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                self.base_editor.logger.info(f"Файл успішно завантажено: {len(content)} символів")
                Clock.schedule_once(lambda dt: self.set_text(content), 0)
                
            except Exception as e:
                self.base_editor.logger.error(f"Помилка завантаження файлу: {e}")
                Clock.schedule_once(lambda dt: self.show_error_popup(str(e)), 0)
        
        threading.Thread(target=load_file, daemon=True).start()

    def set_text(self, text):
        """Встановлення тексту та відновлення закладки"""
        self.base_editor.logger.info(f"Встановлення тексту: {len(text)} символів")
        if self.text_widget:
            self.text_widget.text = text
            self.open_bookmark()
            self.base_editor.logger.info("Текст успішно встановлено та закладку відновлено")

    def open_bookmark(self):
        """Відновлення позиції закладки"""
        try:
            self.base_editor.logger.info(f"Відновлення закладки: scroll_y={self.base_editor.current_scroll_y}, cursor_pos={self.base_editor.current_cursor_pos}")
            
            self.text_widget.scroll_y = float(self.base_editor.current_scroll_y)
            
            if self.base_editor.current_cursor_pos > 0:
                Clock.schedule_once(lambda dt: self._set_cursor_by_index(self.base_editor.current_cursor_pos), 0.08)
                self.base_editor.logger.info(f"Курсор встановлено на позицію: {self.base_editor.current_cursor_pos}")
            else:
                Clock.schedule_once(lambda dt: self._set_cursor_by_index(0), 0.05)
                self.base_editor.logger.info("Курсор встановлено на початок тексту")
                
        except Exception as e:
            self.base_editor.logger.error(f"Не вдалося відновити закладку: {e}")
            self.text_widget.scroll_y = 1.0
            self._set_cursor_by_index(0)
            self.base_editor.logger.info("Відновлення закладки за замовчуванням")

    def save_file(self):
        """Збереження файлу та закладки"""
        self.base_editor.logger.info("Початок збереження файлу")
        
        if not self.text_widget or not self.text_widget.text.strip():
            self.base_editor.logger.warning("Спроба зберегти порожній текст")
            self.show_error_popup("Текстове поле порожнє")
            return
        
        try:
            input_file = self.base_editor.config.get('INPUT_TEXT_FILE', '')
            if not input_file:
                self.base_editor.logger.error("Файл не вказаний у конфігурації")
                self.show_error_popup("Файл не вказаний у конфігурації")
                return
            
            self.base_editor.logger.info(f"Збереження у файл: {input_file}")
            success = self.base_editor.file_manager.save_output_text(self.text_widget.text)
            
            if success:
                # Зберігаємо закладку
                self.save_bookmark()
                self.show_popup("Успіх", f"Файл збережено:\n{input_file}")
                self.base_editor.logger.info(f"Файл успішно збережено: {input_file}")
            else:
                self.base_editor.logger.error("Помилка збереження файлу")
                self.show_error_popup("Помилка збереження файлу")
                
        except Exception as e:
            self.base_editor.logger.error(f"Помилка збереження: {e}")
            self.show_error_popup(f"Помилка збереження: {str(e)}")

    def _set_cursor_by_index(self, idx: int):
        """Встановлення курсора за індексом"""
        self.base_editor.logger.debug(f"Встановлення курсора на індекс: {idx}")
        if not self.text_widget:
            return
        try:
            self.text_widget.cursor = self.text_widget.get_cursor_from_index(idx)
            self.base_editor.logger.debug(f"Курсор успішно встановлено на індекс: {idx}")
        except Exception as e:
            self.base_editor.logger.warning(f"Помилка встановлення курсора: {e}, спроба альтернативного методу")
            try:
                self.text_widget.cursor_index = idx
                self.base_editor.logger.debug("Курсор встановлено альтернативним методом")
            except Exception as e2:
                self.base_editor.logger.error(f"Критична помилка встановлення курсора: {e2}")

    # === МЕТОДИ РОБОТИ З ТЕГАМИ ===

    def set_speed_mode(self, spinner, value):
        """Встановлення швидкості мовлення"""
        self.current_speed = value
        self.base_editor.logger.info(f"Встановлено швидкість мовлення: {value}")

    def add_voice_tag(self, tag):
        """Додавання тегу голосу"""
        self.base_editor.logger.info(f"Додавання тегу голосу: {tag} зі швидкістю: {self.current_speed}")
        
        speed = self.current_speed
        full_tag = f"\n#{tag}: " if speed.lower() == "normal" else f"\n#{tag}_{speed.lower()}: "
        
        if not self.text_widget:
            self.base_editor.logger.error("Текстове поле не ініціалізовано")
            return
            
        try:
            cursor = self.text_widget.cursor_index()
            self.base_editor.logger.debug(f"Поточна позиція курсора: {cursor}")
        except Exception as e:
            cursor = len(self.text_widget.text)
            self.base_editor.logger.warning(f"Помилка отримання позиції курсора, використання кінця тексту: {cursor}")
            
        new_text = self.text_widget.text[:cursor] + full_tag + self.text_widget.text[cursor:]
        self.text_widget.text = new_text
        
        new_cursor_pos = cursor + len(full_tag)
        Clock.schedule_once(lambda dt: self._set_cursor_by_index(new_cursor_pos), 0)
        self.base_editor.logger.info(f"Тег додано, новий курсор: {new_cursor_pos}")

    def listen_tagged_fragment(self, *args):
        """Відтворення фрагменту між тегами"""
        self.base_editor.logger.info("Початок відтворення фрагменту між тегами")
        
        if not self.text_widget:
            self.base_editor.logger.error("Текстове поле не ініціалізовано")
            return
            
        try:
            idx = self.text_widget.cursor_index()
            self.base_editor.logger.debug(f"Позиція курсора для відтворення: {idx}")
        except Exception as e:
            idx = 0
            self.base_editor.logger.warning(f"Помилка отримання позиції курсора, використання 0: {e}")
            
        text = self.text_widget.text or ""
        
        # Регулярний вираз для пошуку тегів
        TAG_OPEN_RE = re.compile(r"#g\d+(?:_(slow|fast))?: ?", flags=re.IGNORECASE)
        opens = list(TAG_OPEN_RE.finditer(text))
        self.base_editor.logger.debug(f"Знайдено тегів у тексті: {len(opens)}")
        
        start_pos, start_speed = 0, "normal"
        for m in opens:
            if m.start() <= idx:
                start_pos = m.end()
                grp = m.group(1)
                start_speed = grp if grp else "normal"
                self.base_editor.logger.debug(f"Знайдено початковий тег: позиція {m.start()}, швидкість {start_speed}")
            else:
                break
                
        end_pos = len(text)
        for m in opens:
            if m.start() > idx:
                end_pos = m.start()
                self.base_editor.logger.debug(f"Знайдено кінцевий тег: позиція {m.start()}")
                break
                
        fragment = text[start_pos:end_pos].strip()
        self.base_editor.logger.info(f"Фрагмент для відтворення: {len(fragment)} символів, швидкість: {start_speed}")
        
        if fragment:
            self.base_editor.tts_manager.safe_tts_speak(fragment)
            self.base_editor.logger.info("Фрагмент відтворюється")
        else:
            self.base_editor.logger.warning("Текст між тегами не знайдено")
            self.show_status("Текст між тегами не знайдено")

    # === МЕТОДИ РОБОТИ З ВИДІЛЕННЯМ СЛІВ ===

    def on_text_touch(self, instance, touch):
        """Обробка торкання текстового поля"""
        if not instance.collide_point(*touch.pos):
            return False
        self.base_editor.logger.debug("Торкання текстового поля, визначення слова")
        Clock.schedule_once(lambda *_: self.detect_word_at_cursor(), 0.03)
        return False

    def detect_word_at_cursor(self):
        """Визначення слова під курсором"""
        try:
            cursor_idx = self.text_widget.cursor_index()
            self.base_editor.logger.debug(f"Визначення слова під курсором: {cursor_idx}")
        except Exception as e:
            self.base_editor.logger.error(f"Помилка отримання позиції курсора: {e}")
            self.clear_selection_state()
            return

        text = self.text_widget.text
        if not text:
            self.base_editor.logger.debug("Текст порожній, очищення виділення")
            self.clear_selection_state()
            return

        word, start, end = self.base_editor.text_processor.detect_word_at_cursor(text, cursor_idx)
        
        if word:
            self.text_before_selected_word = text[:start]
            self.text_after_selected_word = text[end:]
            self.selected_word = word
            self.btn_edit.disabled = False
            self.base_editor.logger.info(f"Виділено слово: '{word}' з позиції {start} до {end}")
        else:
            self.base_editor.logger.debug("Слово не знайдено під курсором")
            self.clear_selection_state()

    def clear_selection_state(self):
        """Очищення виділення"""
        self.selected_word = None
        self.btn_edit.disabled = True
        self.base_editor.logger.debug("Стан виділення очищено")

    def open_edit_popup(self, *_):
        """Відкриття попапу редагування слова"""
        if self.selected_word:
            self.base_editor.logger.info(f"Відкриття попапу редагування слова: '{self.selected_word}'")
            self.stop_tts()
            EditWordPopup(self, self.selected_word, self.app_name).open()
        else:
            self.base_editor.logger.warning("Спроба відкрити попап редагування без виділеного слова")

    def replace_word_in_current_paragraph(self, old_word: str, new_word: str):
        """Заміна слова в тексті"""
        self.base_editor.logger.info(f"Заміна слова: '{old_word}' -> '{new_word}'")
        
        if not self.text_widget:
            self.base_editor.logger.error("Текстове поле не ініціалізовано")
            return
            
        replaced = self.base_editor.text_processor.match_casing(old_word, new_word)
        self.base_editor.logger.debug(f"Слово з відповідним регістром: '{replaced}'")
        
        new_txt = self.text_before_selected_word + replaced + self.text_after_selected_word
        self.text_widget.text = new_txt
        
        new_pos = len(self.text_before_selected_word) + len(replaced)
        Clock.schedule_once(lambda dt: self._set_cursor_by_index(new_pos), 0)
        self.base_editor.logger.info(f"Слово замінено, новий курсор: {new_pos}")

    # === МЕТОДИ РОБОТИ З ЗАКЛАДКАМИ ===

    def save_bookmark(self):
        """Збереження поточної позиції у конфіг"""
        try:
            if self.text_widget:
                self.base_editor.current_cursor_pos = self.text_widget.cursor_index()
                self.base_editor.current_scroll_y = self.text_widget.scroll_y
                self.base_editor.save_bookmark()
                self.base_editor.logger.info(f"Закладку збережено: позиція {self.base_editor.current_cursor_pos}, прокрутка {self.base_editor.current_scroll_y}")
        except Exception as e:
            self.base_editor.logger.error(f"Помилка збереження закладки: {e}")

    def restore_bookmark(self):
        """Відновлення позиції з конфігу"""
        try:
            self.base_editor.restore_bookmark()
            self.base_editor.logger.info(f"Закладку відновлено: позиція {self.base_editor.current_cursor_pos}, прокрутка {self.base_editor.current_scroll_y}")
        except Exception as e:
            self.base_editor.logger.error(f"Помилка відновлення закладки: {e}")

    def reset_bookmark(self):
        """Скидання закладки до початкових значень"""
        self.base_editor.logger.info("Скидання закладки до початкових значень")
        try:
            self.base_editor.config_manager.update_bookmark(self.app_name, 0, 1.0, 0)
            if self.text_widget:
                self.text_widget.scroll_y = 1.0
                self._set_cursor_by_index(0)
            self.show_popup("Успіх", "Закладку скинуто. Відкриття з початку тексту буде активне.")
            self.base_editor.logger.info("Закладку успішно скинуто")
        except Exception as e:
            self.base_editor.logger.error(f"Помилка скидання закладки: {e}")
            self.show_error_popup(f"Помилка скидання закладки: {str(e)}")

    def stop_tts(self):
        """Зупинка TTS відтворення"""
        self.base_editor.logger.info("Зупинка TTS відтворення")
        self.base_editor.stop_tts()

    # === ТЕМА ІНТЕРФЕЙСУ ===

    def get_theme_colors(self):
        """Отримання кольорів теми"""
        return self.base_editor.get_theme_colors()

    def apply_theme(self):
        """Застосування теми до інтерфейсу"""
        self.base_editor.logger.info("Застосування теми до інтерфейсу")
        try:
            widgets_dict = {
                'buttons': [self.btn_listen, self.btn_pause, self.btn_edit, self.btn_extra] + self.voice_buttons,
                'text_inputs': [self.text_widget],
                'window': Window
            }
            
            if hasattr(self, 'speed_spinner'):
                widgets_dict['buttons'].append(self.speed_spinner)
            
            self.base_editor.theme_manager.apply_theme_to_widgets(widgets_dict)
            self.base_editor.logger.info("Тему застосовано до Voice Tags Editor")
            
        except Exception as e:
            self.base_editor.logger.error(f"Помилка застосування теми: {e}")

    def toggle_theme(self):
        """Перемикання теми день/ніч"""
        self.base_editor.logger.info("Перемикання теми день/ніч")
        self.stop_tts()
        self.base_editor.toggle_theme()
        self.apply_theme()
        self.base_editor.logger.info(f"Переключено тему: {self.base_editor.theme_manager.current_theme}")

    # === УТИЛІТИ ===

    def show_popup(self, title: str, message: str):
        """Показ спливаючого повідомлення"""
        self.base_editor.logger.info(f"Показ попапу: {title} - {message}")
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.4)
        )
        popup.open()

    def show_error_popup(self, message: str):
        """Показ попапу з помилкою"""
        self.base_editor.logger.error(f"Показ попапу помилки: {message}")
        self.show_popup("Помилка", message)

    def show_status(self, message: str):
        """Показ статусного повідомлення"""
        self.base_editor.logger.info(f"Показ статусного повідомлення: {message}")
        self.show_popup("Повідомлення", message)

    def on_stop(self):
        """Дії при закритті додатку"""
        self.base_editor.logger.info("Завершення роботи Voice Tags Editor")
        self.save_bookmark()
        self.stop_tts()
        self.base_editor.logger.info("Voice Tags Editor закрито")


# === ЗАПУСК ===
if __name__ == "__main__":
    input_text_file = "/storage/emulated/0/Documents/Inp_txt/доповнення13_у_нас_гості.txt"
    book_project_name = "доповнення13_у_нас_гості"
    
    app = VoiceTagsEditor(
        book_project_name=book_project_name,
        input_text_file=input_text_file
    )
    app.run()
