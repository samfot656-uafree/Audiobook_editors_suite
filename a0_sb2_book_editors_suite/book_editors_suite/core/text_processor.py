# -*- coding: utf-8 -*-
"""
Модуль обробки тексту.
"""
from book_editors_suite.utils.helpers import WORD_RE, strip_combining_acute, match_casing


class TextProcessor:
    """Клас для різноманітної обробки тексту."""
    
    def __init__(self, logger=None):
        self.logger = logger
    
    def match_casing(self, original: str, replacement: str) -> str:
        """
        Підбирає регістр replacement під оригінал.
        Використовує функцію match_casing з helpers.
        """
        result = match_casing(original, replacement)
        if self.logger:
            self.logger.debug(f"match_casing: '{original}' -> '{replacement}' -> '{result}'")
        return result
    
    def add_accents_to_text(self, text: str, accents: dict) -> str:
        """Додає наголоси до тексту згідно з словником."""
        def replace_with_accent(match):
            word = match.group(0)
            if '\u0301' in word:  # Якщо вже є наголос - залишаємо
                return word
            key = strip_combining_acute(word).lower()
            if key in accents:
                return self.match_casing(word, accents[key])
            return word

        accented_text = WORD_RE.sub(replace_with_accent, text)
        
        if self.logger:
            self.logger.info("add_accents_to_text:  Наголоси додано до тексту")
            
        return accented_text

    def split_into_paragraphs(self, text: str) -> list:
        """Розділяє текст на абзаци."""
        paragraphs = text.split("\n")
        if self.logger:
            self.logger.debug(f"split_into_paragraphs:  Текст розділено на {len(paragraphs)} абзаців")
        return paragraphs

    def count_words(self, text: str) -> int:
        """Підраховує кількість слів у тексті."""
        words = text.split()
        return len(words)

    def find_word_positions(self, text: str, word: str) -> list:
        """Знаходить усі позиції слова у тексті."""
        positions = []
        start = 0
        while True:
            start = text.find(word, start)
            if start == -1:
                break
            positions.append(start)
            start += len(word)
        return positions

    def detect_word_at_cursor(self, text: str, cursor_index: int):
        """
        Визначає слово під курсором.
        Повертає (word, start, end)
        """
        if not text or cursor_index < 0 or cursor_index > len(text):
            return None, 0, 0

        # Знаходимо межі слова
        start = cursor_index
        while start > 0 and self._is_word_char(text[start - 1]):
            start -= 1

        end = cursor_index
        while end < len(text) and self._is_word_char(text[end]):
            end += 1

        word = text[start:end]
        if WORD_RE.fullmatch(word):
            return word, start, end
        else:
            return None, 0, 0

    def _is_word_char(self, char: str) -> bool:
        """Перевіряє, чи символ є частиною слова."""
        return char.isalpha() or char == '\u0301' or char == "'"