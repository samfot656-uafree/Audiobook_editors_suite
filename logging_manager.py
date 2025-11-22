# -*- coding: utf-8 -*-
"""
Менеджер логування для всіх редакторів.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path


class LoggingManager:
    """Керування логуванням додатку."""

#-------------------------------------------    
    def __init__(self, log_dir: str, app_name: str = "app", level=logging.INFO):
        self.log_dir = Path(log_dir)
        self.app_name = app_name
        self.level = level
        self.logger = None
        self.setup_logging()

#-------------------------------------------    
    def setup_logging(self):
        """Налаштовує систему логування."""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = self.log_dir / f"{self.app_name}.log"
            
            # Створюємо логер
            self.logger = logging.getLogger(self.app_name)
            self.logger.setLevel(self.level)
            
            # Видаляємо старі обробники
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)
            
            # Форматер
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s\n',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Файловий обробник
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            
            # Консольний обробник
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            
            # Додаємо обробники
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
            
            self.info("=_" * 10)
            self.info(f"setup_logging: 🚀 {self.app_name} запущено\n")
            self.info(f"📝 Лог-файл: {log_file}\n")
            self.info("=_" * 10)
            
        except Exception as e:
            print(f"setup_logging: ❌ Помилка налаштування логування: {e}\n")
            # Резервний логер
            self.logger = logging.getLogger(f"{self.app_name}_fallback")
            self.logger.setLevel(self.level)
            if not self.logger.handlers:
                handler = logging.StreamHandler(sys.stdout)
                self.logger.addHandler(handler)

#-------------------------------------------    
    def info(self, message: str):
        """Запис інформаційного повідомлення."""
        if self.logger:
            self.logger.info(message)

#-------------------------------------------    
    def error(self, message: str):
        """Запис повідомлення про помилку."""
        if self.logger:
            self.logger.error(message)

#-------------------------------------------    
    def warning(self, message: str):
        """Запис попереджувального повідомлення."""
        if self.logger:
            self.logger.warning(message)

#-------------------------------------------    
    def debug(self, message: str):
        """Запис відлагоджувального повідомлення."""
        if self.logger:
            self.logger.debug(message)

#-------------------------------------------    
    def critical(self, message: str):
        """Запис критичного повідомлення."""
        if self.logger:
            self.logger.critical(message)
#-------------------------------------------            