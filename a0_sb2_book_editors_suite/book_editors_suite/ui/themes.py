# -*- coding: utf-8 -*-
"""
Модуль для управління темами інтерфейсу.
"""
from kivy.core.window import Window


class ThemeManager:
    """Менеджер тем для інтерфейсу додатку."""

#-------------------------------------------    
    def __init__(self):
        self.current_theme = "day"
        self.themes = {
            "day": {
                "button_bg": (0.5, 0.5, 0.5, 1),
                "button_fg": (1, 1, 1, 1),
                "input_bg": (1, 1, 1, 1),
                "input_fg": (0, 0, 0, 1),
                "cursor_color": (1, 0.2, 0.2, 1),
                "cursor_bat_color": (0.03, 0.85, 0.53, 1),
                "batt_25": (1, 0.2, 0.2, 1),
                "batt_30": (1, 0.6, 0.6, 1)               
            },
            "night": {
                "button_bg": (0, 0, 0, 1),
                "button_fg": (0.6, 0.85, 1, 1),
                "input_bg": (0, 0, 0, 1),
                "input_fg": (0, 0, 1, 1),
                "cursor_color": (1, 0.2, 0.2, 1),
                "cursor_bat_color": (0.03, 0.85, 0.53, 1),
                "batt_25": (1, 0.2, 0.2, 1),
                "batt_30": (1, 0.6, 0.6, 1)
            }
        }

#-------------------------------------------    
    def get_colors(self) -> dict:
        """Повертає кольори поточної теми."""
        return self.themes.get(self.current_theme, self.themes["day"])

#-------------------------------------------    
    def toggle_theme(self):
        """Перемикає тему день/ніч."""
        self.current_theme = "night" if self.current_theme == "day" else "day"

#-------------------------------------------    
    def set_theme(self, theme_name: str):
        """Встановлює конкретну тему."""
        if theme_name in self.themes:
            self.current_theme = theme_name

#-------------------------------------------
    def apply_theme_to_widgets(self, widgets_dict: dict):
        """
        Застосовує поточну тему до віджетів.
        
        Args:
            widgets_dict: Словник з віджетами {
                'buttons': list[Button],
                'labels': list[Label],            
                'text_inputs': list[TextInput],
                'window': Window
            }
        """
        try:
            colors = self.get_colors()
            
            # Застосування до кнопок
            if 'buttons' in widgets_dict:
                for btn in widgets_dict['buttons']:
                    btn.background_normal = ""
                    btn.background_color = colors["button_bg"]
                    btn.color = colors["button_fg"]
            
            # Застосування до міток
            if 'labels' in widgets_dict:
                for lbl in widgets_dict['labels']:
                	lbl.background_color = colors["button_fg"]                	
                	lbl.color = colors["cursor_bat_color"]
            
            # Застосування до текстових полів
            if 'text_inputs' in widgets_dict:
                for text_input in widgets_dict['text_inputs']:
                    text_input.background_color = colors["input_bg"]
                    text_input.foreground_color = colors["input_fg"]
                    text_input.cursor_color = colors["cursor_color"]
            
            # Застосування до вікна
            if 'window' in widgets_dict:
                widgets_dict['window'].clearcolor = colors["input_bg"]
                        
        except Exception as e:
            raise Exception(f"Помилка застосування теми: {e}")

#-------------------------------------------
    def apply_theme_from_app(self):
        """метод з EditWordPopup. Встановлює колір поля редагування слова залежно від заряду батареї. Кольори кнопок відповідно до День-ніч"""
        batt = self._get_battery_percent()
        colors = self.parent_app.get_theme_colors()
        
        if batt >= 0:
        	self.edit_input.cursor_color = colors["cursor_color"]
        	
        	if batt < 25:
        	       self.edit_input.background_color = colors["batt_25"]
        	       self.edit_input.cursor_color = colors["cursor_bat_color"]
        	       self.batt_label.color = colors["batt_25"]
        	
        	elif batt < 30:
        	       self.edit_input.background_color = colors["batt_30"]
        	       self.edit_input.cursor_color = colors["cursor_bat_color"]
        	       self.batt_label.color = colors["batt_30"]
        	
        	else:
        	       self.edit_input.background_color = colors["input_bg"]
        	       self.edit_input.foreground_color = colors["input_fg"]
        	       self.edit_input.cursor_color = colors["cursor_color"]
        	       self.batt_label.color = colors["cursor_bat_color"]
      
        # Застосування кольорів до кнопок та міток
        self.batt_label.background_color = colors["button_bg"]
        for widget in (self.btn_listen, self.btn_insert, self.btn_save_both, 
                      self.btn_save_text, self.btn_cancel, self.clock_label):
            if hasattr(widget, 'background_normal'):
                widget.background_normal = ""
                widget.background_color = colors["button_bg"]
                widget.color = colors["button_fg"]
            else:
                # Для Label встановлюємо тільки колір тексту
                widget.color = colors["button_fg"]
        
        try:
            self.edit_input.cursor_color = (0.03, 0.85, 0.53, 1)
        except Exception:
            pass
