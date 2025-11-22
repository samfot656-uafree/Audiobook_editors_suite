# -*- coding: utf-8 -*-
"""
Менеджер для роботи з sound_effects_list.json
"""
# Файл: /storage/emulated/0/a0_sb2_book_editors_suite/book_editors_suite/core/sound_effects_manager.py


import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional


class SoundEffectsManager:
    """Менеджер для роботи з sound_effects_list.json"""
    
    def __init__(self, sound_effects_list_path: str, logger=None):
        self.sound_effects_list_path = sound_effects_list_path
        self.logger = logger
        self.create_sound_effects_list_if_not_exists()
    
    def create_sound_effects_list_if_not_exists(self) -> bool:
        """Створити файл sound_effects_list.json якщо не знайдено"""
        try:
            if not os.path.exists(self.sound_effects_list_path):
                # Створюємо директорію, якщо її немає
                os.makedirs(os.path.dirname(self.sound_effects_list_path), exist_ok=True)
                
                # Створюємо базову структуру файлу
                default_data = {"sound_effects": {}}
                
                with open(self.sound_effects_list_path, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, ensure_ascii=False, indent=2)
                
                if self.logger:
                    self.logger.info(f"Створено новий файл sound_effects_list.json: {self.sound_effects_list_path}")
                return True
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f"Помилка створення sound_effects_list.json: {e}")
            return False
    
    def read_sound_effects_list(self) -> Dict[str, Dict[str, str]]:
        """Прочитати з sound_effects_list.json"""
        try:
            if not os.path.exists(self.sound_effects_list_path):
                if self.logger:
                    self.logger.warning("Файл sound_effects_list.json не знайдено")
                return {}
            
            with open(self.sound_effects_list_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Повертаємо словник звукових ефектів
            return data.get("sound_effects", {})
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Помилка читання sound_effects_list.json: {e}")
            return {}
    
    def add_or_update_sound_effect(self, tag: str, description: str, file_path: str) -> bool:
        """Додати/оновити значення у sound_effects_list.json"""
        try:
            sound_effects = self.read_sound_effects_list()
            
            # Оновлюємо або додаємо запис
            sound_effects[tag] = {
                "description": description,
                "file_path": file_path
            }
            
            return self._save_sound_effects_list(sound_effects)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Помилка додавання/оновлення звукового ефекту {tag}: {e}")
            return False
    
    def delete_sound_effect(self, tag: str) -> bool:
        """Видалити вказане значення з sound_effects_list.json"""
        try:
            sound_effects = self.read_sound_effects_list()
            
            if tag in sound_effects:
                del sound_effects[tag]
                return self._save_sound_effects_list(sound_effects)
            else:
                if self.logger:
                    self.logger.warning(f"Тег {tag} не знайдено для видалення")
                return False
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Помилка видалення звукового ефекту {tag}: {e}")
            return False
    
    def sort_sound_effects_list(self) -> bool:
        """Відсортувати список ефектів за номером тегу"""
        try:
            sound_effects = self.read_sound_effects_list()
            
            # Сортуємо за номером тегу (S01, S02, S03, ...)
            def get_tag_number(tag):
                match = re.match(r'S(\d+)', tag.upper())
                return int(match.group(1)) if match else 0
            
            sorted_effects = dict(sorted(
                sound_effects.items(),
                key=lambda x: get_tag_number(x[0])
            ))
            
            return self._save_sound_effects_list(sorted_effects)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Помилка сортування sound_effects_list.json: {e}")
            return False
    
    def _save_sound_effects_list(self, sound_effects: Dict[str, Dict[str, str]]) -> bool:
        """Внутрішній метод для збереження списку звукових ефектів"""
        try:
            data = {"sound_effects": sound_effects}
            
            with open(self.sound_effects_list_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            if self.logger:
                self.logger.info(f"Збережено sound_effects_list.json: {len(sound_effects)} записів")
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Помилка збереження sound_effects_list.json: {e}")
            return False
    
    def get_sound_effect(self, tag: str) -> Optional[Dict[str, str]]:
        """Отримати інформацію про конкретний звуковий ефект"""
        sound_effects = self.read_sound_effects_list()
        return sound_effects.get(tag)
    
    def get_all_tags(self) -> List[str]:
        """Отримати список усіх тегів"""
        sound_effects = self.read_sound_effects_list()
        return list(sound_effects.keys())
    
    def tag_exists(self, tag: str) -> bool:
        """Перевірити, чи існує тег"""
        sound_effects = self.read_sound_effects_list()
        return tag in sound_effects
    
    def get_next_available_tag(self) -> str:
        """Отримати наступний доступний тег у форматі S01, S02, ... S99"""
        existing_tags = self.get_all_tags()
        used_numbers = []
        
        for tag in existing_tags:
            match = re.match(r'S(\d+)', tag.upper())
            if match:
                used_numbers.append(int(match.group(1)))
        
        next_number = 1
        while next_number in used_numbers and next_number < 100:  # Обмеження до S99
            next_number += 1
        
        if next_number >= 100:
            return "S99"  # Максимальний тег
        
        return f"S{next_number:02d}"  # Формат з ведучими нулями
