# -*- coding: utf-8 -*-
# /storage/emulated/0/a0_sb2_book_editors_suite/book_editors_suite/core/config_manager.py

"""
Менеджер конфігурації з автоматичним створенням проекту книги.
з копіюванням файлів мелодій та пауз
"""

import json
import re
import os
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

class ProjectManager:
    """Менеджер для створення структури проекту книги"""
    
    # Словник джерельних файлів для мелодій та пауз
    MELODY_SOURCE_FILES = {
        "PAUSE_4_mp3": "/storage/emulated/0/Documents/Inp_mp3/silence_0.4s.mp3",
        "PAUSE_7_mp3": "/storage/emulated/0/Documents/Inp_mp3/silence_0.7s.mp3",
        "PAUSE_1_mp3": "/storage/emulated/0/Documents/Inp_mp3/silence_1.0s.mp3",
        "PAUSE_2_mp3": "/storage/emulated/0/Documents/Inp_mp3/Pause_s2.mp3",
        "PAUSE_4_wav": "/storage/emulated/0/Documents/Inp_mp3/silence__0.4s.wav",
        "PAUSE_7_wav": "/storage/emulated/0/Documents/Inp_mp3/silence__0.7s.wav",
        "PAUSE_1_wav": "/storage/emulated/0/Documents/Inp_mp3/silence__1.0s.wav",
        "PAUSE_2_wav": "/storage/emulated/0/Documents/Inp_mp3/Pause_s2.wav",
        "MELODY_START_mp3": "/storage/emulated/0/Documents/Inp_mp3/MELODY_START.mp3",
        "MELODY_END_mp3": "/storage/emulated/0/Documents/Inp_mp3/MELODY_END.mp3",
        "MELODY_START_wav": "/storage/emulated/0/Documents/Inp_mp3/Початок_глави.wav",
        "MELODY_END_wav": "/storage/emulated/0/Documents/Inp_mp3/Завершення_глави.wav",
        "TEST_wav": "/storage/emulated/0/Documents/Inp_mp3/part_097.wav",
    }

    @staticmethod
    def copy_melody_files(project_path: str) -> None:
        """
        Копіює файли мелодій та пауз в папку проекту зі стандартними назвами.
        
        Args:
            project_path (str): Шлях до проекту
        """
        target_dir = f"{project_path}/inputs/input_melodu"
        
        # Створюємо папку призначення, якщо вона не існує
        os.makedirs(target_dir, exist_ok=True)
        
        # Словник для перейменування файлів у стандартні назви
        file_mapping = {
            # Паузи
            "PAUSE_4_mp3": "PAUSE_4.mp3",
            "PAUSE_7_mp3": "PAUSE_7.mp3", 
            "PAUSE_1_mp3": "PAUSE_1.mp3",
            "PAUSE_2_mp3": "PAUSE_2.mp3",
            "PAUSE_4_wav": "PAUSE_4.wav",
            "PAUSE_7_wav": "PAUSE_7.wav",
            "PAUSE_1_wav": "PAUSE_1.wav",
            "PAUSE_2_wav": "PAUSE_2.wav",
            
            # Мелодії
            "MELODY_START_mp3": "MELODY_START.mp3",
            "MELODY_END_mp3": "MELODY_END.mp3",
            "MELODY_START_wav": "MELODY_START.wav",
            "MELODY_END_wav": "MELODY_END.wav",
            
            # Тестовий файл
            "TEST_wav": "TEST.wav"
        }
        
        copied_files = []
        
        for source_key, target_name in file_mapping.items():
            source_path = ProjectManager.MELODY_SOURCE_FILES.get(source_key)
            
            if not source_path:
                print(f"Попередження: Не знайдено шлях для ключа {source_key}")
                continue
                
            if not os.path.exists(source_path):
                print(f"Попередження: Файл не існує {source_path}")
                continue
                
            target_path = os.path.join(target_dir, target_name)
            
            try:
                shutil.copy2(source_path, target_path)
                copied_files.append(target_name)
                print(f"Скопійовано: {source_path} -> {target_path}")
            except Exception as e:
                print(f"Помилка при копіюванні {source_path}: {e}")
        
        print(f"Успішно скопійовано {len(copied_files)} файлів мелодій до {target_dir}")

#-----create_project_structure-----
    @staticmethod
    def create_project_structure(project_name: str, input_text_path: str = None, 
                               base_path: str = "/storage/emulated/0/book_projects") -> str:
        """
        Створює структуру проекту книги.
        
        Args:
            project_name (str): Назва проекту
            input_text_path (str, optional): Шлях до вихідного текстового файлу
            base_path (str): Базова папка для проектів
            
        Returns:
            str: Шлях до конфігураційного файлу проекту
        """
        # Основні шляхи проекту
        project_path = f"{base_path}/{project_name}"
        config_file_path = f"{project_path}/json/{project_name}_config.json"
        
        # Створюємо структуру папок
        folders = [
            f"{project_path}",
            f"{project_path}/json",
            f"{project_path}/pluses",
            f"{project_path}/book_text_file",
            f"{project_path}/inputs",
            f"{project_path}/inputs/input_melodu",
            f"{project_path}/inputs/input_sounds_effects",
            f"{project_path}/outputs",
            f"{project_path}/outputs/output_mp3",
            f"{project_path}/outputs/output_multispeakers",
            f"{project_path}/temp_folder",
            f"{project_path}/temp_folder/logs"
        ]
        
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
            print(f"Створено папку: {folder}")
        
        # Копіюємо/створюємо текстовий файл
        text_file_path = f"{project_path}/book_text_file/{project_name}.txt"
        if input_text_path and os.path.exists(input_text_path):
            shutil.copy2(input_text_path, text_file_path)
            print(f"Скопійовано текстовий файл: {text_file_path}")
        else:
            # Створюємо порожній текстовий файл
            with open(text_file_path, 'w', encoding='utf-8') as f:
                f.write("# Вхідний текст проекту\n\n")
            print(f"Створено порожній текстовий файл: {text_file_path}")
        
        # Викликаємо метод для копіювання файлів мелодій
        ProjectManager.copy_melody_files(project_path)
        
        # Створюємо порожні базові JSON файли
        json_files = {
            f"{project_path}/json/accents_files.json": {"акцент": "на́голос"},
            f"{project_path}/json/sound_effects_list.json": {"sound_effects": {}},  # Нова структура
            f"{project_path}/json/sound_effects_files.json": {"sounds": {}}
        }
        
        for json_path, default_data in json_files.items():
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
            print(f"Створено JSON файл: {json_path}")
        
        # Створюємо конфігураційний файл проекту
        config = ProjectManager._create_project_config(project_path, project_name)
        
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"Створено конфігураційний файл: {config_file_path}")
        print(f"Структура проекту '{project_name}' успішно створена!")
        
        return config_file_path

#-----_create_project_config-----    
    @staticmethod
    def _create_project_config(project_path: str, project_name: str) -> Dict[str, Any]:
        """
        Створює конфігурацію проекту з правильними шляхами.
        """
        base_path = f"{project_path}"
        
        config = {
            "COMMON_CONFIG_VERSION": "0_0_0_3",
            "COMMON_TEXT_WIDGET_FONT_SIZE": 56,
            "COMMON_BBTN_FONT_SIZE": 38,
            "COMMON_BBTN_HEIGHT": 120,
            "COMMON_ACCENT_CHAR": "́",
            "COMMON_INPUT_TEXT_FILE": f"{base_path}/book_text_file/{project_name}.txt",
            "COMMON_OUTPUT_FOLDER": f"{base_path}/outputs",
            "COMMON_TEMP_FOLDER": f"{base_path}/temp_folder",
            "COMMON_VOICE_DICT": {
                "G1": "Розповідач",
                "G2": "Чоловік1", 
                "G3": "Чоловік2",
                "G4": "Жінка1",
                "G5": "Жінка2",
                "G6": "Хлопець",
                "G7": "Дівчина",
                "G8": "Думки чол",
                "G9": "Думки жін"
            },
            "COMMON_PAUSE_DICT": {
                "P4": "PAUSE_4",
                "P7": "PAUSE_7", 
                "P1": "PAUSE_1",
                "P2": "PAUSE_2"
            },
            
            # Конфіг для accent_editor
            "ACCENT_EDITOR_ACCENTS_FILE": f"{base_path}/json/accents_files.json",
            "ACCENT_EDITOR_OUTPUT_MP3_FOLDER": f"{base_path}/outputs/output_mp3",
            "ACCENT_EDITOR_TTS_MODE": "gTTS",
            "ACCENT_EDITOR_DO_SPLIT": False,
            "ACCENT_EDITOR_BOOKMARK": {
                "cursor": 0,
                "scroll": 0.0,
                "paragraph_index": 0
            },
            
            # Конфіг для voice_tags_editor
            "VOICE_TAGS_EDITOR_PAUSE_4_MP3": f"{base_path}/inputs/input_melodu/PAUSE_4.mp3",
            "VOICE_TAGS_EDITOR_PAUSE_7_MP3": f"{base_path}/inputs/input_melodu/PAUSE_7.mp3",
            "VOICE_TAGS_EDITOR_PAUSE_1_MP3": f"{base_path}/inputs/input_melodu/PAUSE_1.mp3",
            "VOICE_TAGS_EDITOR_PAUSE_2_MP3": f"{base_path}/inputs/input_melodu/PAUSE_2.mp3",
            "VOICE_TAGS_EDITOR_PAUSE_4_WAV": f"{base_path}/inputs/input_melodu/PAUSE_4.wav",
            "VOICE_TAGS_EDITOR_PAUSE_7_WAV": f"{base_path}/inputs/input_melodu/PAUSE_7.wav",
            "VOICE_TAGS_EDITOR_PAUSE_1_WAV": f"{base_path}/inputs/input_melodu/PAUSE_1.wav",
            "VOICE_TAGS_EDITOR_PAUSE_2_WAV": f"{base_path}/inputs/input_melodu/PAUSE_2.wav",
            "VOICE_TAGS_EDITOR_MELODY_START_MP3": f"{base_path}/inputs/input_melodu/MELODY_START.mp3",
            "VOICE_TAGS_EDITOR_MELODY_END_MP3": f"{base_path}/inputs/input_melodu/MELODY_END.mp3",
            "VOICE_TAGS_EDITOR_MELODY_START_WAV": f"{base_path}/inputs/input_melodu/MELODY_START.wav",
            "VOICE_TAGS_EDITOR_MELODY_END_WAV": f"{base_path}/inputs/input_melodu/MELODY_END.wav",
            "VOICE_TAGS_EDITOR_TEST_WAV": f"{base_path}/inputs/input_melodu/TEST.wav",
            "VOICE_TAGS_EDITOR_BOOKMARK": {
                "cursor": 0,
                "scroll": 0.0,
                "paragraph_index": 0
            },
            
            # Конфіг для sound_effects_editor 
            "SOUND_EFFECTS_EDITOR_SOUND_DICT": {
                "S01": "Звук_пострілу",
                "S02": "Машина_гальмує", 
                "S03": "Гарчання_мутанта"
            },
            "SOUND_EFFECTS_EDITOR_SOUNDS_EFFECTS_LIST": f"{base_path}/json/sound_effects_list.json",
            "SOUND_EFFECTS_EDITOR_SOUNDS_EFFECTS_FILES": f"{base_path}/json/sound_effects_files.json",
            "SOUND_EFFECTS_EDITOR_SOUNDS_EFFECTS_INPUT_FOLDER": f"{base_path}/inputs/input_sounds_effects",
            "SOUND_EFFECTS_EDITOR_BOOKMARK": {
                "cursor": 0,
                "scroll": 0.0,
                "paragraph_index": 0
            },
            
            # Конфіг для multispeaker_tts - 
  #zp==========
              
            "MULTISPEAKER_TTS_PAUSE_4_MP3": f"{base_path}/inputs/input_melodu/PAUSE_4.mp3",
            "MULTISPEAKER_TTS_PAUSE_7_MP3": f"{base_path}/inputs/input_melodu/PAUSE_7.mp3",
            "MULTISPEAKER_TTS_PAUSE_1_MP3": f"{base_path}/inputs/input_melodu/PAUSE_1.mp3",
            "MULTISPEAKER_TTS_PAUSE_2_MP3": f"{base_path}/inputs/input_melodu/PAUSE_2.mp3",
            "MULTISPEAKER_TTS_PAUSE_4_WAV": f"{base_path}/inputs/input_melodu/PAUSE_4.wav",
            "MULTISPEAKER_TTS_PAUSE_7_WAV": f"{base_path}/inputs/input_melodu/PAUSE_7.wav",
            "MULTISPEAKER_TTS_PAUSE_1_WAV": f"{base_path}/inputs/input_melodu/PAUSE_1.wav",
            "MULTISPEAKER_TTS_PAUSE_2_WAV": f"{base_path}/inputs/input_melodu/PAUSE_2.wav",
            "MULTISPEAKER_TTS_MELODY_START_MP3": f"{base_path}/inputs/input_melodu/MELODY_START.mp3",
            "MULTISPEAKER_TTS_MELODY_END_MP3": f"{base_path}/inputs/input_melodu/MELODY_END.mp3",
            "MULTISPEAKER_TTS_MELODY_START_WAV": f"{base_path}/inputs/input_melodu/MELODY_START.wav",
            "MULTISPEAKER_TTS_MELODY_END_WAV": f"{base_path}/inputs/input_melodu/MELODY_END.wav",
            "MULTISPEAKER_TTS_TEST_WAV": f"{base_path}/inputs/input_melodu/TEST.wav",

  #zd==========          
            
            "MULTISPEAKER_TTS_INPUT_SOUNDS_FOLDER": f"{base_path}/inputs/input_melodu",
                        "MULTISPEAKER_TTS_OUTPUTS_FOLDER": f"{base_path}/outputs/output_multispeakers",
            "MULTISPEAKER_TTS_FRAGMENT_SOFT_LIMIT": 900,
            "MULTISPEAKER_TTS_FRAGMENT_HARD_LIMIT": 1000,
            "MULTISPEAKER_TTS_DO_SPLIT": True,
            "MULTISPEAKER_TTS_DO_MERGE": False,
            "MULTISPEAKER_TTS_TTS_MODE": "TFile",
            "MULTISPEAKER_TTS_SOUND_DICT": {
                "S01": "Звук_пострілу",
                "S02": "Машина_гальмує", 
                "S03": "Гарчання_мутанта"
            },
            "MULTISPEAKER_TTS_SOUNDS_EFFECTS_LIST": f"{base_path}/json/sound_effects_list.json",
            "MULTISPEAKER_TTS_BOOKMARK": {
                "cursor": 0,
                "scroll": 0.0,
                "paragraph_index": 0
            }
        }     
        return config

#----project_exists-----
    @staticmethod
    def project_exists(project_name: str, base_path: str = "/storage/emulated/0/book_projects") -> bool:
        """Перевіряє, чи існує проект."""
        project_path = f"{base_path}/{project_name}"
        config_file = f"{project_path}/json/{project_name}_config.json"
        return os.path.exists(config_file)

#----get_project_config_path-----
    @staticmethod
    def get_project_config_path(project_name: str, base_path: str = "/storage/emulated/0/book_projects") -> str:
        """Повертає шлях до конфігураційного файлу проекту."""
        return f"{base_path}/{project_name}/json/{project_name}_config.json"

#===ModularConfigManager===
class ModularConfigManager:
    """
    Модульний менеджер конфігурації з підтримкою проектів книг.
    """

#----__init__-----
    def __init__(self, book_project_name: str, input_text_file: str = None):
        self.book_project_name = book_project_name
        self.input_text_file = input_text_file
        self.base_path = "/storage/emulated/0/book_projects"
        
        # Визначаємо шлях до конфігу проекту
        self.config_file = Path(ProjectManager.get_project_config_path(book_project_name, self.base_path))
        self.data = {}
        
        # Налаштування логування
        self.logger = self._setup_logging()

        # Спільні параметри
        self.common_params = {
            'params': [
                'CONFIG_VERSION',
                'TEXT_WIDGET_FONT_SIZE',
                'BBTN_FONT_SIZE',
                'BBTN_HEIGHT',
                'ACCENT_CHAR',
                'INPUT_TEXT_FILE',
                'OUTPUT_FOLDER',
                'TEMP_FOLDER',
                'VOICE_DICT',
                'PAUSE_DICT'
            ],
            'defaults': {
                'CONFIG_VERSION': '0_0_0_3',
                'TEXT_WIDGET_FONT_SIZE': 56,
                'BBTN_FONT_SIZE': 38,
                'BBTN_HEIGHT': 150,
                'ACCENT_CHAR': '\u0301',
                'INPUT_TEXT_FILE': '',
                'OUTPUT_FOLDER': '',
                'TEMP_FOLDER': '',
                'VOICE_DICT': {
                    "G1": "Розповідач",
                    "G2": "Чоловік1", 
                    "G3": "Чоловік2",
                    "G4": "Жінка1",
                    "G5": "Жінка2",
                    "G6": "Хлопець",
                    "G7": "Дівчина",
                    "G8": "Думки чол",
                    "G9": "Думки жін"
                },
                'PAUSE_DICT': {
                    "P4": "PAUSE_4",
                    "P7": "PAUSE_7", 
                    "P1": "PAUSE_1",
                    "P2": "PAUSE_2"
                },
            }
        }
        
        # Особисті параметри редакторів
        self.editor_registry = {
            'accent_editor': {
                'params': [
                    'ACCENTS_FILE',
                    'OUTPUT_MP3_FOLDER', 
                    'TTS_MODE', 
                    'DO_SPLIT',
                    'BOOKMARK'
                ],
                'defaults': {
                    'ACCENTS_FILE': '',
                    'OUTPUT_MP3_FOLDER': '',
                    'TTS_MODE': 'gTTS', 
                    'DO_SPLIT': False,
                    'BOOKMARK': {'cursor': 0, 'scroll': 0.0, 'paragraph_index': 0}
                }
            },
            'voice_tags_editor': {
                'params': [
                    'PAUSE_4_MP3',
                    'PAUSE_7_MP3', 
                    'PAUSE_1_MP3', 
                    'PAUSE_2_MP3',
                    'PAUSE_4_WAV',
                    'PAUSE_7_WAV', 
                    'PAUSE_1_WAV', 
                    'PAUSE_2_WAV',
                    "MELODY_START_MP3",
                    "MELODY_END_MP3",
                    "MELODY_START_WAV",
                    "MELODY_END_WAV",
                    "TEST_WAV",                    
                    'BOOKMARK'
                ],
                'defaults': {
                    "PAUSE_4_MP3": "",
                    "PAUSE_7_MP3": "",
                    "PAUSE_1_MP3": "",
                    "PAUSE_2_MP3": "",
                    "PAUSE_4_WAV": "",
                    "PAUSE_7_WAV": "",
                    "PAUSE_1_WAV": "",
                    "PAUSE_2_WAV": "",
                    "MELODY_START_MP3": "",
                    "MELODY_END_MP3": "",
                    "MELODY_START_WAV": "",
                    "MELODY_END_WAV": "",
                    "TEST_WAV": "",
                    'BOOKMARK': {'cursor': 0, 'scroll': 0.0, 'paragraph_index': 0}
                }
            },           
            'sound_effects_editor': {
                'params': [
                    'SOUNDS_EFFECTS_LIST', 
                    'SOUNDS_EFFECTS_FILES',
                    'SOUNDS_EFFECTS_INPUT_FOLDER',
                    'SOUND_DICT',
                    'BOOKMARK'
                ],
                'defaults': {
                    'SOUND_DICT': {
                        "S01": "Звук_пострілу", 
                        "S02": "Машина_гальмує", 
                        "S03": "Гарчання_мутанта"
                    },
                    'SOUNDS_EFFECTS_LIST': '',
                    'SOUNDS_EFFECTS_FILES': '',
                    'SOUNDS_EFFECTS_INPUT_FOLDER': '',
                    'BOOKMARK': {'cursor': 0, 'scroll': 0.0, 'paragraph_index': 0}
                }
            },
            'multispeaker_tts': {
                'params': [
                    'INPUT_SOUNDS_FOLDER',
                    'FRAGMENT_SOFT_LIMIT',
                    'FRAGMENT_HARD_LIMIT', 
                    'DO_SPLIT',
                    'DO_MERGE',
                    'TTS_MODE',
                    "SOUNDS_EFFECTS_LIST"
                    'SOUND_DICT',
                    'BOOKMARK'
                ],
                'defaults': {
                    'INPUT_SOUNDS_FOLDER': '',
                    'FRAGMENT_SOFT_LIMIT': 900,
                    'FRAGMENT_HARD_LIMIT': 1000,
                    'DO_SPLIT': True,
                    'DO_MERGE': False,
                    'TTS_MODE': 'TFile',
                    'SOUNDS_EFFECTS_LIST': '',
                    'SOUND_DICT': {
                        "S01": "Звук_пострілу",
                        "S02": "Машина_гальмує", 
                        "S03": "Гарчання_мутанта"
                    },
                    'BOOKMARK': {'cursor': 0, 'scroll': 0.0, 'paragraph_index': 0}
                }
            }
        }
        
        # Автоматичне створення проекту при ініціалізації
        self._auto_create_project()

#----_auto_create_project-----
    def _auto_create_project(self):
        """Автоматично створює проект, якщо він не існує."""
        try:
            if not ProjectManager.project_exists(self.book_project_name, self.base_path):
                self.logger.info(f"_auto_create_project: \nСтворення нового проекту: {self.book_project_name}\n")
                
                # Створюємо структуру проекту
                ProjectManager.create_project_structure(
                    project_name=self.book_project_name,
                    input_text_path=self.input_text_file,
                    base_path=self.base_path
                )
            
            # Завантажуємо конфіг
            self.load_full_config()
            self.logger.info(f"_auto_create_project: \nПроект {self.book_project_name} готовий до використання\n")
            
        except Exception as e:
            self.logger.error(f"_auto_create_project: Помилка створення проекту:\n {e}")
            raise

#----_setup_logging-----
    def _setup_logging(self):
        """Налаштовує логування для config_manager."""
        # Шлях до папки логів проекту
        log_dir = f"{self.base_path}/{self.book_project_name}/temp_folder/logs"
        os.makedirs(log_dir, exist_ok=True)
        
        logger = logging.getLogger('config_manager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            log_file = f"{log_dir}/config_manager.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            formatter = logging.Formatter(
                '\n%(asctime)s | %(levelname)-8s | %(name)s\n%(message)s\n',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
                
            logger.addHandler(file_handler)
            
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger

#----ensure_config-----
    def ensure_config(self):
        """Гарантує наявність конфігурації (для сумісності)."""
        # Проект вже створено в _auto_create_project
        pass

#----load_full_config-----
    def load_full_config(self) -> Dict[str, Any]:
        """Завантажує повний конфіг з файлу."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                self.logger.info(f"load_full_config: \nЗавантажено конфіг: {len(self.data)} параметрів")
            except Exception as e:
                self.logger.error(f"load_full_config: Помилка завантаження конфігу: {e}")
                self.data = {}
        return self.data

#----load_for_editor-----
    def load_for_editor(self, editor_name: str) -> Dict[str, Any]:
        """Завантажує тільки параметри потрібні конкретному редактору."""
        if editor_name not in self.editor_registry:
            error_msg = f"load_for_editor: Невідомий редактор: {editor_name}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        editor_config = {}
        
        # Завантажуємо спільні параметри
        for param in self.common_params['params']:
            common_key = f"COMMON_{param.upper()}"
            if common_key in self.data:
                editor_config[param] = self.data[common_key]
            elif param in self.common_params['defaults']:
                editor_config[param] = self.common_params['defaults'][param]
        
        # Завантажуємо особисті параметри редактора
        for param in self.editor_registry[editor_name]['params']:
            personal_key = f"{editor_name.upper()}_{param.upper()}"
            if personal_key in self.data:
                editor_config[param] = self.data[personal_key]
            elif param in self.editor_registry[editor_name]['defaults']:
                editor_config[param] = self.editor_registry[editor_name]['defaults'][param]
        
        self.logger.info(f"load_for_editor: Завантажено конфіг для {editor_name}: {len(editor_config)} параметрів")
        return editor_config

#----save_from_editor-----
    def save_from_editor(self, editor_name: str, editor_data: Dict[str, Any]):
        """Зберігає тільки особисті параметри від конкретного редактора."""
        if editor_name not in self.editor_registry:
            error_msg = f"save_from_editor: Невідомий редактор: {editor_name}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        updated_params = []
        
        for param, value in editor_data.items():
            if param in self.editor_registry[editor_name]['params']:
                personal_param = f"{editor_name.upper()}_{param.upper()}"
                self.data[personal_param] = value
                updated_params.append(personal_param)
        
        if updated_params:
            self.save_full_config()
            self.logger.info(f"save_from_editor: Оновлено особисті параметри {editor_name}: {len(updated_params)} параметрів")

#----save_full_config-----
    def save_full_config(self, data: Dict[str, Any] = None):
        """Зберігає повний конфіг у файл."""
        if data is not None:
            self.data = data
            
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"save_full_config: \nУспішно збережено конфіг: {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"save_full_config: \nПомилка збереження конфігу: {e}")
            return False

#----update_bookmark-----
    def update_bookmark(self, editor_name: str, cursor_pos: int, scroll_y: float, paragraph_index: int):
        """Оновлює закладку для конкретного редактора."""
        updates = {
            'BOOKMARK': {
                'cursor': int(cursor_pos),
                'scroll': float(scroll_y),
                'paragraph_index': int(paragraph_index)
            }
        }
        self.save_from_editor(editor_name, updates)
        self.logger.info(f"update_bookmark: \nОновлено закладку для {editor_name}: \nparagraph={paragraph_index}, cursor={cursor_pos}, scroll={scroll_y}\n")

#----get_bookmark-----
    def get_bookmark(self, editor_name: str) -> Dict[str, Any]:
        """Отримує закладку для конкретного редактора."""
        editor_config = self.load_for_editor(editor_name)
        bookmark = editor_config.get('BOOKMARK', {'cursor': 0, 'scroll': 0.0, 'paragraph_index': 0})
        return {
            'scroll_y': bookmark.get('scroll', 0.0),
            'cursor_pos': bookmark.get('cursor', 0),
            'paragraph_index': bookmark.get('paragraph_index', 0)
        }

#----get_common_param-----
    def get_common_param(self, param_name: str, default=None):
        """Отримує значення спільного параметра."""
        common_param = f"COMMON_{param_name.upper()}"
        return self.data.get(common_param, default)

#----get_project_info-----
    def get_project_info(self) -> Dict[str, Any]:
        """Повертає інформацію про поточний проект."""
        return {
            'project_name': self.book_project_name,  # Виправлено з 'name' на 'project_name'
            'config_path': str(self.config_file),
            'text_file': self.get_common_param('INPUT_TEXT_FILE', ''),
            'base_path': self.base_path
        }


# Синглтон для глобального доступу
_global_config_manager = None

#----get_config_manager-----
def get_config_manager(book_project_name: str = None, input_text_file: str = None) -> ModularConfigManager:
    """Повертає глобальний екземпляр менеджера конфігурації."""
    global _global_config_manager
    if _global_config_manager is None and book_project_name:
        _global_config_manager = ModularConfigManager(book_project_name, input_text_file)
    return _global_config_manager

#----reset_config_manager-----
def reset_config_manager():
    """Скидає глобальний екземпляр менеджера конфігурації."""
    global _global_config_manager
    _global_config_manager = None

__all__ = ['ModularConfigManager', 'ProjectManager', 'get_config_manager', 'reset_config_manager']