# -*- coding: utf-8 -*-
"""
Sound Effects Editor - редактор тегів звукових ефектів
"""
# реалізовано лише додаввння тегів в текст та створення списку "тег-опис звуку- шлях до файлу"

import sys
import os
from pathlib import Path

# Додаємо шляхи для імпортів
sys.path.insert(0, '/storage/emulated/0/a0_sb2_book_editors_suite')
sys.path.insert(0, '/storage/emulated/0/a0_sb2_book_editors_suite/book_editors_suite')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
import threading

from book_editors_suite.core.base_editor import BaseEditor
from book_editors_suite.core.sound_effects_manager import SoundEffectsManager
from book_editors_suite.ui.popups.edit_word_popup import EditWordPopup
from book_editors_suite.ui.popups.extra_buttons_popup import ExtraButtonsPopup


class CompactSoundEffectsPopup(Popup):
    """Компактний попап з усіма звуковими ефектами"""
    
    def __init__(self, main_app, **kwargs):
        super().__init__(**kwargs)
        self.main_app = main_app
        self.title = "Усі звукові ефекти"
        self.size_hint = (0.9, 0.8)
        self.auto_dismiss = True
        
        self._build_interface()
    
    def _build_interface(self):
        """Побудова інтерфейсу попапу"""
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # ScrollView для ефектів
        scroll = ScrollView()
        effects_layout = GridLayout(cols=3, spacing=10, size_hint_y=None)
        effects_layout.bind(minimum_height=effects_layout.setter('height'))
        
        # Отримуємо всі звукові ефекти
        sound_effects = self.main_app.sound_effects_manager.read_sound_effects_list()
        sound_tags = sorted(sound_effects.keys())
        
        bbtn_font_size = self.main_app.base_editor.config_manager.get_common_param('BBTN_FONT_SIZE', 38) - 10
        
        for tag in sound_tags:
            effect = sound_effects[tag]
            display = f"{tag}\n{effect.get('description', '')[:12]}"
            btn = Button(
                text=display, 
                font_size=bbtn_font_size,
                size_hint_y=None,
                height=100
            )
            btn.bind(on_release=lambda inst, t=tag: self._select_effect(t))
            effects_layout.add_widget(btn)
        
        scroll.add_widget(effects_layout)
        layout.add_widget(scroll)
        
        # Кнопка закриття
        btn_close = Button(
            text="Закрити", 
            size_hint_y=None,
            height=60
        )
        btn_close.bind(on_press=self.dismiss)
        layout.add_widget(btn_close)
        
        self.content = layout
    
    def _select_effect(self, tag):
        """Вибрати ефект і закрити попап"""
        self.main_app.select_existing_effect(tag)
        self.dismiss()


class SoundEffectsEditor(App):
    """Редактор тегів звукових ефектів з компактною панеллю"""

    def __init__(self, book_project_name: str, input_text_file: str = None, **kwargs):
        super().__init__(**kwargs)
        self.book_project_name = book_project_name
        self.input_text_file = input_text_file
        self.app_name = "sound_effects_editor"
        
        # Використовуємо композицію замість успадкування від BaseEditor
        self.base_editor = BaseEditor(book_project_name, input_text_file, "sound_effects_editor")
        
        # Ініціалізація менеджера звукових ефектів
        sound_effects_list_path = self.base_editor.config.get('SOUNDS_EFFECTS_LIST', '')
        self.sound_effects_manager = SoundEffectsManager(sound_effects_list_path, self.base_editor.logger)
        
        # Додаткові властивості для звукових ефектів
        self.sound_dict = self.base_editor.config.get('SOUND_DICT', {})
        self.sound_effects_input_folder = self.base_editor.config.get('SOUNDS_EFFECTS_INPUT_FOLDER', '')
        
        # Відновлюємо закладку
        self.restore_bookmark()
        
        # Стан програми
        self.selected_word = None
        self.text_before_selected_word = ""
        self.text_after_selected_word = ""
        self.recent_effects = []  # Список останніх використаних ефектів
        
        # Віджети
        self.text_widget = None
        self.recent_effect_buttons = []
        self.btn_edit = None
        self.tag_input = None
        self.description_input = None
        self.file_input = None

    def build(self):
        """Побудова інтерфейсу"""
        Window.softinput_mode = "below_target"
        return self._build_interface()

    def _build_interface(self):
        """Побудова інтерфейсу"""
        self.base_editor.logger.info("Створення інтерфейсу Sound Effects Editor")
        
        # Отримуємо налаштування з конфігу
        bbtn_font_size = self.base_editor.config_manager.get_common_param('BBTN_FONT_SIZE', 38)
        text_widget_font_size = self.base_editor.config_manager.get_common_param('TEXT_WIDGET_FONT_SIZE', 56)
        bbtn_height = self.base_editor.config_manager.get_common_param('BBTN_HEIGHT', 120)
                
        layout = BoxLayout(orientation="vertical", spacing=5, padding=22)

        # Верхній ряд кнопок
        top_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=bbtn_height, spacing=8)
        self.btn_listen = Button(text="Слухати", font_size=bbtn_font_size)
        self.btn_edit = Button(text="Правити", font_size=bbtn_font_size, disabled=True)
        self.btn_extra = Button(text=". . .", font_size=bbtn_font_size)
        
        for b in (self.btn_listen, self.btn_edit, self.btn_extra):
            top_row.add_widget(b)
        layout.add_widget(top_row)

        # Поля для введення звукового ефекту
        # Рядок тегу
        tag_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=bbtn_height, spacing=8)
        self.tag_label = Label(text="Тег:", font_size=bbtn_font_size, size_hint_x=0.3, halign='left', valign='middle')
        tag_row.add_widget(self.tag_label)
        self.tag_input = TextInput(
            text=self.sound_effects_manager.get_next_available_tag(),
            multiline=False,
            font_size=text_widget_font_size-5
        )
        tag_row.add_widget(self.tag_input)
        layout.add_widget(tag_row)

        # Рядок опису
        desc_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=bbtn_height, spacing=8)
        self.desc_label = Label(text="Опис:", font_size=bbtn_font_size, size_hint_x=0.3, halign='left', valign='middle')
        desc_row.add_widget(self.desc_label)
        self.description_input = TextInput(
            text="",
            multiline=False,
            font_size=text_widget_font_size-5
        )
        desc_row.add_widget(self.description_input)
        layout.add_widget(desc_row)

        # Рядок файлу
        file_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=bbtn_height, spacing=8)
        self.file_label = Label(text="Файл:", font_size=bbtn_font_size, size_hint_x=0.3, halign='left', valign='middle')
        file_row.add_widget(self.file_label)

        self.file_input = TextInput(
            text="",
            multiline=False,
            font_size=text_widget_font_size-5
        )
        file_row.add_widget(self.file_input)
        
        self.btn_select_file = Button(text="Обрати", font_size=bbtn_font_size, size_hint_x=0.3)
        file_row.add_widget(self.btn_select_file)
        layout.add_widget(file_row)

        # Кнопка додавання звукового ефекту
        self.btn_add_effect = Button(
            text="Додати звуковий ефект", 
            font_size=bbtn_font_size,
            size_hint_y=None,
            height=bbtn_height
        )
        layout.add_widget(self.btn_add_effect)

        # === КОМПАКТНА ПАНЕЛЬ ЗВУКОВИХ ЕФЕКТІВ ===
        effects_panel = BoxLayout(orientation='vertical', size_hint_y=None, height=bbtn_height + 20, spacing=8)
        
        # Заголовок панелі
        effects_label = Label(
            text="Останні звукові ефекти:", 
            font_size=bbtn_font_size - 8,
            size_hint_y=None,
            height=40
        )
        effects_panel.add_widget(effects_label)
        
        # Рядок з трьома останніми ефектами та кнопкою "Всі"
        effects_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=bbtn_height, spacing=8)
        
        # Три кнопки останніх ефектів
        self.recent_effect_buttons = []
        for i in range(3):
            btn = Button(
                text=f"S{i+1:02d}",
                font_size=bbtn_font_size - 8,
                disabled=True
            )
            btn.bind(on_release=lambda inst, idx=i: self._on_recent_effect_click(idx))
            effects_row.add_widget(btn)
            self.recent_effect_buttons.append(btn)
        
        # Кнопка "Всі ефекти"
        self.btn_all_effects = Button(
            text="Всі\nефекти",
            font_size=bbtn_font_size - 10,
            size_hint_x=0.3
        )
        self.btn_all_effects.bind(on_press=self._show_all_effects)
        effects_row.add_widget(self.btn_all_effects)
        
        effects_panel.add_widget(effects_row)
        layout.add_widget(effects_panel)

        # Текстове поле
        self.text_widget = TextInput(text="", multiline=True, font_size=text_widget_font_size)
        self.text_widget.bind(on_touch_down=self.on_text_touch)
        layout.add_widget(self.text_widget)

        # Прив'язка подій
        self.btn_listen.bind(on_press=self.listen_current_word)
        self.btn_edit.bind(on_press=self.open_edit_popup)
        self.btn_extra.bind(on_press=lambda *_: ExtraButtonsPopup(main_app=self, editor_name=self.app_name).open())
        self.btn_select_file.bind(on_press=self.select_sound_file)
        self.btn_add_effect.bind(on_press=self.add_sound_effect)

        # Автоматичні дії
        Clock.schedule_once(lambda *_: self.apply_theme(), 0.0)
        Clock.schedule_once(lambda *_: self.open_file_async(), 0.1)
        Clock.schedule_once(lambda *_: self.update_recent_effects(), 0.2)

        return layout

    def update_recent_effects(self):
        """Оновлення списку останніх звукових ефектів"""
        try:
            sound_effects = self.sound_effects_manager.read_sound_effects_list()
            sound_tags = sorted(sound_effects.keys(), reverse=True)  # Сортуємо за тегом (новіші перші)
            
            # Беремо останні 3 ефекти
            recent_tags = sound_tags[:3]
            
            for i, tag in enumerate(recent_tags):
                if i < len(self.recent_effect_buttons):
                    effect = sound_effects[tag]
                    display = f"{tag}\n{effect.get('description', '')[:10]}"
                    self.recent_effect_buttons[i].text = display
                    self.recent_effect_buttons[i].disabled = False
                    # Зберігаємо тег у властивості кнопки
                    self.recent_effect_buttons[i].effect_tag = tag
            
            # Відключаємо незаповнені кнопки
            for i in range(len(recent_tags), 3):
                if i < len(self.recent_effect_buttons):
                    self.recent_effect_buttons[i].text = f"S{i+1:02d}"
                    self.recent_effect_buttons[i].disabled = True
                    self.recent_effect_buttons[i].effect_tag = None
                    
        except Exception as e:
            self.base_editor.logger.error(f"Помилка оновлення останніх ефектів: {e}")

    def _on_recent_effect_click(self, index):
        """Обробка кліку на кнопку останнього ефекту"""
        if index < len(self.recent_effect_buttons):
            btn = self.recent_effect_buttons[index]
            if hasattr(btn, 'effect_tag') and btn.effect_tag:
                self.select_existing_effect(btn.effect_tag)
                
                # Додаємо тег до тексту в позицію курсору
                if self.text_widget:
                    cursor_pos = self.text_widget.cursor_index()
                    sound_tag = f"#{btn.effect_tag}: "
                    self.text_widget.text = (self.text_widget.text[:cursor_pos] + 
                                           sound_tag + 
                                           self.text_widget.text[cursor_pos:])
                    # Переміщаємо курсор після тегу
                    Clock.schedule_once(lambda dt: self._set_cursor_by_index(cursor_pos + len(sound_tag)), 0.1)

    def _show_all_effects(self, instance):
        """Показати попап з усіма звуковими ефектами"""
        CompactSoundEffectsPopup(self).open()

    def open_file_async(self, *args):
        """Асинхронне завантаження файлу"""
        def load_file():
            try:
                input_file = self.base_editor.config.get('INPUT_TEXT_FILE', '')
                if not input_file or not Path(input_file).exists():
                    Clock.schedule_once(lambda dt: self.show_error_popup("Файл не вказаний або не існує"), 0)
                    return
                
                with open(input_file, "r", encoding="utf-8") as f:
                    content = f.read()
                Clock.schedule_once(lambda dt: self.set_text(content), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self.show_error_popup(str(e)), 0)
        
        threading.Thread(target=load_file, daemon=True).start()

    def set_text(self, text):
        """Встановлення тексту та відновлення закладки"""
        if self.text_widget:
            self.text_widget.text = text
            self.open_bookmark()

    def open_bookmark(self):
        """Відновлення позиції закладки"""
        try:
            self.text_widget.scroll_y = float(self.base_editor.current_scroll_y)
            if self.base_editor.current_cursor_pos > 0:
                Clock.schedule_once(lambda dt: self._set_cursor_by_index(self.base_editor.current_cursor_pos), 0.08)
            else:
                Clock.schedule_once(lambda dt: self._set_cursor_by_index(0), 0.05)
        except Exception as e:
            self.base_editor.logger.error(f"Не вдалося відновити закладку: \n{e}")
            self.text_widget.scroll_y = 1.0
            self._set_cursor_by_index(0)

    def _set_cursor_by_index(self, idx: int):
        """Встановлення курсора за індексом"""
        if not self.text_widget:
            return
        try:
            self.text_widget.cursor = self.text_widget.get_cursor_from_index(idx)
        except Exception:
            try:
                self.text_widget.cursor_index = idx
            except Exception:
                pass

    def select_sound_file(self, instance):
        """Вибір файлу звукового ефекту"""
        self.show_popup("Вибір файлу", "Функція вибору файлу буде реалізована пізніше")

    def add_sound_effect(self, instance):
        """Додавання звукового ефекту до тексту та списку"""
        tag = self.tag_input.text.strip()
        description = self.description_input.text.strip()
        file_path = self.file_input.text.strip()

        if not tag:
            self.show_error_popup("Введіть тег \n звукового ефекту")
            return

        if not description:
            self.show_error_popup("Введіть опис\n звукового ефекту")
            return

        # Перевіряємо формат тегу
        if not tag.upper().startswith('S') or not tag[1:].isdigit():
            self.show_error_popup("Тег повинен мати формат S01, S02, ... S99")
            return

        try:
            # Додаємо тег до тексту в позицію курсору
            if self.text_widget:
                cursor_pos = self.text_widget.cursor_index()
                sound_tag = f"#{tag}: "
                self.text_widget.text = (self.text_widget.text[:cursor_pos] + 
                                       sound_tag + 
                                       self.text_widget.text[cursor_pos:])
                # Переміщаємо курсор після тегу
                Clock.schedule_once(lambda dt: self._set_cursor_by_index(cursor_pos + len(sound_tag)), 0.1)
            
            # Додаємо до списку звукових ефектів
            success = self.sound_effects_manager.add_or_update_sound_effect(
                tag, description, file_path
            )
            
            if success:
                self.base_editor.logger.info(f"Додано звуковий ефект: \n{tag} - \n{description}")
                self.show_popup("Успіх", f"Звуковий ефект \n{tag} - \n{description} \nдодано")
                
                # Оновлюємо інтерфейс
                self.update_recent_effects()
                
                # Очищаємо поля та встановлюємо наступний тег
                self.tag_input.text = self.sound_effects_manager.get_next_available_tag()
                self.description_input.text = ""
                self.file_input.text = ""
            else:
                self.show_error_popup("Помилка збереження звукового ефекту")
                
        except Exception as e:
            self.base_editor.logger.error(f"Помилка додавання звукового ефекту: {e}")
            self.show_error_popup(f"Помилка: {str(e)}")

    def select_existing_effect(self, tag: str):
        """Вибрати існуючий звуковий ефект для редагування"""
        effect = self.sound_effects_manager.get_sound_effect(tag)
        if effect:
            self.tag_input.text = tag
            self.description_input.text = effect.get('description', '')
            self.file_input.text = effect.get('file_path', '')

    # === МЕТОДИ РОБОТИ З ВИДІЛЕННЯМ СЛІВ ===

    def on_text_touch(self, instance, touch):
        """Обробка торкання текстового поля"""
        if not instance.collide_point(*touch.pos):
            return False
        Clock.schedule_once(lambda *_: self.detect_word_at_cursor(), 0.03)
        return False

    def detect_word_at_cursor(self):
        """Визначення слова під курсором"""
        try:
            cursor_idx = self.text_widget.cursor_index()
        except Exception as e:
            self.clear_selection_state()
            return

        text = self.text_widget.text
        if not text:
            self.clear_selection_state()
            return

        # Використовуємо TextProcessor для визначення слова
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
            EditWordPopup(self, self.selected_word, self.app_name).open()

    def replace_word_in_current_paragraph(self, old_word: str, new_word: str):
        """Заміна слова в тексті"""
        if not self.text_widget:
            return
            
        # Використовуємо text_processor для заміни з правильним регістром
        replaced = self.base_editor.text_processor.match_casing(old_word, new_word)
        
        new_txt = self.text_before_selected_word + replaced + self.text_after_selected_word
        self.text_widget.text = new_txt
        new_pos = len(self.text_before_selected_word) + len(replaced)
        Clock.schedule_once(lambda dt: self._set_cursor_by_index(new_pos), 0)

    def listen_current_word(self, instance):
        """Відтворення поточного слова через TTS"""
        if self.selected_word:
            self.base_editor.tts_manager.safe_tts_speak(self.selected_word)

    # === МЕТОДИ РОБОТИ З ЗАКЛАДКАМИ ===

    def save_bookmark(self):
        """Збереження поточної позиції у конфіг"""
        try:
            if self.text_widget and hasattr(self, 'base_editor'):
                self.base_editor.current_cursor_pos = self.text_widget.cursor_index()
                self.base_editor.current_scroll_y = self.text_widget.scroll_y
                
                self.base_editor.config_manager.update_bookmark(
                    self.app_name, 
                    self.base_editor.current_cursor_pos, 
                    self.base_editor.current_scroll_y,
                    0
                )
                self.base_editor.logger.debug(f"Закладку збережено: позиція {self.base_editor.current_cursor_pos}, прокрутка {self.base_editor.current_scroll_y}")
        except Exception as e:
            self.base_editor.logger.error(f"Помилка збереження закладки: {e}")

    def save_file(self):
        """Збереження файлу та закладки"""
        if not self.text_widget or not self.text_widget.text.strip():
            self.show_error_popup("Текстове поле порожнє")
            return
        
        try:
            input_file = self.base_editor.config.get('INPUT_TEXT_FILE', '')
            if not input_file:
                self.show_error_popup("Файл не вказаний у конфігурації")
                return
            
            success = self.base_editor.file_manager.save_output_text(self.text_widget.text)
            
            if success:
                # Зберігаємо закладку
                self.save_bookmark()
                self.show_popup("Успіх", f"Файл збережено:\n{input_file}")
                self.base_editor.logger.info(f"Файл успішно збережено: {input_file}")
            else:
                self.show_error_popup("Помилка збереження файлу")
                
        except Exception as e:
            self.base_editor.logger.error(f"Помилка збереження: {e}")
            self.show_error_popup(f"Помилка збереження: {str(e)}")

    def restore_bookmark(self):
        """Відновлення позиції з конфігу"""
        try:
            if hasattr(self, 'base_editor'):
                bookmark = self.base_editor.config_manager.get_bookmark(self.app_name)
                if bookmark:
                    self.base_editor.current_scroll_y = bookmark.get('scroll_y', 0.0)
                    self.base_editor.current_cursor_pos = bookmark.get('cursor_pos', 0)
                    self.base_editor.logger.debug(f"Закладку відновлено: \nпозиція {self.base_editor.current_cursor_pos}, \nпрокрутка {self.base_editor.current_scroll_y}")
        except Exception as e:
            self.base_editor.logger.error(f"Помилка відновлення закладки: {e}")

    # === ТЕМА ІНТЕРФЕЙСУ ===

    def get_theme_colors(self):
        """Отримання кольорів теми"""
        return self.base_editor.theme_manager.get_colors()

    def apply_theme(self):
        """Застосування теми до інтерфейсу"""
        try:
            # Створюємо словник з віджетами для теми
            widgets_dict = {
                'buttons': [
                    self.btn_listen, self.btn_edit, self.btn_extra,
                    self.btn_select_file, self.btn_add_effect,
                    self.btn_all_effects
                ] + self.recent_effect_buttons,
                'labels': [
                    self.tag_label, self.desc_label, self.file_label
                ],
                'text_inputs': [
                    self.text_widget, self.tag_input, 
                    self.description_input, self.file_input
                ],
                'window': Window
            }
            
            # Використовуємо ThemeManager для застосування теми
            self.base_editor.theme_manager.apply_theme_to_widgets(widgets_dict)
            self.base_editor.logger.debug("Тему застосовано до Sound Effects Editor")
            
        except Exception as e:
            self.base_editor.logger.error(f"Помилка застосування теми: {e}")

    def toggle_theme(self):
        """Перемикання теми день/ніч"""
        self.base_editor.theme_manager.toggle_theme()
        self.apply_theme()
        self.base_editor.logger.info(f"Переключено тему: \n{self.base_editor.theme_manager.current_theme}")

    # === УТИЛІТИ ===

    def show_popup(self, title: str, message: str):
        """Показ спливаючого повідомлення"""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.4)
        )
        popup.open()
        self.base_editor.logger.debug(f"Показано попап: {title}")

    def show_error_popup(self, message: str):
        """Показ попапу з помилкою"""
        self.show_popup("Помилка", message)

    def on_stop(self):
        """Дії при закритті додатку"""
        self.save_bookmark()
        self.base_editor.tts_manager.stop_tts()
        self.base_editor.logger.info("Sound Effects Editor закрито")


# === ЗАПУСК ===
if __name__ == "__main__":
    # Приклад запуску
    input_text_file = "/storage/emulated/0/book_projects/доповнення13_у_нас_гості/book_text_file/доповнення13_у_нас_гості.txt"
    book_project_name = "доповнення13_у_нас_гості"
    
    app = SoundEffectsEditor(
        book_project_name=book_project_name,
        input_text_file=input_text_file
    )
    app.run()
