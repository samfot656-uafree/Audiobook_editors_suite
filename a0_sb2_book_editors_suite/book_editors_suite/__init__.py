# -*- coding: utf-8 -*-
"""
/storage/emulated/0/a0_sb2_book_editors_suite/book_editors_suite/__init__.py

Головний пакет Book Editors Suite.
"""

__version__ = "1.0.0"
__author__ = "Book Editors Suite Team"

# Імпорти для зручності
from .core.config_manager import get_config_manager, ModularConfigManager
from .core.tts_manager import TTSManager
from .utils.helpers import (
    strip_combining_acute, 
    match_casing, 
    get_clock_str, 
    get_battery_percent,
    sanitize_filename,
    WORD_RE
)

__all__ = [
    'get_config_manager',
    'ModularConfigManager', 
    'TTSManager',
    'strip_combining_acute',
    'match_casing',
    'get_clock_str',
    'get_battery_percent',
    'sanitize_filename',
    'WORD_RE'
]


# book_editors_suite/__init__.py
#"""
#Book Editors Suite - комплекс редакторів для підготовки аудіокниг
#Головний пакет проекту
#"""

#__version__ = "1.0.0"
#__author__ = "Your Name"

# Імпортуємо тільки те, що реально існує
#from .core.config_manager import ModularConfigManager, get_config_manager, reset_config_manager

# Список доступних редакторів
#AVAILABLE_EDITORS = [
#    'accent_editor',
#    'voice_tags_editor', 
#    'sound_effects_editor',
#    'multispeaker_tts'
#]

#__all__ = [
#    'ModularConfigManager',
#    'get_config_manager',
#    'reset_config_manager',
#    'AVAILABLE_EDITORS'
#]


# book_editors_suite/__init__.py
#"""
#Book Editors Suite - комплекс редакторів для підготовки аудіокниг
#Головний пакет проекту
#"""

#__version__ = "1.0.0"
#__author__ = "Your Name"

# Імпорт основних компонентів для зручного доступу
#from .core.config_manager import ModularConfigManager, get_config_manager, reset_config_manager
#from .core.tts_manager import TTSManager
#from .core.text_processor import TextProcessor
#from .core.file_manager import FileManager

# Список доступних редакторів
#AVAILABLE_EDITORS = [
#    'accent_editor',
#    'voice_tags_editor', 
#    'sound_effects_editor',
#    'multispeaker_tts'
#]

#__all__ = [
#    'ModularConfigManager',
#    'get_config_manager',
#    'reset_config_manager',
#    'TTSManager', 
#    'TextProcessor',
#    'FileManager',
#    'AVAILABLE_EDITORS'
#]

# book_editors_suite/__init__.py
#"""
#Book Editors Suite - комплекс редакторів для підготовки аудіокниг
#Головний пакет проекту
#"""

#__version__ = "1.0.0"
#__author__ = "Your Name"

# Імпорт основних компонентів для зручного доступу
#from core.config_manager import ModularConfigManager, get_config_manager, reset_config_manager
#from core.tts_manager import TTSManager
#from core.text_processor import TextProcessor
#from core.file_manager import FileManager

# Список доступних редакторів
#AVAILABLE_EDITORS = [
#    'accent_editor',
#    'voice_tags_editor', 
#    'sound_effects_editor',
#    'multispeaker_tts'
#]

#__all__ = [
#    'ModularConfigManager',
#    'get_config_manager',
#    'reset_config_manager',
#    'TTSManager', 
#    'TextProcessor',
#    'FileManager',
#    'AVAILABLE_EDITORS'
#]


# book_editors_suite/__init__.py
#"""
#Book Editors Suite - комплекс редакторів для підготовки аудіокниг
#Головний пакет проекту
#"""

#__version__ = "1.0.0"
#__author__ = "Your Name"

# Імпорт основних компонентів для зручного доступу
#from core.config_manager import ModularConfigManager, get_config_manager
#from core.tts_manager import TTSManager
#from core.text_processor import TextProcessor
#from core.file_manager import FileManager

# Список доступних редакторів
#AVAILABLE_EDITORS = [
#    'accent_editor',
#    'voice_tags_editor', 
#    'sound_effects_editor',
#    'multispeaker_tts'
#]

#__all__ = [
#    'ModularConfigManager',
#    'get_config_manager',
#    'TTSManager', 
#    'TextProcessor',
#    'FileManager',
#    'AVAILABLE_EDITORS'
#]

#"""
#Book Editors Suite - комплекс редакторів для підготовки аудіокниг
#Головний пакет проекту
#"""

#__version__ = "1.0.0"
#__author__ = "Your Name"

# Імпорт основних компонентів для зручного доступу
#from core.config_manager import ModularConfigManager, get_config_manager
#from core.tts_manager import TTSManager
#from core.text_processor import TextProcessor
#from core.file_manager import FileManager

# Список доступних редакторів
#AVAILABLE_EDITORS = [
#    'accent_editor',
#    'voice_tags_editor', 
#    'sound_effects_editor',
#    'multispeaker_tts'
#]

#__all__ = [
#    'ModularConfigManager',
#    'get_config_manager',
#    'TTSManager', 
#    'TextProcessor',
#    'FileManager',
#    'AVAILABLE_EDITORS'
#]