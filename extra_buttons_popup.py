# -*- coding: utf-8 -*-

"""
Попап з додатковими кнопками для всіх редакторів
"""
#Файл: /storage/emulated/0/a0_sb2_book_editors_suite/book_editors_suite/ui/popups/extra_buttons_popup.py


from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout


class ExtraButtonsPopup(Popup):
    """Попап з додатковими функціями редактора."""
    
    def __init__(self, main_app, editor_name, **kwargs):
        super().__init__(**kwargs)
        self.main_app = main_app
        self.editor_name = editor_name
        
        # для налагодження
#        self.editor_name = 'accent_editor'
#        self.editor_name = 'voice_tags_editor'
#        self.editor_name = 'sound_effects_editor'
#        self.title = f"{self.editor_name} \nДодаткові кнопки"

        self.title = "Додаткові кнопки"

        self.size_hint = (0.95, 0.6)
        self.auto_dismiss = True
        
        self._build_interface()
        Clock.schedule_once(lambda *_: self.apply_theme_from_app(), 0)

    def _build_interface(self):
        """Побудова інтерфейсу попапу з розташуванням кнопок у два стовпчики."""
        # Отримуємо налаштування з конфігурації
        try:
            # Для всіх редакторів тепер використовуємо base_editor
            config_data = self.main_app.base_editor.config_manager.data
            bbtn_font_size = config_data.get('BBTN_FONT_SIZE', 42)
            bbtn_height = config_data.get('BBTN_HEIGHT', 150)
        except AttributeError:
            # Резервні значення
            bbtn_font_size = 72
            bbtn_height = 220
      
        # Основний контейнер
        root = BoxLayout(orientation='vertical', spacing=8, padding=8)

        # Сітка кнопок зверху
        btn_grid = GridLayout(cols=2, size_hint_y=None, height=3*(8+bbtn_height), spacing=8)

        # Створюємо кнопки
        self.btn_save_txt = Button(text="До txt", font_size=bbtn_font_size)
        self.btn_save_mp3 = Button(text="До mp3", font_size=bbtn_font_size)
        self.btn_theme = Button(text="День-ніч", font_size=bbtn_font_size)
        self.btn_sort_dict = Button(text="Сортуй", font_size=bbtn_font_size)
        self.btn_bookmark_start = Button(text="Закладку на початок", font_size=bbtn_font_size)
        self.btn_back = Button(text="Повернутися", font_size=bbtn_font_size)
        
        # Список кнопок залежить від типу редактора
        if self.editor_name == "accent_editor":
            for btn in (self.btn_theme, self.btn_bookmark_start, self.btn_save_txt, self.btn_save_mp3, self.btn_sort_dict, self.btn_back):
                btn_grid.add_widget(btn)
            self.extra_button_list = (self.btn_theme, self.btn_bookmark_start, self.btn_save_txt, self.btn_save_mp3, self.btn_sort_dict, self.btn_back)
        
        elif self.editor_name in ["voice_tags_editor", "sound_effects_editor"]:
            for btn in (self.btn_theme, self.btn_bookmark_start, self.btn_save_txt, self.btn_back):
                btn_grid.add_widget(btn)
            self.extra_button_list = (self.btn_theme, self.btn_bookmark_start, self.btn_save_txt, self.btn_back)
        
        # Додаємо сітку кнопок до основного контейнера
        root.add_widget(btn_grid)
        root.add_widget(Label())  # Порожній простір
        self.content = root
        
        # Прив'язка кнопок
        self.btn_save_txt.bind(on_press=self.on_save_txt)
        if self.editor_name == "accent_editor":
            self.btn_save_mp3.bind(on_press=self.on_save_mp3)
            self.btn_sort_dict.bind(on_press=self.on_sort_dict)
        self.btn_theme.bind(on_press=self.on_toggle_theme)        
        self.btn_bookmark_start.bind(on_press=self.on_bookmark_start)
        self.btn_back.bind(on_press=lambda *_: self.dismiss())

    def apply_theme_from_app(self):
        """Застосовує тему з головного додатку."""
        colors = self.main_app.get_theme_colors()
        for b in self.extra_button_list:
            b.background_normal = ""
            b.background_color = colors["button_bg"]
            b.color = colors["button_fg"]           

    def on_save_txt(self, *_):
        """Зберігає текст у txt файл."""
        try:
            if self.editor_name == "accent_editor":
                self.main_app.save_full_text()
            elif self.editor_name == "voice_tags_editor":
                self.main_app.save_file()
            elif self.editor_name == "sound_effects_editor":
                self.main_app.save_file()
                
            self.show_success_popup("Збережено TXT")
            self.dismiss()
        except Exception as e:
            self.main_app.base_editor.logger.error(f"Помилка збереження txt: {e}")
            self.show_error_popup(f"Не вдалося зберегти TXT:\n{e}")

    def on_save_mp3(self, *_):
        """Зберігає текст у mp3 файл."""
        try:
            self.main_app.save_full_mp3()
            self.dismiss()
        except Exception as e:
            self.main_app.base_editor.logger.error(f"Помилка збереження mp3: {e}")
            self.show_error_popup(f"Не вдалося зберегти MP3:\n{e}")

    def on_toggle_theme(self, *_):
        """Перемикає тему."""
        try:
            self.main_app.toggle_theme()
            self.dismiss()
        except Exception as e:
            self.main_app.base_editor.logger.error(f"Помилка перемикання теми: {e}")

    def on_sort_dict(self, *_):
        """Сортує словник наголосів."""
        try:
            if hasattr(self.main_app, 'accents'):
                self.main_app.accents = dict(sorted(self.main_app.accents.items()))
                self.main_app.save_accents()
                self.show_success_popup("Словник відсортовано")
            else:
                self.show_error_popup("Цей редактор не має словника для сортування")
        except Exception as e:
            self.main_app.base_editor.logger.error(f"Помилка сортування словника: {e}")
            self.show_error_popup(f"Не вдалося відсортувати словник:\n{e}")

    def on_bookmark_start(self, *_):
        """Встановлює закладку на початок тексту."""
        try:
            config_manager = self.main_app.base_editor.config_manager
            
            config_manager.update_bookmark(
                editor_name=self.editor_name,
                cursor_pos=0,
                scroll_y=0.0,
                paragraph_index=0
            )
            
            # Оновлюємо поточні значення
            self.main_app.base_editor.current_cursor_pos = 0
            self.main_app.base_editor.current_scroll_y = 0.0
            self.main_app.base_editor.current_paragraph_index = 0
            
            # Встановлюємо відповідні значення для різних редакторів
            if self.editor_name == "accent_editor":
                if hasattr(self.main_app, 'current_idx'):
                    self.main_app.current_idx = 0
                if hasattr(self.main_app, 'text_for_correction') and self.main_app.text_for_correction:
                    self.main_app.text_input.text = self.main_app.text_for_correction[0]
                    self.main_app.text_input.cursor = (0, 0)
                    self.main_app.text_input.scroll_y = 0.0
            
            elif self.editor_name in ["voice_tags_editor", "sound_effects_editor"]:
                if hasattr(self.main_app, 'text_widget'):
                    self.main_app.text_widget.scroll_y = 1.0
                    if hasattr(self.main_app, '_set_cursor_by_index'):
                        self.main_app._set_cursor_by_index(0)
            
            self.main_app.base_editor.logger.info(f"\nЗакладку встановлено на початок тексту для {self.editor_name}\n")
            self.show_success_popup(f"Закладку для {self.editor_name} \nвстановлено на початок тексту")
                
        except Exception as e:
            self.main_app.base_editor.logger.error(f"Помилка встановлення закладки \nдля {self.editor_name}: {e}")
            self.show_error_popup(f"Не вдалося встановити закладку:\n{e}")

    def show_success_popup(self, message: str):
        """Показ попапу з успіхом"""
        Popup(
            title="Успіх", 
            content=Label(text=message), 
            size_hint=(0.7, 0.3)
        ).open()

    def show_error_popup(self, message: str):
        """Показ попапу з помилкою"""
        Popup(
            title="Помилка", 
            content=Label(text=message), 
            size_hint=(0.8, 0.3)
        ).open()