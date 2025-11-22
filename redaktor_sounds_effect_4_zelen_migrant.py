"""
Редактор сценаріїв озвучення для Android (Pydroid 3)

Опис:
Додаток дозволяє:
- Зчитати JSON-файл зі сценаріями ("Сценарії до тексту.json").
- Показати всі теги у Spinner (в порядку номерів).
- Показати тег з найбільшим номером у Label.
- Створювати новий тег (кнопка показує наступний номер).
- Додавати тег у позицію курсору в тексті для озвучування.
- Зберігати JSON і текстовий файл.

"""

# ------------------------------------------------------------
# Імпорти
# ------------------------------------------------------------
import json
import os
from functools import partial

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.clock import Clock

# ------------------------------------------------------------
# Налаштування зовнішнього вигляду
# ------------------------------------------------------------
Window.clearcolor = (1, 1, 1, 1)
FONT_SIZE = 40
TEXT_COLOR = (0, 0.4, 0, 1)

# ------------------------------------------------------------
# Константи шляхів до файлів
# ------------------------------------------------------------
SCENARIOS_JSON_PATH = "/storage/emulated/0/Documents/pidgotovka_knigi/jsons/scenarios_ozvuch_c4.json"
TEXT_FOR_TTS_PATH = "/storage/emulated/0/Documents/Out_txt/ч001.txt"

# ------------------------------------------------------------
# Утиліти: Робота з тегами
# ------------------------------------------------------------
def parse_tag_number(tag: str) -> int:
    try:
        if tag and tag[0].upper() == 'S':
            return int(tag[1:])
    except Exception:
        pass
    return -1

def make_tag_from_number(n: int) -> str:
    return f"S{n:02d}"

# ------------------------------------------------------------
# Робота з файлами
# ------------------------------------------------------------
def read_scenarios_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        scenarios = data.get('scenarios_dict', {}) if isinstance(data, dict) else {}
        return {str(k): str(v) for k, v in scenarios.items()}
    except Exception as e:
        print('Error reading JSON:', e)
        return {}

def save_scenarios_json(path: str, scenarios: dict) -> bool:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'scenarios_dict': scenarios}, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print('Error saving JSON:', e)
        return False

def read_text_file(path: str) -> str:
    if not os.path.exists(path):
        return ""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print('Error reading text file:', e)
        return ""

def save_text_file(path: str, text: str) -> bool:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        return True
    except Exception as e:
        print('Error saving text file:', e)
        return False

# ------------------------------------------------------------
# Головний Layout
# ------------------------------------------------------------
class EditorLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=8, spacing=8, **kwargs)

        self.scenarios = read_scenarios_json(SCENARIOS_JSON_PATH)
        self.max_tag = self._find_max_tag()

        self._build_ui()
        Clock.schedule_once(lambda dt: self.load_text(), 0.1)

    # ------------------ Утиліти ------------------
    def _find_max_tag(self):
        if not self.scenarios:
            return make_tag_from_number(0)
        max_n = -1
        max_tag = 'S00'
        for t in self.scenarios.keys():
            n = parse_tag_number(t)
            if n > max_n:
                max_n = n
                max_tag = t
        if max_n == -1:
            return make_tag_from_number(0)
        return max_tag

    def _next_tag(self):
        current = self._find_max_tag()
        n = parse_tag_number(current)
        if n < 0:
            n = 0
        return make_tag_from_number(n + 1)

    def _sorted_tags(self):
        tags = list(self.scenarios.keys())
        tags.sort(key=lambda t: parse_tag_number(t))
        return tags

    # ------------------ Побудова UI ------------------
    def _build_ui(self):
        # Spinner
        self.spinner = Spinner(
            text='Всі наявні теги сценаріїв',
            values=tuple(self._sorted_tags()),
            size_hint=(1, None),
            height=80,
            font_size=FONT_SIZE
        )
        self.spinner.bind(text=self.on_spinner_select)
        self.add_widget(self.spinner)

        # Label max tag
        self.label_max_tag = Label(
            text=f'Максимальний тег: {self.max_tag}',
            size_hint=(1, None),
            height=40,
            font_size=FONT_SIZE,
            color=TEXT_COLOR
        )
        self.label_max_tag.bind(size=self.label_max_tag.setter('text_size'))
        self.add_widget(self.label_max_tag)

        # Поточний тег
        self.current_tag_input = TextInput(
            text='',
            multiline=False,
            size_hint=(1, None),
            height=60,
            font_size=FONT_SIZE,
            foreground_color=TEXT_COLOR
        )
        self.add_widget(self.current_tag_input)

        # Поточний опис
        self.current_desc_input = TextInput(
            text='',
            multiline=True,
            size_hint=(1, None),
            height=120,
            font_size=FONT_SIZE,
            foreground_color=TEXT_COLOR
        )
        self.add_widget(self.current_desc_input)

        # Кнопки
        btn_row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=70, spacing=6)

        btn_clear = Button(text='Очистити', size_hint=(.25, 1), font_size=FONT_SIZE)
        btn_clear.bind(on_release=lambda btn: self.clear_current_fields())
        btn_row.add_widget(btn_clear)

        self.btn_next_tag = Button(text=self._next_tag(), size_hint=(.25, 1), font_size=FONT_SIZE)
        self.btn_next_tag.bind(on_release=lambda btn: self.set_next_tag())
        btn_row.add_widget(self.btn_next_tag)

        btn_add = Button(text='Додати сценарій', size_hint=(.25, 1), font_size=FONT_SIZE)
        btn_add.bind(on_release=lambda btn: self.add_scenario_at_cursor())
        btn_row.add_widget(btn_add)

        btn_save_text = Button(text='Зберегти текст', size_hint=(.25, 1), font_size=FONT_SIZE)
        btn_save_text.bind(on_release=lambda btn: self.save_text_to_file())
        btn_row.add_widget(btn_save_text)

        self.add_widget(btn_row)

        # Текст для озвучування
        self.text_input = TextInput(
            text='',
            multiline=True,
            size_hint=(1, 1),
            font_size=FONT_SIZE,
            foreground_color=TEXT_COLOR
        )
        self.add_widget(self.text_input)

    # ------------------ Події ------------------
    def on_spinner_select(self, spinner, text):
        tag = text
        desc = self.scenarios.get(tag, '')
        self.current_tag_input.text = tag
        self.current_desc_input.text = desc

    def load_text(self):
        txt = read_text_file(TEXT_FOR_TTS_PATH)
        self.text_input.text = txt

    def update_all_widgets(self):
        self.scenarios = read_scenarios_json(SCENARIOS_JSON_PATH)
        tags = self._sorted_tags()
        self.spinner.values = tuple(tags)
        if tags:
            self.spinner.text = tags[0]
            self.current_tag_input.text = tags[0]
            self.current_desc_input.text = self.scenarios.get(tags[0], '')
        else:
            self.spinner.text = 'Всі наявні теги сценаріїв'
            self.current_tag_input.text = ''
            self.current_desc_input.text = ''
        self.max_tag = self._find_max_tag()
        self.label_max_tag.text = f'Максимальний тег: {self.max_tag}'
        self.btn_next_tag.text = self._next_tag()

    def clear_current_fields(self):
        self.current_tag_input.text = ''
        self.current_desc_input.text = ''

    def set_next_tag(self):
        next_tag = self._next_tag()
        self.current_tag_input.text = next_tag
        self.current_desc_input.text = ''
        self.btn_next_tag.text = self._next_tag()

    def add_scenario_at_cursor(self):
        tag = self.current_tag_input.text.strip()
        desc = self.current_desc_input.text

        if not tag:
            self._show_message('Помилка', 'Поле "Поточний тег" пусте.')
            return

        try:
            self.text_input.insert_text(f"#{tag}: ")
        except Exception as e:
            print('Error inserting text:', e)

        self.scenarios[tag] = desc
        ok = save_scenarios_json(SCENARIOS_JSON_PATH, self.scenarios)
        if ok:
            self._show_message('Успіх', f'Сценарій {tag}\n{self.scenarios[tag]} \nзбережено у JSON.')
            self.update_all_widgets()
        else:
            self._show_message('Помилка', 'Не вдалося зберегти JSON.')

    def save_text_to_file(self):
        text = self.text_input.text
        ok = save_text_file(TEXT_FOR_TTS_PATH, text)
        if ok:
            self._show_message('Успіх', f'Текст збережено.\n{TEXT_FOR_TTS_PATH}')
        else:
            self._show_message('Помилка', 'Не вдалося зберегти текст.')

    def _show_message(self, title: str, message: str):
        content = BoxLayout(orientation='vertical', padding=10)
        lbl = Label(text=message, font_size=FONT_SIZE, color=TEXT_COLOR)
        btn = Button(text='OK', size_hint=(1, None), height=60, font_size=FONT_SIZE)
        content.add_widget(lbl)
        content.add_widget(btn)
        popup = Popup(title=title, content=content, size_hint=(.9, .4))
        btn.bind(on_release=popup.dismiss)
        popup.open()

# ------------------------------------------------------------
# Запуск додатку
# ------------------------------------------------------------
class ScenariosEditorApp(App):
    def build(self):
        return EditorLayout()

if __name__ == '__main__':
    ScenariosEditorApp().run()
