# -*- coding: utf-8 -*-
"""
Базовий клас для всіх редакторів зі стандартною ініціалізацією
"""

from book_editors_suite.core.config_manager import get_config_manager
from book_editors_suite.core.tts_manager import TTSManager
from book_editors_suite.core.file_manager import FileManager
from book_editors_suite.core.text_processor import TextProcessor
from book_editors_suite.core.logging_manager import LoggingManager
from book_editors_suite.ui.themes import ThemeManager


class BaseEditor:
    """Базовий клас для всіх редакторів зі стандартною ініціалізацією"""
    
    def __init__(self, book_project_name: str, input_text_file: str = None, editor_name: str = ""):
        self.book_project_name = book_project_name
        self.input_text_file = input_text_file
        self.editor_name = editor_name
        
        # Ініціалізація менеджерів
        self.config_manager = get_config_manager(book_project_name, input_text_file)
        self.config = self.config_manager.load_for_editor(editor_name)
        
        # Отримуємо інформацію про проект для логера
        project_info = self.config_manager.get_project_info()
        log_dir = project_info['base_path'] + f"/{self.book_project_name}/temp_folder/logs"
        self.logger = LoggingManager(log_dir, app_name=editor_name)
        
        self.tts_manager = TTSManager()
        self.file_manager = FileManager(self.config_manager, editor_name, self.logger)
        self.text_processor = TextProcessor(self.logger)
        self.theme_manager = ThemeManager()
        
        # Стандартні властивості
        self.current_scroll_y = 0.0
        self.current_cursor_pos = 0
        self.current_paragraph_index = 0
        
    def save_bookmark(self):
        """Зберегти закладку"""
        self.config_manager.update_bookmark(
            self.editor_name,
            self.current_cursor_pos,
            self.current_scroll_y,
            self.current_paragraph_index
        )
    
    def restore_bookmark(self):
        """Відновити закладку"""
        bookmark = self.config_manager.get_bookmark(self.editor_name)
        self.current_scroll_y = bookmark.get('scroll_y', 0.0)
        self.current_cursor_pos = bookmark.get('cursor_pos', 0)
        self.current_paragraph_index = bookmark.get('paragraph_index', 0)
    
    def get_theme_colors(self):
        """Отримання кольорів теми"""
        return self.theme_manager.get_colors()
    
    def toggle_theme(self):
        """Перемикання теми день/ніч"""
        self.theme_manager.toggle_theme()
    
    def stop_tts(self):
        """Зупинка TTS відтворення"""
        if self.tts_manager:
            self.tts_manager.stop_tts()
