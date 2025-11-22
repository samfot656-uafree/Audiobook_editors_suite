# -*- coding: utf-8 -*-
"""
Менеджер роботи з файлами.
"""
import json
from pathlib import Path


class FileManager:
    """Керування файловими операціями."""

#-------------------------------------------    
    def __init__(self, config_manager, editor_name: str, logger=None):
        self.config_manager = config_manager
        self.editor_name = editor_name
        self.config = config_manager.load_for_editor(editor_name)
        self.logger = logger

#-------------------------------------------    
    def load_input_text(self) -> str:
        """Завантажує вхідний текст з файлу."""
        input_file = self.config.get('INPUT_TEXT_FILE', '')
        if not input_file or not Path(input_file).exists():
            error_msg = f"\nload_input_text: Файл не знайдено: {input_file}\n"
            if self.logger:
                self.logger.error(error_msg)
            return None

        try:
            with open(input_file, "r", encoding="utf-8") as f:
                raw_text = f.read()
                
            if self.logger:
                self.logger.info(f"\nload_input_text:  Текст завантажено: {len(raw_text)} символів, {len(raw_text.split())} слів\n")
            return raw_text
            
        except Exception as e:
            error_msg = f"\nload_input_text: Не вдалося прочитати файл: {e}\n"
            if self.logger:
                self.logger.error(error_msg)
            return None

#-------------------------------------------    
    def save_output_text(self, content: str) -> bool:
        """Зберігає текст у вихідний файл."""
        output_file = self.config.get('INPUT_TEXT_FILE', '')
        
        if not output_file:
            if self.logger:
                self.logger.error("\nsave_output_text:  Шлях для збереження не вказано\n")
            return False

        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            if self.logger:
                self.logger.info(f"\nsave_output_text: 💾 Текст збережено: {output_file}\n")
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"\nsave_output_text: Помилка збереження тексту: {e}\n")
            return False

#-------------------------------------------    
    def load_accents(self) -> dict:
        """Завантажує словник наголосів з JSON файлу."""
        accents_file = self.config.get('ACCENTS_FILE', '')
        if accents_file and Path(accents_file).exists():
            try:
                with open(accents_file, "r", encoding="utf-8") as f:
                    accents = json.load(f)
                if self.logger:
                    self.logger.info(f"\nload_accents:  Словник наголосів завантажено: {len(accents)} слів\n")
                return accents
            except Exception as e:
                error_msg = f"\nload_accents:  Помилка завантаження accents.json: {e}\n"
                if self.logger:
                    self.logger.error(error_msg)
        else:
            if self.logger:
                self.logger.warning(f"\nload_accents:  Файл словника не знайдено: {accents_file}\n")
        return {}

#-------------------------------------------        
    def save_accents(self, accents: dict) -> bool:
        """Зберігає словник наголосів у JSON файл."""
        accents_file = self.config.get('ACCENTS_FILE', '')
        if accents_file:
            try:
                Path(accents_file).parent.mkdir(parents=True, exist_ok=True)
                with open(accents_file, "w", encoding="utf-8") as f:
                    json.dump(accents, f, ensure_ascii=False, indent=2)
                if self.logger:
                    self.logger.info(f"\nsave_accents:  Словник наголосів збережено: {len(accents)} слів\n")
                return True
            except Exception as e:
                error_msg = f"\nsave_accents: Помилка збереження accents: {e}\n"
                if self.logger:
                    self.logger.error(error_msg)
        return False

#-------------------------------------------    
    def get_config_value(self, key: str, default=None):
        """Отримує значення з конфігурації."""
        return self.config.get(key, default)
 
 #-------------------------------------------   
    def update_config(self, updates: dict):
        """Оновлює конфігурацію через config_manager."""
        try:
            self.config_manager.save_from_editor(self.editor_name, updates)
            # Оновлюємо локальну копію конфігурації
            self.config = self.config_manager.load_for_editor(self.editor_name)
            if self.logger:
                self.logger.info(f"\nupdate_config: Конфігурацію оновлено: {list(updates.keys())}\n")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"\nupdate_config:  Помилка оновлення конфігурації: {e}\n")
            return False
#-------------------------------------------            