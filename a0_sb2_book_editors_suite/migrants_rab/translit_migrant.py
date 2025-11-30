import os
from datetime import datetime

# Транслитерація українських букв у латиницю
uk_to_lat = {
    'а':'a','б':'b','в':'v','г':'h','ґ':'g','д':'d','е':'e','є':'ye','ж':'zh',
    'з':'z','и':'y','і':'i','ї':'yi','й':'y','к':'k','л':'l','м':'m','н':'n',
    'о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts',
    'ч':'ch','ш':'sh','щ':'shch','ь':'','ю':'yu','я':'ya'
}

def transliterate(text):
    result = ''
    for char in text.lower():
        if char in uk_to_lat:
            result += uk_to_lat[char]
        elif char.isalnum() or char in ['_']:
            result += char
        else:
            result += '_'  # для пробілів та інших символів
    return result

def save_file(output_folder, input_name, text):
    # Розділяємо шлях на існуючі та нові папки
    path_parts = output_folder.split(os.sep)
    existing_path = ''
    new_parts = []
    
    for part in path_parts:
        check_path = os.path.join(existing_path, part) if existing_path else part
        if os.path.exists(check_path):
            existing_path = check_path
        else:
            # Робимо безпечну назву лише для нових частин шляху
            safe_part = transliterate(part.replace(' ', '_'))
            new_parts.append(safe_part)
            existing_path = os.path.join(existing_path, safe_part) if existing_path else safe_part
    
    # Остаточний шлях для створення
    final_folder = existing_path
    os.makedirs(final_folder, exist_ok=True)
    
    # Таймштамп рр_мм_дд_гг_хх
    timestamp = datetime.now().strftime("%y_%m_%d_%H_%M")
    
    # Назва файлу з транслітерацією та підкресленнями
    base_name = transliterate(os.path.splitext(input_name)[0].replace(' ', '_'))
    output_name = f"{base_name}_pravka_{timestamp}.txt"
    output_path = os.path.join(final_folder, output_name)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    
    print(f"Файл збережено: {output_path}")
    return output_path

# --- Тестовий запуск ---
if __name__ == "__main__":
    folder = "/storage/emulated/0/Documents/Multispeakers GGG/тестовий_текст/нова_папка"
    input_file_name = "тестовий файл.txt"
    sample_text = "Це тестовий текст для збереження."
    
    save_file(folder, input_file_name, sample_text)