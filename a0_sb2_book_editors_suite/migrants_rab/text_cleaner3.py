import unicodedata

def clean_text(input_file, output_file, symbols_file):
    # Відкриваємо файли
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out, \
         open(symbols_file, 'w', encoding='utf-8') as f_sym:

        # Читаємо вхідний файл посимвольно
        content = f_in.read()
        
        for char in content:
            # Дозволені символи:
            # 1. Українські літери (кирилиця)
            # 2. Латинські літери
            # 3. Цифри
            # 4. Основні розділові знаки
            # 5. Спеціальні: пробіл, табуляція, переноси, акутний знак
            
            code = ord(char)
            
            # Перевіряємо чи символ дозволений
            allowed = False
            
            # 1. Українські літери (кирилиця)
            if ('\u0400' <= char <= '\u04FF') or ('\u0500' <= char <= '\u052F'):
                allowed = True
            
            # 2. Латинські літери
            elif ('\u0041' <= char <= '\u005A') or ('\u0061' <= char <= '\u007A'):
                allowed = True
            
            # 3. Цифри
            elif '\u0030' <= char <= '\u0039':
                allowed = True
            
            # 4. Основні розділові знаки
            elif char in ' .,!?;:"\'()-_#[]{}«»„“–—…':
                allowed = True
            
            # 5. Спеціальні символи
            elif code in [0x0009, 0x000A, 0x000D, 0x0020, 0x0301]:  # \t, \n, \r, пробіл, акут
                allowed = True
            
            # Обробка результату
            if allowed:
                f_out.write(char)
            else:
                # Записуємо інформацію про символ у файл символів
                category = unicodedata.category(char)
                try:
                    char_name = unicodedata.name(char)
                except ValueError:
                    char_name = 'НЕВІДОМИЙ СИМВОЛ'
                
                f_sym.write(f"U+{code:04X} ({category}) - {char_name}\n")
                print(f"Видалено символ: U+{code:04X} ({category}) - {char_name}")

if __name__ == "__main__":
    input_path = "/storage/emulated/0/book_projects/доповнення13_у_нас_гості/book_text_file/доповнення13_у_нас_гості.txt"
    output_path = "/storage/emulated/0/book_projects/доповнення13_у_нас_гості/outputs/доповнення13_у_нас_гості_чист.txt"
    symbols_path = "/storage/emulated/0/book_projects/доповнення13_у_нас_гості/outputs/доповнення13_у_нас_гості_символи.txt"
    
    clean_text(input_path, output_path, symbols_path)
    print("Очищення завершено!")