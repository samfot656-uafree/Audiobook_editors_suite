# -*- coding: utf-8 -*-
# Оновлена версія редактора наголосів з використанням BaseEditor

#Файл: /storage/emulated/0/a0_sb2_book_editors_suite/book_editors_suite/editors/accent_editor/main.py

# Не варто додавати наголоси в кожне слово. Лише до проблемних для певної TTS: вигадані назви, сленг, омоніми. Замінити прослуховування з андроїд ттс на потрібну.

import sys
import os
from pathlib import Path

sys.path.insert(0, '/storage/emulated/0/a0_sb2_book_editors_suite')
sys.path.insert(0, '/storage/emulated/0/a0_sb2_book_editors_suite/book_editors_suite')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock

from book_editors_suite.core.base_editor import BaseEditor
from book_editors_suite.ui.popups.edit_word_popup import EditWordPopup
from book_editors_suite.ui.popups.extra_buttons_popup import ExtraButtonsPopup


class AccentEditorApp(App):
    """Редактор наголосів з використанням BaseEditor"""

    def __init__(self, book_project_name: str, input_text_file: str = None, **kwargs):
        super().__init__(**kwargs)
        self.book_project_name = book_project_name
        self.input_text_file = input_text_file
        self.app_name = "accent_editor"
        
        # Використовуємо BaseEditor
        self.base_editor = BaseEditor(book_project_name, input_text_file, "accent_editor")
        
        # Властивості редактора наголосів
        self.accents = {}
        self.text_for_correction = []
        self.fixed_text = []
        self.current_idx = -1
        self.selected_word = None
        self.text_before_selected_word = ""
        self.text_after_selected_word = ""
        
        # Віджети
        self.text_input = None
        self.btn_listen = None
        self.btn_pause = None
        self.btn_edit = None
        self.btn_next = None
        self.btn_extra = None

    def build(self):
        """Побудова інтерфейсу"""
        self._init_managers()
        Window.softinput_mode = "below_target"
        return self._build_interface()

    def _init_managers(self):
        """Ініціалізація менеджерів"""
        try:
            self.accents = self.base_editor.file_manager.load_accents()
            self.base_editor.logger.info("Менеджери ініціалізовані")
        except Exception as e:
            self.show_popup("Помилка", f"Помилка ініціалізації:\n{e}")

    def _build_interface(self):
        """Побудова інтерфейсу"""
        bbtn_font_size = self.base_editor.config_manager.get_common_param('BBTN_FONT_SIZE', 38)
        text_widget_font_size = self.base_editor.config_manager.get_common_param('TEXT_WIDGET_FONT_SIZE', 56)
        bbtn_height = self.base_editor.config_manager.get_common_param('BBTN_HEIGHT', 120)
            
        root = BoxLayout(orientation='vertical', spacing=8, padding=22)

        # Верхній ряд кнопок
        top_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=bbtn_height, spacing=8)
        self.btn_listen = Button(text="Слухати", font_size=bbtn_font_size)
        self.btn_pause = Button(text="Пауза", font_size=bbtn_font_size)
        self.btn_edit = Button(text="Правити", font_size=bbtn_font_size, disabled=True)
        self.btn_next = Button(text="Наступний", font_size=bbtn_font_size)
        self.btn_extra = Button(text="  . . .  ", font_size=bbtn_font_size)
        
        for btn in (self.btn_listen, self.btn_pause, self.btn_edit, self.btn_next, self.btn_extra):
            top_row.add_widget(btn)

        # Текстове поле
        self.text_input = TextInput(font_size=text_widget_font_size, multiline=True)
        self.text_input.bind(on_touch_down=self.on_text_touch)

        root.add_widget(top_row)
        root.add_widget(self.text_input)
        self._bind_events()

        Clock.schedule_once(lambda *_: self.open_and_prepare_text(), 0.1)
        Clock.schedule_once(lambda *_: self.apply_theme(), 0)
        Clock.schedule_once(lambda *_: self.restore_bookmark(), 0.2)

        return root

    def _bind_events(self):
        """Прив'язка подій"""
        self.btn_listen.bind(on_press=lambda *_: self.listen_current_paragraph())
        self.btn_pause.bind(on_press=lambda *_: self.stop_tts())
        self.btn_edit.bind(on_press=self.open_edit_popup)
        self.btn_next.bind(on_press=lambda *_: self.go_next_paragraph())
        self.btn_extra.bind(on_press=lambda *_: ExtraButtonsPopup(main_app=self, editor_name=self.app_name).open())

    # ========== КРИТИЧНІ МЕТОДИ ==========

    def open_and_prepare_text(self):
        """Завантажує текст і відновлює закладку З ПРОПУСКОМ ПОРОЖНІХ АБЗАЦІВ"""
        try:
            raw_text = self.base_editor.file_manager.load_input_text()
            if raw_text is None:
                self.base_editor.logger.warning("Текст не знайдено")
                return

            accented_text = self.base_editor.text_processor.add_accents_to_text(raw_text, self.accents)
            paragraphs = accented_text.split("\n")
            self.text_for_correction = paragraphs
            self.fixed_text = []

            self.restore_bookmark()
            target_index = self.base_editor.current_paragraph_index

            # Додаємо абзаци до закладки
            for i in range(target_index):
                self.fixed_text.append(self.text_for_correction[i])

            # ПРОПУСК ПОРОЖНІХ АБЗАЦІВ
            while (target_index < len(paragraphs) and not paragraphs[target_index].strip()):
                self.fixed_text.append("")
                target_index += 1

            if target_index < len(paragraphs):
                self.text_input.text = paragraphs[target_index]
                self.base_editor.current_paragraph_index = target_index
            else:
                self.text_input.text = ""
                self.base_editor.current_paragraph_index = len(paragraphs)

            total_paragraphs = len(paragraphs)
            self.btn_extra.text = f"   . . .   \n{self.base_editor.current_paragraph_index+1}/{total_paragraphs}"
            self.clear_selection_state()

        except Exception as e:
            self.base_editor.logger.error(f"Помилка підготовки тексту: {e}")
            self.show_popup("Помилка", f"Не вдалося підготувати текст:\n{e}")

    def go_next_paragraph(self):
        """Перехід до наступного абзацу З ПРОПУСКОМ ПОРОЖНІХ"""
        self.stop_tts()

        current_text = self.text_input.text
        if self.base_editor.current_paragraph_index < len(self.text_for_correction):
            self.fixed_text.append(current_text)
            self.base_editor.current_paragraph_index += 1
            
            # ПРОПУСК ПОРОЖНІХ АБЗАЦІВ
            while (self.base_editor.current_paragraph_index < len(self.text_for_correction) and 
                   not self.text_for_correction[self.base_editor.current_paragraph_index].strip()):
                self.fixed_text.append("")
                self.base_editor.current_paragraph_index += 1

            if self.base_editor.current_paragraph_index < len(self.text_for_correction):
                self.text_input.text = self.text_for_correction[self.base_editor.current_paragraph_index]
            else:
                self.text_input.text = ""
                self.show_popup("Кінець", "Досягнуто кінця тексту")

        self.btn_extra.text = f"   . . .   \n{self.base_editor.current_paragraph_index+1}/{len(self.text_for_correction)}"
        self.move_bookmark()
        self.clear_selection_state()

    def move_bookmark(self):
        """Оновлює закладку у властивостях класу"""
        try:
            if self.text_input:
                self.base_editor.current_cursor_pos = self.text_input.cursor_index()
                self.base_editor.current_scroll_y = self.text_input.scroll_y
        except Exception as e:
            self.base_editor.logger.error(f"Помилка оновлення закладки: {e}")

    def save_bookmark(self):
        """Зберігає закладку в конфіг"""
        try:
            self.base_editor.save_bookmark()
        except Exception as e:
            self.base_editor.logger.error(f"Помилка збереження закладки: {e}")

    def restore_bookmark(self):
        """Відновлює закладку з конфігу"""
        try:
            self.base_editor.restore_bookmark()
        except Exception as e:
            self.base_editor.logger.error(f"Помилка відновлення закладки: {e}")

    def build_full_text(self) -> str:
        """Побудова повного тексту"""
        parts = []
        parts.extend(self.fixed_text)
        
        if self.base_editor.current_paragraph_index < len(self.text_for_correction):
            parts.append(self.text_input.text)
            if self.base_editor.current_paragraph_index + 1 < len(self.text_for_correction):
                parts.extend(self.text_for_correction[self.base_editor.current_paragraph_index + 1:])
        
        return "\n".join(parts)

    def save_full_text(self):
        """Збереження повного тексту"""
        self.stop_tts()
        content = self.build_full_text()
        success = self.base_editor.file_manager.save_output_text(content)
        self.save_bookmark()
        
        if success:
            self.base_editor.logger.info("Текст успішно збережено")
            self.show_popup("Успіх", "Текст збережено")
        else:
            self.base_editor.logger.error("Помилка збереження тексту")
            self.show_popup("Помилка", "Не вдалося зберегти текст")

    def save_full_mp3(self):
        """Збереження тексту в MP3"""
        self.stop_tts()
        content = self.build_full_text().strip()
        if not content:
            self.show_popup("Помилка", "Текст порожній")
            return
        
        try:
            project_info = self.base_editor.config_manager.get_project_info()
            project_name = project_info.get('project_name', self.book_project_name)
            base_path = project_info.get('base_path', '/storage/emulated/0/book_projects')
            project_path = f"{base_path}/{project_name}"
            
            mp3_folder = f"{project_path}/outputs/output_mp3"
            os.makedirs(mp3_folder, exist_ok=True)
            out_f_path = f"{mp3_folder}/{project_name}.mp3"
            
            from gtts import gTTS
            tts = gTTS(text=content, lang="uk")
            tts.save(out_f_path)
            
            self.show_popup("MP3 збережено", f"MP3 збережено:\n{out_f_path}")
            self.base_editor.logger.info(f"MP3 збережено: {out_f_path}")
        
        except ImportError:
            error_msg = "Бібліотека gTTS не встановлена. pip install gtts"
            self.base_editor.logger.error(error_msg)
            self.show_popup("Помилка gTTS", error_msg)
        
        except Exception as e:
            error_msg = f"Помилка MP3: \n{str(e)}"
            self.base_editor.logger.error(error_msg)
            self.show_popup("Помилка", error_msg)

    def sort_dictionary(self):
        """Сортування словника"""
        try:
            self.accents = dict(sorted(self.accents.items()))
            self.save_accents()
            self.show_popup("Успіх", "Словник відсортовано")
            self.base_editor.logger.info("Словник відсортовано")
        except Exception as e:
            self.base_editor.logger.error(f"Помилка сортування: {e}")
            self.show_popup("Помилка", f"Не вдалося відсортувати словник:\n{e}")

    def save_accents(self):
        """Збереження словника"""
        try:
            success = self.base_editor.file_manager.save_accents(self.accents)
            if success:
                self.base_editor.logger.info("Словник наголосів збережено")
            else:
                self.base_editor.logger.error("Помилка збереження словника")
        except Exception as e:
            self.base_editor.logger.error(f"Помилка збереження словника: {e}")

    # ========== МЕТОДИ РОБОТИ З ТЕКСТОМ ==========

    def on_text_touch(self, instance, touch):
        """Обробка торкання текстового поля"""
        if not instance.collide_point(*touch.pos):
            return False
        Clock.schedule_once(lambda *_: self.detect_word_at_cursor(), 0.01)
        return False

    def detect_word_at_cursor(self):
        """Визначення слова під курсором"""
        try:
            cursor_idx = self.text_input.cursor_index()
        except Exception as e:
            self.clear_selection_state()
            return

        text = self.text_input.text
        if not text:
            self.clear_selection_state()
            return

        word, start, end = self.base_editor.text_processor.detect_word_at_cursor(text, cursor_idx)
        
        if word:
            self.text_before_selected_word = text[:start]
            self.text_after_selected_word = text[end:]
            self.selected_word = word
            self.btn_edit.disabled = False
            self.base_editor.logger.debug(f"Виділено слово: '{word}'")
        else:
            self.clear_selection_state()

    def clear_selection_state(self):
        """Очищення виділення"""
        self.selected_word = None
        self.btn_edit.disabled = True

    def open_edit_popup(self, *_):
        """Відкриття попапу редагування слова"""
        if self.selected_word:
            self.stop_tts()
            EditWordPopup(self, self.selected_word, self.app_name).open()

    def replace_word_in_current_paragraph(self, old_word: str, new_word: str):
        """Заміна слова в тексті"""
        if self.base_editor.current_paragraph_index < 0:
            return
            
        if not self.text_input:
            return
            
        replaced = self.base_editor.text_processor.match_casing(old_word, new_word)
        
        new_txt = self.text_before_selected_word + replaced + self.text_after_selected_word
        self.text_input.text = new_txt
        new_pos = len(self.text_before_selected_word) + len(replaced)
        Clock.schedule_once(lambda dt: self._set_cursor_by_index(new_pos), 0)

    def _set_cursor_by_index(self, idx: int):
        """Встановлення курсора за індексом"""
        if not self.text_input:
            return
        try:
            self.text_input.cursor = self.text_input.get_cursor_from_index(idx)
        except Exception:
            try:
                self.text_input.cursor_index = idx
            except Exception:
                pass

    def listen_current_paragraph(self):
        """Відтворення поточного абзацу через TTS"""
        text = self.text_input.text.strip()
        if text:
            self.base_editor.tts_manager.safe_tts_speak(text)

    def stop_tts(self):
        """Зупинка TTS"""
        self.base_editor.stop_tts()

    # ========== ТЕМА ІНТЕРФЕЙСУ ==========

    def get_theme_colors(self):
        """Отримання кольорів теми"""
        return self.base_editor.get_theme_colors()

    def apply_theme(self):
        """Застосування теми до інтерфейсу"""
        try:
            widgets_dict = {
                'buttons': [self.btn_listen, self.btn_pause, self.btn_edit, self.btn_next, self.btn_extra],
                'text_inputs': [self.text_input],
                'window': Window
            }
            self.base_editor.theme_manager.apply_theme_to_widgets(widgets_dict)
        except Exception as e:
            self.base_editor.logger.error(f"Помилка застосування теми: {e}")

    def toggle_theme(self):
        """Перемикання теми"""
        self.stop_tts()
        self.base_editor.toggle_theme()
        self.apply_theme()

    # ========== УТИЛІТИ ==========

    def show_popup(self, title: str, message: str):
        """Показ спливаючого повідомлення"""
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()

    def on_stop(self):
        """Дії при закритті додатку"""
        self.save_bookmark()
        self.stop_tts()
        self.base_editor.logger.info("Редактор наголосів закрито")


# ========== Запуск ==========
if __name__ == "__main__":
    input_text_file = "/storage/emulated/0/Documents/Inp_txt/доповнення13_у_нас_гості.txt"
    book_project_name = "доповнення13_у_нас_гості"
    #input_text_file = "/storage/emulated/0/Documents/Inp_txt/Чекаючий_1_1.txt"
 #   book_project_name = "Чекаючий_1_1"
    
    app = AccentEditorApp(
        book_project_name=book_project_name,
        input_text_file=input_text_file
    )
    app.run()
