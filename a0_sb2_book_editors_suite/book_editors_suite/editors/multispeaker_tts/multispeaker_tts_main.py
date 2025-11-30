#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Автономний MultispeakerTTS для Pydroid 3
Працює без залежності від графічного інтерфейсу
"""

import os
import sys
import json
import re
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# TTS
try:
    from gtts import gTTS
except:
    gTTS = None

try:
    from pydub import AudioSegment
except:
    AudioSegment = None


class SimpleConfigManager:
    """Спрощений менеджер конфігурації без залежностей"""
    
    def __init__(self, book_project_name: str, input_text_file: str = None):
        self.book_project_name = book_project_name
        self.base_path = "/storage/emulated/0/book_projects"
        self.project_path = f"{self.base_path}/{book_project_name}"
        self.config_file = f"{self.project_path}/json/{book_project_name}_config.json"
        
        # Перевіряємо чи існує проект
        if not os.path.exists(self.config_file):
            print(f"Помилка: Проект {book_project_name} не знайдено!")
            sys.exit(1)
            
        # Завантажуємо конфіг
        with open(self.config_file, 'r', encoding='utf-8') as f:
            self.full_config = json.load(f)
    
    def load_for_editor(self, editor_name: str) -> Dict:
        """Завантажує конфігурацію для конкретного редактора"""
        editor_config = {}
        
        # Спільні параметри
        common_params = [
            'CONFIG_VERSION',
            'TEXT_WIDGET_FONT_SIZE',
            'BBTN_FONT_SIZE',
            'BBTN_HEIGHT',
            'ACCENT_CHAR',
            'INPUT_TEXT_FILE',
     #       'OUTPUT_FOLDER',
      #      'TEMP_FOLDER',
            'VOICE_DICT',
            'PAUSE_DICT'
        ]
        
        for param in common_params:
            common_key = f"COMMON_{param}"
            if common_key in self.full_config:
                editor_config[param] = self.full_config[common_key]
        
        # Особисті параметри редактора
        editor_prefix = editor_name.upper() + "_"
        for key, value in self.full_config.items():
            if key.startswith(editor_prefix):
                param_name = key[len(editor_prefix):]
                editor_config[param_name] = value
        
        return editor_config
    
    def get_project_info(self) -> Dict:
        """Повертає інформацію про проект"""
        return {
            'project_name': self.book_project_name,
            'config_path': self.config_file,
            'base_path': self.base_path
        }


class SimpleLoggingManager:
    """Спрощений менеджер логування"""
    
    def __init__(self, log_dir: str, app_name: str = "app"):
        self.log_dir = Path(log_dir)
        self.app_name = app_name
        self.setup_logging()
    
    def setup_logging(self):
        """Налаштовує логування"""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            log_file = self.log_dir / f"{self.app_name}.log"
            
            # Налаштування базового логування
            logging.basicConfig(
                level=logging.INFO,
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ],
                format='\n%(asctime)s - %(levelname)s - \n%(message)s\n',
                datefmt='%d-%m-%Y %H:%M:%S'
            )
            
            self.logger = logging.getLogger(self.app_name)
            self.info(f"{self.app_name} запущено")
            self.info(f"Лог-файл: {log_file}")
            
        except Exception as e:
            print(f"Помилка налаштування логування: {e}")
            # Резервний логер
            self.logger = logging.getLogger(f"{self.app_name}_fallback")
    
    def info(self, message: str):
        """Запис інформаційного повідомлення"""
        if hasattr(self, 'logger'):
            self.logger.info(message)
        else:
            print(f"INFO: \n{message}\n")
    
    def error(self, message: str):
        """Запис повідомлення про помилку"""
        if hasattr(self, 'logger'):
            self.logger.error(message)
        else:
            print(f"ERROR: \n{message}\n")
    
    def warning(self, message: str):
        """Запис попереджувального повідомлення"""
        if hasattr(self, 'logger'):
            self.logger.warning(message)
        else:
            print(f"WARNING: \n{message}\n")
    
    def debug(self, message: str):
        """Запис відлагоджувального повідомлення"""
        if hasattr(self, 'logger'):
            self.logger.debug(message)
        else:
            print(f"DEBUG: \n{message}\n")


class MultispeakerTTS:
    """Мультиспікер TTS для створення аудіокниг з підготованого тексту"""
    
    def __init__(self, book_project_name: str, input_text_file: str = None):
        self.book_project_name = book_project_name
        self.input_text_file = input_text_file
        
        # Ініціалізація менеджерів
        self.config_manager = SimpleConfigManager(book_project_name, input_text_file)
        self.config = self.config_manager.load_for_editor('multispeaker_tts')
        
        # Налаштування логування
        project_info = self.config_manager.get_project_info()
        log_dir = project_info['base_path'] + f"/{book_project_name}/temp_folder/logs"
        self.logger = SimpleLoggingManager(log_dir, app_name="multispeaker_tts")
        
        # Внутрішні змінні
        self._project_root = None
        self._temp_folder = None
        self._current_fragment_counter = 0
        self._current_block_text = []
        self._current_voice_tag = None
        self._current_voice_speed = "normal"
        self._current_chapter_folder = None
        self._current_text_folder = None
        self._current_audio_folder = None
        self._current_chapter_name_for_files = None
        
        # Ініціалізація параметрів з конфігу
        self._init_from_config()
        
        self.logger.info(f"MultispeakerTTS: Ініціалізовано для проекту {book_project_name}")

    def _init_from_config(self):
        """Ініціалізація параметрів з конфігурації"""
        # Отримуємо параметри з конфігу
        self.INPUT_FILE = Path(self.config.get('INPUT_TEXT_FILE', ''))
        
        # Використовуємо MULTISPEAKER_TTS_OUTPUTS_FOLDER, MULTISPEAKER_TTS_TEMP_FOLDER, INPUT_MELODY_FOLDER та INPUT_SOUNDS_EFFECTS_FOLDER з конфігу
        self.OUTPUT_FOLDER = Path(self.config.get('OUTPUTS_FOLDER', self.config.get('OUTPUT_FOLDER', '')))
        self.TEMP_FOLDER = Path(self.config.get('TEMP_FOLDER', ''))
        self.INPUT_MELODY_FOLDER = Path(self.config.get('INPUT_MELODY_FOLDER', ''))
        self.INPUT_SOUNDS_EFFECTS_FOLDER = Path(self.config.get('INPUT_SOUNDS_EFFECTS_FOLDER', ''))
 
        
        # Словники
        self.voice_dict = self.config.get('VOICE_DICT', {})
        self.pause_dict = self.config.get('PAUSE_DICT', {})
        self.sound_dict = self.config.get('SOUND_DICT', {})
        
        # Параметри обробки
        self.TTS_MODE = self.config.get('TTS_MODE', 'TFile')
        self.DO_SPLIT = self.config.get('DO_SPLIT', True)
        self.DO_MERGE = self.config.get('DO_MERGE', False)
        self.FRAGMENT_SOFT_LIMIT = self.config.get('FRAGMENT_SOFT_LIMIT', 900)
        self.FRAGMENT_HARD_LIMIT = self.config.get('FRAGMENT_HARD_LIMIT', 1000)
        self.SOUNDS_MODE = "mp3" if self.TTS_MODE == "gTTS" else "wav"
        
        # Шляхи до звукових файлів з конфігу
        self.PAUSE_4_MP3 = self.config.get('PAUSE_4_MP3', '')
        self.PAUSE_7_MP3 = self.config.get('PAUSE_7_MP3', '')
        self.PAUSE_1_MP3 = self.config.get('PAUSE_1_MP3', '')
        self.PAUSE_2_MP3 = self.config.get('PAUSE_2_MP3', '')
        self.MELODY_START_MP3 = self.config.get('MELODY_START_MP3', '')
        self.MELODY_END_MP3 = self.config.get('MELODY_END_MP3', '')
        self.TEST_WAV = self.config.get('TEST_WAV', '')
        
        # Завантажуємо додаткові дані звукових ефектів
        self.scenarios = self._load_scenarios_json()

    def _load_scenarios_json(self) -> dict:
        """Завантажує JSON зі сценаріями звукових ефектів"""
        sounds_effects_list = self.config.get('SOUNDS_EFFECTS_LIST', '')
        if not sounds_effects_list or not os.path.exists(sounds_effects_list):
            self.logger.warning("MultispeakerTTS: Файл сценаріїв звукових ефектів не знайдено")
            return {}
        
        try:
            with open(sounds_effects_list, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Спроба різних форматів файлу
            if 'scenarios_dict' in data:
                scenarios = data.get('scenarios_dict', {})
            elif 'sound_effects' in data:
                scenarios = data.get('sound_effects', {})
            else:
                scenarios = data
                
            return {str(k).upper(): str(v) for k, v in scenarios.items()}
        except Exception as e:
            self.logger.error(f"MultispeakerTTS: Помилка завантаження JSON звукових ефектів: {e}")
            return {}

    # ---------- Утиліти ----------
    def ensure_folder(self, path):
        """Створює папку якщо не існує"""
        Path(path).mkdir(parents=True, exist_ok=True)

    def sanitize_chapter_folder_name(self, s: str) -> str:
        """Очищує назву глави для використання в іменах папок"""
        s2 = re.sub(r"^##\s*", "", s)
        s2 = re.sub(r"#g\d+(?:_(slow|fast))?:", "", s2, flags=re.IGNORECASE)
        s2 = re.sub(r"#S\d+:", "", s2, flags=re.IGNORECASE)
        s2 = s2.strip()
        s2 = s2.replace('\u0301', '')
        s2 = s2.replace("'", '')
        s2 = s2.replace(' ', '_')
        s2 = s2.replace(',', '')
        s2 = s2.replace('.', '')
        s2 = s2.replace('+', '')
        s2 = re.sub(r"[\\/:*?\"<>|]", "_", s2)
        
        if not s2:
            s2 = "Глава"
            
        self.logger.info(f"MultispeakerTTS: Назва глави: '{s2}'")
        return s2

    def sanitize_chapter_fragment_title(self, s: str) -> str:
        """Очищує назву глави для фрагментів"""
        s2 = re.sub(r"^##\s*", "", s)
        s2 = re.sub(r"#g\d+(?:_(slow|fast))?:", "", s2, flags=re.IGNORECASE)
        s2 = re.sub(r"#S\d+:", "", s2, flags=re.IGNORECASE)
        return s2.strip()

    def format_fragment_filename(self, chapter_name: str, num: int, ext: str) -> str:
        """Форматує ім'я файлу фрагмента"""
        return f"{chapter_name}_фр_{num:04d}.{ext}"

    # ---------- TTS генерація ----------
    def tts_generate_gtts(self, text: str, out_path: Path, lang: str = 'uk') -> bool:
        """Генерація TTS через gTTS"""
        if gTTS is None:
            self.logger.error("MultispeakerTTS: gTTS не встановлено")
            return False
        try:
            gTTS(text=text, lang=lang).save(str(out_path))
            return True
        except Exception as e:
            self.logger.error(f"MultispeakerTTS: gTTS помилка: {e}")
            return False

    def tts_generate_tfile(self, text: str, out_path: Path) -> bool:
        """Генерація TTS через тестовий файл (для тестування)"""
        if not self.TEST_WAV or not os.path.exists(self.TEST_WAV):
            self.logger.error("MultispeakerTTS: Тестовий WAV файл не знайдено")
            return False
            
        try:
            shutil.copyfile(self.TEST_WAV, str(out_path))
            return True
        except Exception as e:
            self.logger.error(f"MultispeakerTTS: TFile помилка: {e}")
            return False

    def tts_generate_stylets2(self, text: str, out_path: Path, voice_tag: str) -> bool:
        """Заглушка для StyleTTS2"""
        self.logger.info(f"StyleTTS2: потрібно реалізувати реальний TTS (голос: {voice_tag})")
        return False

    # ---------- Збереження фрагмента ----------
    def save_fragment_and_tts(self, fragment_text: str, voice_tag: str, speed: str, 
                            chapter_folder_name: str, fragment_num: int) -> Tuple[bool, Optional[Path]]:
        """Зберігає текст фрагмента і генерує аудіо"""
        if self._current_text_folder is None or self._current_audio_folder is None:
            self.logger.error("MultispeakerTTS: Папки не ініціалізовані")
            return False, None

        # Зберігаємо текст
        txt_name = self.format_fragment_filename(chapter_folder_name, fragment_num, 'txt')
        txt_path = self._current_text_folder / txt_name
        try:
            with txt_path.open('w', encoding='utf-8') as f:
                f.write(fragment_text)
            self.logger.info(f"MultispeakerTTS: Збережено текст: {txt_path}")
        except Exception as e:
            self.logger.error(f"MultispeakerTTS: Помилка збереження txt: {e}")
            return False, None

        # Генеруємо аудіо
        audio_name = self.format_fragment_filename(chapter_folder_name, fragment_num, self.SOUNDS_MODE)
        audio_path = self._current_audio_folder / audio_name

        success = False
        if self.TTS_MODE == 'gTTS':
            success = self.tts_generate_gtts(fragment_text, audio_path)
        elif self.TTS_MODE == 'TFile':
            success = self.tts_generate_tfile(fragment_text, audio_path)
        elif self.TTS_MODE == 'StyleTTS2':
            success = self.tts_generate_stylets2(fragment_text, audio_path, voice_tag)
        else:
            self.logger.error(f"Невідомий режим TTS: {self.TTS_MODE}")         

        if success:
            self.logger.info(f"MultispeakerTTS: Фрагмент озвучено: {audio_path} (голос: {voice_tag}, швидкість: {speed})")
            self._current_fragment_counter += 1
            return True, audio_path
        else:
            self.logger.error(f"MultispeakerTTS: Не вдалося озвучити фрагмент #{fragment_num}")
            return False, None

# ===========================
# Додавання пауз та звукових ефектів
# ===========================

    def add_sound_or_pause(self, tag: str, chapter_folder: Path) -> Optional[Path]:
        """Додає звуковий ефект або паузу"""
        audio_folder = chapter_folder / "Звук"
        self.ensure_folder(audio_folder)
        
        out_path = audio_folder / self.format_fragment_filename(chapter_folder.name, self._current_fragment_counter, self.SOUNDS_MODE)
        #шукаємо в папці звуків
        
        if tag in self.pause_dict:
        	
        	pause_inp_name = f"{self.pause_dict[tag]}.{self.SOUNDS_MODE}"
        	pause_inp_path = self.INPUT_MELODY_FOLDER / pause_inp_name
        	if pause_inp_path.exists():
        	           shutil.copy2(str(pause_inp_path), str(out_path))
        	           self.logger.info(f"MultispeakerTTS: Додано паузу: {tag} -> \n{pause_inp_path}")
        	           self._current_fragment_counter += 1
        	else:
        	           self.logger.warning(f"MultispeakerTTS: Файл паузи не знайдено: \n{self.INPUT_MELODY_FOLDER} \n{pause_inp_path}")

        elif tag.startswith('S') and tag[1:].isdigit():
            # Звуковий ефект з тегу S01, S02, etc.
            sound_tag_upper = tag.upper()
            sound_effect_name = f"{sound_tag_upper}.{self.SOUNDS_MODE}"
            sound_inp_path = self.INPUT_SOUNDS_EFFECTS_FOLDER / sound_effect_name

            if sound_inp_path.exists():
                shutil.copyfile(str(sound_inp_path), str(out_path))
                self._current_fragment_counter += 1
                self.logger.info(f"MultispeakerTTS: Додано звуковий ефект: {tag} -> {out_path}")
            else:
                self.logger.warning(f"MultispeakerTTS: Файл звукового ефекту не знайдено: \n{self.INPUT_SOUNDS_EFFECTS_FOLDER} \n{sound_inp_path}")
        
        
        return out_path

# ===========================
# Мелодії початок і кінець глави
# ===========================

    def add_melody(self, chapter_folder: Path,  kind="START"):
        """Додає мелодію початку або завершення"""
        audio_folder = chapter_folder / "Звук"
        self.ensure_folder(audio_folder)
        
        melody_filename = f"MELODY_{kind}.{self.SOUNDS_MODE}"
        out_path = audio_folder / self.format_fragment_filename(chapter_folder.name, self._current_fragment_counter, self.SOUNDS_MODE)
        #шукаємо в папці звуків
        melody_inp_path = self.INPUT_MELODY_FOLDER / melody_filename
        if melody_inp_path.exists():
                shutil.copyfile(str(melody_inp_path), str(out_path))
                self._current_fragment_counter += 1
                self.logger.info(f"MultispeakerTTS: Додано мелодію {kind}: \n{out_path}")
        else:
        	self.logger.warning(f"MultispeakerTTS: Файл мелодії не знайдено: \n{self.INPUT_MELODY_FOLDER} \n{melody_inp_path}")
        
        return out_path

    # ---------- Управління главами та блоками ----------
    def init_project_root(self) -> Path:
        """Ініціалізує кореневу папку проекту"""
        input_name = Path(self.INPUT_FILE).stem
        
        # Використовуємо MULTISPEAKER_TTS_OUTPUTS_FOLDER як основну папку
   #     project_root = Path(self.OUTPUT_FOLDER) / input_name
        project_root = Path(self.OUTPUT_FOLDER)
        self.ensure_folder(project_root)
        
        self._project_root = project_root
        
        # Використовуємо MULTISPEAKER_TTS_TEMP_FOLDER для тимчасових файлів
        if self.TEMP_FOLDER:
            self._temp_folder = Path(self.TEMP_FOLDER)
            self.ensure_folder(self._temp_folder)
        else:
            self._temp_folder = project_root / "temp_multispeakers"
            self.ensure_folder(self._temp_folder)
        
        self.logger.info(f"MultispeakerTTS: Ініціалізовано проєкт: {self._project_root}")
        return project_root

    def start_new_chapter(self, raw_chapter_line: str):
        """Починає нову главу"""
        chapter_folder_name = self.sanitize_chapter_folder_name(raw_chapter_line)
        chapter_fragment_title = self.sanitize_chapter_fragment_title(raw_chapter_line)

        self._current_chapter_folder = self._project_root / chapter_folder_name
        self.ensure_folder(self._current_chapter_folder)
        self._current_text_folder = self._current_chapter_folder / "Текст"
        self._current_audio_folder = self._current_chapter_folder / "Звук"
        self.ensure_folder(self._current_text_folder)
        self.ensure_folder(self._current_audio_folder)

        self._current_fragment_counter = 0
        self._current_block_text = []
        self._current_voice_tag = 'G1'  # голос за замовчуванням
        self._current_voice_speed = "normal"  # швидкість за замовчуванням

        # Шукаємо тег голосу з швидкістю
        voice_match = re.search(r"#g(\d+)(?:_(slow|fast))?:", raw_chapter_line, re.IGNORECASE)
        if voice_match:
            self._current_voice_tag = f"G{voice_match.group(1)}"
            self._current_voice_speed = voice_match.group(2) if voice_match.group(2) else "normal"

        self._current_chapter_name_for_files = chapter_folder_name
        
        # Додати мелодію початку
        self.add_melody(self._current_chapter_folder, "START")
        
        # Перший фрагмент починається з назви глави
        if chapter_fragment_title:
            self._current_block_text.append(chapter_fragment_title)
        
        self.logger.info(f"MultispeakerTTS: Почато нову главу: {self._current_chapter_folder} (голос: {self._current_voice_tag}, швидкість: {self._current_voice_speed})")

    def start_new_voice_block(self, line_with_tag: str):
        """Починає новий блок з іншим голосом"""
        # Зберегти поточний блок
        cur_text = '\n'.join(self._current_block_text).strip()
        if cur_text and self._current_voice_tag:
            self.save_fragment_and_tts(cur_text, self._current_voice_tag, self._current_voice_speed,
                                    self._current_chapter_name_for_files, self._current_fragment_counter)
        
        # Очистити поточний блок
        self._current_block_text = []
        
        # Шукаємо тег голосу з швидкістю
        voice_match = re.search(r"#g(\d+)(?:_(slow|fast))?:", line_with_tag, re.IGNORECASE)
        if voice_match:
            self._current_voice_tag = f"G{voice_match.group(1)}"
            self._current_voice_speed = voice_match.group(2) if voice_match.group(2) else "normal"
            
            # Додаємо текст після тегу
            after = re.sub(r"^.*#g\d+(?:_(slow|fast))?:", "", line_with_tag, flags=re.IGNORECASE).strip()
            if after:
                self._current_block_text.append(after)
        else:
            self.logger.warning(f"MultispeakerTTS: Не знайдено тегу голосу в рядку: {line_with_tag}")

    def process_sound_effect_tag(self, line_with_tag: str):
        """Обробляє тег звукового ефекту (#S01:, #S02:, etc.)"""
        sound_match = re.search(r"#(S\d+):", line_with_tag, re.IGNORECASE)
        if sound_match:
            sound_tag = sound_match.group(1).upper()
            # Додаємо звуковий ефект як окремий фрагмент
            self.add_sound_or_pause(sound_tag, self._current_chapter_folder)
            
            # Можна додати текст після тегу звукового ефекту
            after = re.sub(r"^.*#S\d+:", "", line_with_tag, flags=re.IGNORECASE).strip()
            if after:
                self._current_block_text.append(after)

    def append_line_to_block(self, line: str):
        """Додає рядок до поточного блоку"""
        stripped = line.rstrip('\n')
        
        # Перевіряємо на тег звукового ефекту
        if re.search(r"#S\d+:", stripped, re.IGNORECASE):
            self.process_sound_effect_tag(stripped)
            return
            
        # Порожній рядок - пауза
        if stripped.strip() == "":
            cur_text = '\n'.join(self._current_block_text).strip()
            if cur_text:
                self.save_fragment_and_tts(cur_text, self._current_voice_tag, self._current_voice_speed,
                                        self._current_chapter_name_for_files, self._current_fragment_counter)
                # Додати паузу
                self.add_sound_or_pause("P2", self._current_chapter_folder)
            self._current_block_text = []
            return

        cur_text = '\n'.join(self._current_block_text)
        cur_len = len(cur_text)

        if cur_len + 1 + len(stripped) <= self.FRAGMENT_HARD_LIMIT:
            self._current_block_text.append(stripped)
            if len('\n'.join(self._current_block_text)) >= self.FRAGMENT_SOFT_LIMIT:
                self.save_fragment_and_tts('\n'.join(self._current_block_text).strip(), 
                                        self._current_voice_tag, self._current_voice_speed,
                                        self._current_chapter_name_for_files, self._current_fragment_counter)
                self._current_block_text = []
        else:
            if cur_text.strip():
                self.save_fragment_and_tts(cur_text.strip(), self._current_voice_tag, self._current_voice_speed,
                                        self._current_chapter_name_for_files, self._current_fragment_counter)
            self._current_block_text = [stripped]

    def finalize_chapter(self):
        """Завершує обробку поточної глави"""
        if self._current_chapter_name_for_files is None:
            self.logger.debug("MultispeakerTTS: Нема відкритої глави")
            return
            
        if self._current_block_text and self._current_voice_tag:
            fragment_text = '\n'.join(self._current_block_text).strip()
            if fragment_text:
                self.save_fragment_and_tts(fragment_text, self._current_voice_tag, self._current_voice_speed,
                                        self._current_chapter_name_for_files, self._current_fragment_counter)
        
        # Додати мелодію завершення
        self.add_melody(self._current_chapter_folder, "END")
        
        self.logger.info(f"MultispeakerTTS: \nГлава '{self._current_chapter_name_for_files}' завершена. \nФрагментів: {self._current_fragment_counter}")
        self._current_block_text = []
        self._current_voice_tag = None

    def merge_chapter_audio(self, chapter_folder: Path):
        """Об'єднує всі звукові фрагменти глави в один файл"""
        if AudioSegment is None:
            self.logger.error("MultispeakerTTS: pydub не встановлено — не можу об'єднати аудіо.")
            return
            
        sound_folder = chapter_folder / "Звук"
        if not sound_folder.exists():
            self.logger.warning(f"MultispeakerTTS: Папки зі звуком немає: {sound_folder}")
            return
            
        fragments = sorted([f for f in os.listdir(sound_folder) if f.endswith(f".{self.SOUNDS_MODE}")])
        if not fragments:
            self.logger.warning("MultispeakerTTS: Немає фрагментів для об'єднання.")
            return
            
        combined = None
        for f in fragments:
            try:
                seg = AudioSegment.from_file(str(sound_folder / f))
                combined = seg if combined is None else combined + seg
            except Exception as e:
                self.logger.warning(f"MultispeakerTTS: Помилка завантаження фрагменту {f}: {e}")
                
        if combined:
            out_file = sound_folder / f"{chapter_folder.name}_повна.{self.SOUNDS_MODE}"
            combined.export(str(out_file), format=self.SOUNDS_MODE)
            self.logger.info(f"MultispeakerTTS: Об'єднано аудіо: {out_file}")

    # ---------- Основний процес ----------
    def process_input_file(self):
        """Основний процес обробки вхідного файлу"""
        self.init_project_root()

        if not self.DO_SPLIT:
            self.logger.info("MultispeakerTTS: DO_SPLIT=False — розбиття відключено.")
            return

        with open(self.INPUT_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        in_chapter = False
        for raw_line in lines:
            line = raw_line.rstrip('\n')
            
            # Початок глави
            if line.strip().startswith('##'):
                if in_chapter:
                    self.finalize_chapter()
                self.start_new_chapter(line)
                in_chapter = True
                continue
                
            # Тег голосу
            if re.search(r"#g\d+(?:_(slow|fast))?:", line, re.IGNORECASE):
                self.start_new_voice_block(line)
                continue
                
            # Рядок поза главою
            if not in_chapter:
                self.logger.debug(f"MultispeakerTTS: Рядок поза главою ігнорується: {line}")
                continue
                
            # Додаємо рядок у блок
            self.append_line_to_block(line)

        if in_chapter:
            self.finalize_chapter()

        if self.DO_MERGE:
            for chapter_dir in self._project_root.iterdir():
                if chapter_dir.is_dir():
                    self.merge_chapter_audio(chapter_dir)

        self.logger.info("MultispeakerTTS: Обробка файлу завершена.")

    def run(self):
        """Головний метод запуску"""
        if not self.INPUT_FILE.exists():
            self.logger.error(f"MultispeakerTTS: Вхідний файл не знайдено: {self.INPUT_FILE}")
            return False
            
        self.ensure_folder(self.OUTPUT_FOLDER)
        self.logger.info(f"MultispeakerTTS: Запуск: \nTTS_MODE={self.TTS_MODE}, \nSOUNDS_MODE={self.SOUNDS_MODE}")
        self.logger.info(f"MultispeakerTTS: Вхідний файл: {self.INPUT_FILE}")
        self.logger.info(f"MultispeakerTTS: Вихідна папка: {self.OUTPUT_FOLDER}")
        
        try:
            self.process_input_file()
            self.logger.info("MultispeakerTTS: Обробка завершена успішно")
            return True
        except Exception as e:
            self.logger.error(f"MultispeakerTTS: Критична помилка при обробці: {e}")
            return False


# ========== Запуск ==========
if __name__ == "__main__":
    input_text_file = "/storage/emulated/0/Documents/Inp_txt/доповнення13_у_нас_гості.txt"
    book_project_name = "доповнення13_у_нас_гості"

    print("=" * 30)
    print("MultispeakerTTS - Автономна версія для Pydroid 3")
    print("=" * 30)
    
    multispeaker = MultispeakerTTS(
        book_project_name=book_project_name,
        input_text_file=input_text_file
    )
    
    success = multispeaker.run()
    if success:
        print("✅ MultispeakerTTS: Обробка завершена успішно!")
    else:
        print("❌ MultispeakerTTS: Обробка завершена з помилками!")