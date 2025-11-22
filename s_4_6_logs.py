маємо проект з отакою структурою.

a0_sb2_book_editors_suite/
││
│ book_editors_suite/
│├── __init__.py                          # [1] Головний пакет
│├── core/
││     ├── __init__.py                      # [2] Спільні компоненти
││   ├── config_manager.py
││   ├── tts_manager.py
││   ├── text_processor.py
││   └── file_manager.py
│├── ui/
││   ├── __init__.py                      # [3] UI компоненти
││   ├── themes.py
││   └── popups/
││       ├── __init__.py                  # [4] Попапи
││       ├── edit_word_popup.py
││       └── extra_buttons_popup.py
│├── utils/
││       ├── __init__.py                      # [5] Утиліти
│ │      └── helpers.py
│ └── editors/
│ │        ├── __init__.py                      # [6] Пакет редакторів
│ │          ├── accent_editor/
│ │          ├── __init__.py                  # [7] Редактор наголосів
│ │         └── main.py
│ ├── voice_tags_editor/
│ │          ├── __init__.py                  # [8] Редактор тегів голосів
│ │          └── main.py
│ ├── sound_effects_editor/
│ │          ├── __init__.py                  # [9] Редактор звукових ефектів
│ │          └── main.py
│ └── multispeaker_tts/
│              ├── __init__.py                  # [10]   Мультиспікер
│              └── main.py
└── testing_function/
                     ├── test_config_manager.py
                     └── logs/
                            ├── config_manager.log
                            ├── accent_editor.log 
                            ├── voice_tags_editor.log                          
                            ├── sound_effects_editor.log
                            └── multispeaker_tts.log
