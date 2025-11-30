#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# озвучує текст.
# глави зберігає по папках Текст та Звук.
# додає мелодію початка і кінця глави.
# за тегами в папку Звук копіює файли пауз та додаткових звуків
# параметри у config_m5_3.json
# копіює в папку проєкту вхідний текст, конфіг, лог та папку мелодій і пауз.
# додаткові звуки не копіює

#потрібно додати нові теги голосів з режимом швидкості
#потрібно додати нові теги "#S01: ".."#S99: " додаткових звуків з SCENARIOS_JSON_PATH : 
# "INPUT_SOUNDS_EFFECTS_FOLDER"
# "S43": "Звук_пострілу_part_022.wav"


import os, sys, json, re, logging, shutil
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
    
   
    
# ===========================
# Завантаження конфігурації
# ===========================

CONFIG_FILE = "/storage/emulated/0/Documents/pidgotovka_knigi/jsons/config_migration.json"
#CONFIG_FILE = "/storage/emulated/0/Documents/Json/config_m5_3.json"
with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

INPUT_TEXT_FILE = Path(config["INPUT_TEXT_FILE"])
OUTPUT_FOLDER = Path(config["OUTPUT_FOLDER"])
INPUT_SOUNDS_FOLDER = Path(config["INPUT_SOUNDS_FOLDER"])

PAUSE_4_mp3 = Path(config["PAUSE_4_mp3"])
PAUSE_7_mp3 = Path(config["PAUSE_7_mp3"])
PAUSE_1_mp3 = Path(config["PAUSE_1_mp3"])
PAUSE_2_mp3 = Path(config["PAUSE_2_mp3"])

PAUSE_4_wav = Path(config["PAUSE_4_wav"])
PAUSE_7_wav = Path(config["PAUSE_7_wav"])
PAUSE_1_wav = Path(config["PAUSE_1_wav"])
PAUSE_2_wav = Path(config["PAUSE_2_wav"])

MELODY_START_mp3 = Path(config["MELODY_START_mp3"])
MELODY_END_mp3 = Path(config["MELODY_END_mp3"])
MELODY_START_wav = Path(config["MELODY_START_wav"])
MELODY_END_wav = Path(config["MELODY_END_wav"])

TEST_wav = Path(config["TEST_wav"])

voice_dict: Dict[str, str] = config["voice_dict"]
pause_dict: Dict[str, str] = config["pause_dict"]
sound_dict: Dict[str, str] = config["sound_dict"]
TTS_MODE = config.get("TTS_MODE", "TFile")
DO_SPLIT = config.get("DO_SPLIT", True)
DO_MERGE = config.get("DO_MERGE", True)
FRAGMENT_SOFT_LIMIT = config.get("FRAGMENT_SOFT_LIMIT", 900)
FRAGMENT_HARD_LIMIT = config.get("FRAGMENT_HARD_LIMIT", 1000)
SOUNDS_MODE = "mp3" if TTS_MODE == "gTTS" else "wav"
_current_fragment_counter = 0

# Тимчасові та іменні константи (для структури проекту)
TEMP_FOLDER_NAME = "temp_multispeakers"
INP_MELODY_SUBFOLDER = "Input_melodu"
#"INPUT_SOUNDS_EFFECTS_FOLDER"

# Внутрішні змінні (ініціалізуються в init_project_root)
_project_root: Optional[Path] = None
_temp_folder: Optional[Path] = None
_log_file_path: Optional[Path] = None
_current_chapter_folder: Optional[Path] = None
_current_audio_folder: Optional[Path] = None
_current_text_folder: Optional[Path] = None
_current_chapter_name_for_files: Optional[str] = None
_current_chapter_name_for_fragment: Optional[str] = None
_current_voice_tag: Optional[str] = None
_current_fragment_counter: int = 0
_current_block_text: List[str] = []

# ===========================
# Логування
# ===========================
def setup_logging(project_root: Path):
    log_path = project_root /TEMP_FOLDER_NAME/ "Лог_збереження.txt"
    logging.basicConfig(
        level=logging.INFO,
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
        format='\n%(asctime)s | %(levelname)s | %(message)s\n',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
#    logging.info(f"setup_logging: \nЛогування встановлено")

# ===========================
# Утиліти
# ===========================
#
def ensure_folder(path):
    Path(path).mkdir(parents=True, exist_ok=True)
  #  logging.info(f"ensure_folder: \nСтворено папку: \n{path}")
    
# -------------------
def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)
   # logging.info(f"ensure_dir: \nСтворено діректорію: \n{path}")
    
 # -------------------
def sanitize_chapter_folder_name (s: str) -> str:
    s2 = re.sub(r"^##\s* ", "", s)
    s2 = re.sub(r"#g\d+: ", "", s2)   
    s2 = s2.strip()
    s2 = s2.replace('\u0301', '')
    s2 = s2.replace("'", '')
    s2 = s2.replace(' ', '_')
    s2 = s2.replace(',', '')
    s2 = s2.replace('.', '')
    s2 = s2.replace('+', '')
    s2 = re.sub(r"[\\/:*?\"<>|]", "_", s2)
    logging.info(f"sanitize_chapter_fragment_title: \nНазва глави: \n'{s2}'")
    if not s2:
        s2 = "Глава"
    return s2
    
# -------------------
def sanitize_chapter_fragment_title(s: str) -> str:
    s2 = re.sub(r"^##\s* ", "", s)
    s2 = re.sub(r"#g\d+: ", "", s2)
    logging.info(f"sanitize_chapter_fragment_title: \nНазва глави: \n'{s2}'")
    return s2.strip()
    
# -------------------
def format_fragment_filename(chapter_name: str, num: int, ext: str) -> str:
    logging.info(f"format_fragment_filename: \nФрагмент: \n'{chapter_name}_фр_{num:04d}.{ext}'")
    return f"{chapter_name}_фр_{num:04d}.{ext}"

# -------------------
def ensure_melodies_copied():
    """
    Копіює мелодії та паузи у TEMP/Inp_melodu і дає стандартні назви. 
    Додаткові звуки не переносить.
    """
    global _temp_folder
    if _temp_folder is None:
        logging.warning("ensure_melodies_copied:  \n_temp_folder не встановлено")
        return
    f_i_s= folder_input_sound = _temp_folder / INP_MELODY_SUBFOLDER
    ensure_folder(f_i_s)
    melody_map = [
        (MELODY_START_wav, f_i_s / f"MELODY_START.wav"),
        (MELODY_END_wav, f_i_s / f"MELODY_END.wav"),
        
        (MELODY_START_mp3, f_i_s / f"MELODY_START.mp3"),
        (MELODY_END_mp3, f_i_s / f"MELODY_END.mp3"),
        
        (PAUSE_2_wav, f_i_s / f"PAUSE_2.wav"),
        (PAUSE_2_mp3, f_i_s / f"PAUSE_2.mp3"),
        
        (PAUSE_1_wav, f_i_s / f"PAUSE_1.wav"),
        (PAUSE_1_mp3, f_i_s / f"PAUSE_1.mp3"),
        
        (PAUSE_7_wav, f_i_s / f"PAUSE_7.wav"),
        (PAUSE_7_mp3, f_i_s / f"PAUSE_7.mp3"),
        
        (PAUSE_4_wav, f_i_s / f"PAUSE_4.wav"),
        (PAUSE_4_mp3, f_i_s / f"PAUSE_4.mp3"),
        (TEST_wav, f_i_s / f"TEST.wav")                          
    ]
    for src, dst in melody_map:
        try:
            if src and Path(src).exists():
                shutil.copy2(src, dst)
                logging.info(f"ensure_melodies_copied: \nКопія мелодії: \n{src} -> \n{dst}")
            else:
                logging.warning(f" ensure_melodies_copied: \nМелодія не знайдена: \n{src}")
        except Exception as e:
            logging.warning(f"ensure_melodies_copied: \nНе вдалося скопіювати мелодію \n{src}: {e}")


# ===========================
# TTS генерація
# ===========================
def tts_generate_gtts(text: str, out_path: Path, lang: str='uk') -> bool:
    if gTTS is None:
        logging.error("tts_generate_gtts: \ngTTS не встановлено")
        return False
    try:
        gTTS(text=text, lang=lang).save(str(out_path))
        return True
    except Exception as e:
        logging.exception(f"tts_generate_gtts \ngTTS помилка: {e}")
        return False
# -------------------
def tts_generate_tfile(text: str, out_path: Path, test_l_wav: Path) -> bool:
    try:
        shutil.copyfile(str(test_l_wav), str(out_path))
        return True
    except Exception as e:
        logging.exception(f"tts_generate_tfile \nTFile помилка: {e}")
        return False
# -------------------
def tts_generate_stylets2(text: str, out_path: Path, voice_tag: str) -> bool:
    logging.warning("tts_generate_stylets2: \nStyleTTS2: потрібно реалізувати реальний TTS")
    return False

# ===========================
# Збереження фрагмента
# ===========================
def save_fragment_and_tts(fragment_l_text: str, voice_l_tag: str, chapter_l_folder_name: str, fragment_l_num: int) -> Tuple[bool, Optional[Path]]:
    global _current_text_folder, _current_audio_folder, _current_fragment_counter, SOUNDS_MODE
    if _current_text_folder is None or _current_audio_folder is None:
        logging.error(f"save_fragment_and_tts: \nПапки не ініціалізовані: \n{_current_text_folder} \n{_current_audio_folder} \n{_current_fragment_counter} \n{SOUNDS_MODE}")
        return False, None

    txt_l_name = format_fragment_filename(chapter_l_folder_name, fragment_l_num, 'txt')
    txt_l_path = _current_text_folder / txt_l_name
    try:
        with txt_l_path.open('w', encoding='utf-8') as f:
            f.write(fragment_l_text)
        logging.info(f"save_fragment_and_tts: \nЗбережено текст: {txt_l_path} ")
    except Exception as e:
        logging.exception(f"save_fragment_and_tts: \nПомилка збереження txt: {e}")
        return False, None
   
    audio_l_name = format_fragment_filename(chapter_l_folder_name, fragment_l_num, SOUNDS_MODE)
    audio_l_path = _current_audio_folder / audio_l_name

    success = False
    if TTS_MODE == 'gTTS':
        success = tts_generate_gtts(fragment_l_text, audio_l_path)
    elif TTS_MODE == 'TFile':
        success = tts_generate_tfile(fragment_l_text, audio_l_path, Path(TEST_wav))
    elif TTS_MODE == 'StyleTTS2':
        success = tts_generate_stylets2(fragment_l_text, audio_l_path, voice_l_tag)
    else:
        logging.error(f"\nНевідомий режим TTS: {TTS_MODE}")

    if success:
        logging.info(f"save_fragment_and_tts: \nФрагмент  озвучено: \n{audio_l_path} (голос: {voice_l_tag})")              
        _current_fragment_counter +=1      
        return True, audio_l_path
    else:
        logging.error(f"save_fragment_and_tts: \nНе вдалося озвучити фрагмент #{fragment_l_num} для голосу {voice_l_tag}")
        return False, None
        
# -------------------
def save_fragment(text: str, voice_tag: str, chapter_folder: Path, frag_num: int, test_l_wav: Optional[Path]=None) -> Path:
    global _current_fragment_counter
    
    audio_folder = chapter_folder / "Звук"
    text_folder = chapter_folder / "Текст"
    ensure_folder(audio_folder)
    ensure_folder(text_folder)

    # txt
    txt_path = text_folder / format_fragment_filename(chapter_folder.name, frag_num, "txt")
    txt_path.write_text(text, encoding="utf-8")
    logging.info(f"save_fragment: \nЗбережено текст фрагменту: \n{txt_path}")

    # аудіо
    audio_path = audio_folder / format_fragment_filename(chapter_folder.name, frag_num, SOUNDS_MODE)
    success = False
    if TTS_MODE=='gTTS':
        success = tts_generate_gtts(text, audio_path)
    elif TTS_MODE=='TFile':
        success = tts_generate_tfile(text, audio_path, test_l_wav)
    elif TTS_MODE=='StyleTTS2':
        success = tts_generate_stylets2(text, audio_path, voice_tag)
    if success:
        logging.info(f"save_fragment: \nФрагмент озвучено: \n{audio_path}")
    _current_fragment_counter +=1
    return audio_path

# ===========================
# Додавання пауз та звуків
# ===========================
def add_sound_or_pause(tag: str, chapter_folder: Path, frag_num: int) -> Optional[Path]:
    global frag_counter
    global _temp_folder, _current_fragment_counter, SOUNDS_MODE
    audio_folder = chapter_folder / "Звук"
    ensure_folder(audio_folder)
    
    folder_l_input_sound = _temp_folder / INP_MELODY_SUBFOLDER    
    
    out_l_path = audio_folder / format_fragment_filename(chapter_folder.name, frag_num, SOUNDS_MODE)
    if tag in pause_dict:    	
    	pause_l_name = f"{pause_dict[tag]}.{SOUNDS_MODE}"
    	pause_l_path = folder_l_input_sound / pause_l_name
    
    	shutil.copy2(str(pause_l_path), str(out_l_path))
    	logging.info(f"add_sound_or_pause: \nДодано паузу: {tag} -> \n{out_l_path}")
    elif tag in sound_dict:
        sound_inp_path = os.path.join(INPUT_SOUNDS_FOLDER, f"{sound_dict[tag]}.{SOUNDS_MODE}")
        shutil.copyfile(sound_inp_path, out_l_path)
        logging.info(f"add_sound_or_pause: \nДодано звук: {tag} -> \n{out_l_path}")
    _current_fragment_counter +=1
    return out_l_path

# ===========================
# Мелодії початок і кінець глави
# ===========================
def add_melody(chapter_folder: Path, frag_num: int, kind="START"):
    global _current_fragment_counter
    audio_folder = chapter_folder / "Звук"
    ensure_folder(audio_folder)
    
    melody_inp_path = os.path.join(INPUT_SOUNDS_FOLDER, f"MELODY_{kind}.{SOUNDS_MODE}")      
    out_path = audio_folder / format_fragment_filename(chapter_folder.name, frag_num, SOUNDS_MODE)
    shutil.copyfile(melody_inp_path, out_path)
    logging.info(f"add_melody: \nДодано мелодію {kind}: \n{out_path}")
    _current_fragment_counter +=1
    return out_path

# -------------------
def merge_chapter_audio(chapter_folder: Path):
    """Об’єднує всі звукові фрагменти глави в один файл (використовує pydub)."""
    if AudioSegment is None:
        logging.error("merge_chapter_audio: \npydub не встановлено — не можу об'єднати аудіо.")
        return
    sound_folder = chapter_folder / "Звук"
    if not sound_folder.exists():
        logging.warning(f"merge_chapter_audio: \nПапки зі звуком немає: {sound_folder}")
        return
    fragments = sorted([f for f in os.listdir(sound_folder) if f.endswith(f".{SOUNDS_MODE}")])
    if not fragments:
        logging.warning("merge_chapter_audio: \nНемає фрагментів для об'єднання.")
        return
    combined = None
    for f in fragments:
        seg = AudioSegment.from_file(str(sound_folder / f))
        combined = seg if combined is None else combined + seg
    if combined:
        out_file = sound_folder / f"{chapter_folder.name}_повна.{SOUNDS_MODE}"
        combined.export(str(out_file), format=SOUNDS_MODE)
        logging.info(f"merge_chapter_audio: \nОб'єднано аудіо: \n{out_file}")

# -------------------
# Управління главами та блоками
# -------------------
def init_project_root(input_file: str, output_folder: str) -> Path:
    global _project_root, _temp_folder
    input_name = Path(input_file).stem
    project_root = Path(output_folder) / input_name
    ensure_folder(project_root)
    _project_root = project_root
    _temp_folder = project_root / TEMP_FOLDER_NAME
    ensure_folder(_temp_folder)
    ensure_folder(_temp_folder / INP_MELODY_SUBFOLDER)
    try:
    	shutil.copyfile(input_file, str(_temp_folder / Path(input_file).name))
    	shutil.copyfile(CONFIG_FILE, str(_temp_folder / Path(CONFIG_FILE).name))
    	
    except Exception as e:
        logging.warning(f"init_project_root: \nНе вдалося скопіювати вхідний файл у проект: {e}")
    setup_logging(project_root)
    logging.info(f"init_project_root: \nІніціалізовано проєкт: \n{_project_root}")
    return project_root

# -------------------
def start_new_chapter(raw_chapter_line: str):
    global _current_chapter_folder, _current_text_folder, _current_audio_folder
    global _current_chapter_name_for_files, _current_chapter_name_for_fragment
    global _current_fragment_counter, _current_block_text, _current_voice_tag

    chapter_folder_name = sanitize_chapter_folder_name(raw_chapter_line)
    chapter_fragment_title = sanitize_chapter_fragment_title(raw_chapter_line)

    _current_chapter_folder = _project_root / chapter_folder_name
    ensure_folder(_current_chapter_folder)
    _current_text_folder = _current_chapter_folder / "Текст"
    _current_audio_folder = _current_chapter_folder / "Звук"
    ensure_folder(_current_text_folder)
    ensure_folder(_current_audio_folder)

    _current_fragment_counter = 0
    _current_block_text = []

    m = re.search(r"#g(\d+):", raw_chapter_line)
    if m:
        _current_voice_tag = f"g{m.group(1)}"
    else:
        _current_voice_tag = 'g1'

    _current_chapter_name_for_files = chapter_folder_name
    _current_chapter_name_for_fragment = chapter_fragment_title
    
    # Додати мелодію початку як фрагмент 0000 
    add_melody (_current_chapter_folder, _current_fragment_counter, "START")
    # Перший фрагмент починається з назви глави (якщо є)
    if _current_chapter_name_for_fragment:
        _current_block_text.append(_current_chapter_name_for_fragment)
    logging.info(f"start_new_chapter: \nПочато нову главу: \n{_current_chapter_folder} (голос: {_current_voice_tag})")

# -------------------
def start_new_voice_block(line_with_tag: str):
    global _current_block_text, _current_voice_tag, _current_fragment_counter
    global _current_chapter_name_for_files
    # Зберегти поточний блок
    cur_text = '\n'.join(_current_block_text).strip()
    if cur_text and _current_voice_tag:
        		
    	save_fragment_and_tts (cur_text, _current_voice_tag, _current_chapter_name_for_files, _current_fragment_counter)
    # Очистити поточний блок
    _current_block_text = []
    m = re.search(r"#g(\d+):", line_with_tag)
    if m:
        _current_voice_tag = f"g{m.group(1)}"
        after = re.sub(r"^.*#g\d+:", "", line_with_tag).strip()
        if after:
            _current_block_text.append (after)
    else:
        logging.warning(f"start_new_voice_block: \nНе знайдено тегу в рядку: {line_with_tag}")

# -------------------
def append_line_to_block(line: str):
    global _current_block_text, _current_fragment_counter, _current_voice_tag, _current_chapter_name_for_files, _current_chapter_folder
    stripped = line.rstrip('\n')
    # Якщо порожній рядок — вважати паузою: додати паузу як окремий фрагмент
    if stripped.strip() == "":
        # Якщо є накопичений текст — зберегти його як фрагмент
        cur_text = '\n'.join(_current_block_text).strip()
        if cur_text:
            save_fragment_and_tts (cur_text, _current_voice_tag, _current_chapter_name_for_files, _current_fragment_counter)
            # Додати паузу як наступний аудіофайл 
            add_sound_or_pause("P2", _current_chapter_folder,_current_fragment_counter) 
 
        _current_block_text = []
        return

    cur_text = '\n'.join(_current_block_text)
    cur_len = len(cur_text)

    # Якщо додавання рядка не порушує HARD ліміту — додаємо
    if cur_len + 1 + len(stripped) <= FRAGMENT_HARD_LIMIT:
        # Якщо після додавання перевищується SOFT — можна все одно додати до HARD
        _current_block_text.append(stripped)
        # Якщо після додавання ми перевищили SOFT, але не HARD — можна вирішити зберегти наступного разу
        if len('\n'.join(_current_block_text)) >= FRAGMENT_SOFT_LIMIT:
            # зберігаємо як фрагмент, але дозволяємо продовжити
            save_fragment_and_tts('\n'.join(_current_block_text).strip(), _current_voice_tag, _current_chapter_name_for_files, _current_fragment_counter)
            _current_block_text = []
    else:
        # Закриваємо поточний блок і починаємо новий
        if cur_text.strip():
        	save_fragment_and_tts (cur_text.strip(), _current_voice_tag, _current_chapter_name_for_files, _current_fragment_counter)
        _current_block_text = [stripped]

# -------------------
def finalize_chapter():
    global _current_block_text, _current_voice_tag, _current_audio_folder, _current_fragment_counter, _current_chapter_name_for_files, _current_chapter_folder
    if _current_chapter_name_for_files is None:
        logging.debug("finalize_chapter: \nНема відкритої глави")
        return
    if _current_block_text and _current_voice_tag:
        fragment_text = '\n'.join(_current_block_text).strip()
        if fragment_text:
             save_fragment_and_tts (fragment_text, _current_voice_tag, _current_chapter_name_for_files, _current_fragment_counter)
        # Додати мелодію завершення як наступний фрагмент
    add_melody (_current_chapter_folder, _current_fragment_counter, "END")
    
    logging.info(f"finalize_chapter: \nГлава '{_current_chapter_name_for_files}' завершена.\nФрагментів: {_current_fragment_counter}")
    _current_block_text = []
    _current_voice_tag = None

# -------------------
# Основний процес
# -------------------
def process_input_file(input_file: str):
    global _project_root
    global _current_block_text, _current_voice_tag, _current_fragment_counter, _current_chapter_folder, _current_chapter_name_for_files

    project_root = init_project_root(input_file, OUTPUT_FOLDER)

    if not DO_SPLIT:
        logging.info("process_input_file: \nDO_SPLIT=False — розбиття відключено.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_chapter = False
    for raw_line in lines:
        line = raw_line.rstrip('\n')
        # Початок глави
        if line.strip().startswith('##'):
            if in_chapter:
                finalize_chapter()
            start_new_chapter(line)
            in_chapter = True
            continue
        # Тег голосу у рядку
        m = re.search(r"#g(\d+):", line)
        if m:
            start_new_voice_block(line)
            continue
        # Рядок поза главою
        if not in_chapter:
            logging.debug(f"process_input_file: \nРядок поза главою ігнорується: \n{line}")
            continue
        # Додаємо рядок у блок
        append_line_to_block(line)

    if in_chapter:
        finalize_chapter()

    if DO_MERGE:
        # Злиття аудіо по кожній главі
        for chapter_dir in _project_root.iterdir():
            if chapter_dir.is_dir():
                audio_dir = chapter_dir / 'Звук'
                if audio_dir.exists():
                    merge_chapter_audio(chapter_dir)

    logging.info("process_input_file: \nОбробка файлу завершена.")

# -------------------
# Утиліти для ініціалізації при запуску
# -------------------
def process_init_project(input_file: str):
    ensure_folder(OUTPUT_FOLDER)
    # init_project_root створить структуру і лог
    project_root = init_project_root(input_file, OUTPUT_FOLDER)
       
    # Скопіювати мелодії в TEMP
  
    ensure_melodies_copied()
    logging.info(f"process_init_project: \nІніціалізація проекту у \n{project_root}")

# -------------------
# Запуск
# -------------------
if __name__ == '__main__':
    if not Path(INPUT_TEXT_FILE).exists():
        print(f"Запуск: \nВхідний файл не знайдено: \n{INPUT_TEXT_FILE}")
        sys.exit(1)
        
    ensure_folder(OUTPUT_FOLDER)
    print(f"Запуск: \nTTS_MODE={TTS_MODE}, \nSOUNDS_MODE={SOUNDS_MODE}\n ")
    try:
        process_init_project(INPUT_TEXT_FILE)
        process_input_file(INPUT_TEXT_FILE)
    except Exception as e:
        logging.exception(f'Запуск: \nКритична помилка при обробці: {e}')
        print(f'Запуск: \nКритична помилка: {e}')
        sys.exit(1)
    print('Запуск: \n--- Готово: обробка завершена. Перевірте лог у каталозі проєкту. ---\n')
