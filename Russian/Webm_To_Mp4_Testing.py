import os
import subprocess
import sys
import tempfile
import shutil
import time
import json
from pathlib import Path

# ------------------------------------------------------------
# НАСТРОЙКИ (можно изменить)
# ------------------------------------------------------------


#⚠️⚠️⚠️ При копировании пути с windows используйте особый тип строки - r"...", где вместо ... Ваш путь к папке, скопированный из Windows. Это поможет избежать ошибки, при которой Python воспримет \U или любой другой символ после косой черты в пути к папке как команду. (а ошибка точно будет!)



# Путь к папке с исходными .webm файлами.
# Если оставить пустой строкой, будет использована текущая папка.
input_path = r""

# Путь для сохранения сконвертированных .mp4 файлов.
# Если оставить пустой строкой, будет создана папка 'converted' в папке с исходниками.
output_path = r""

# Режим конвертации: "Direct", "Frames" или "Auto"
mode = "Auto"  # Direct / Frames / Auto

# Значение CRF по умолчанию для всех конвертаций (чем меньше, тем выше качество и больше размер)
# Рекомендации: 18 - отличное качество (визуально lossless), 16 - очень высокое, 14 - избыточно высоко
crf_default = 18

# Путь к исполняемому файлу ffmpeg (если не прописан в PATH, укажите полный путь)
FFMPEG_PATH = "ffmpeg"  # или "C:\\ffmpeg\\bin\\ffmpeg.exe" для Windows
FFPROBE_PATH = "ffprobe"  # нужен для получения информации о видео



# ------------------------------------------------------------
# НАСТРОЙКИ ТЕСТОВОГО РЕЖИМА. Вы можете использовать его, чтобы сравнить итоговые файлы и решить для себя, какой crf Вам предпочтительнее. По своим наблюдениям хочу сказать, что не вижу разницу между оригиналом и crf 24 (кроме артефактов, которые видно только под микроскопом), а после crf 18 объём файлов значительно увеличивается.
# ------------------------------------------------------------
# Укажите путь к любому .webm файлу для тестирования
test_file_path = r"D:\webm to mp4\пример.webm"  # ⚠️ ЗАМЕНИТЕ НА РЕАЛЬНЫЙ ФАЙЛ!

# Папка для сохранения результатов теста.
# Если оставить пустой, будет создана папка "compare" рядом со скриптом.
test_output_dir = r""

# Режим обрезки для тестов:
# "default" - обрабатывать всё видео целиком
# "cut"     - обрезать первые 30 секунд (для ускорения тестирования)
test_cut_mode = "cut"  # default / cut

#Чтобы запустить тестовый режим, уберите комментарий на строках 300-301, в начале основной программы. (со временем и обновлением программы строки могут поменяться, а разработчик может об этом забыть. Читайте комментарии в том районе - не ошибётесь.)

# ------------------------------------------------------------
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ------------------------------------------------------------

def bytes_to_human(size):
    """Переводит байты в читаемый формат (Б, КБ, МБ, ГБ)."""
    for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} ТБ"

def get_video_info(video_path):
    """Получает длительность и fps видео с помощью ffprobe."""
    cmd = [
        FFPROBE_PATH,
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_streams',
        '-select_streams', 'v:0',
        video_path
    ]
    try:
        output = subprocess.check_output(cmd, universal_newlines=True)
        info = json.loads(output)
        streams = info.get('streams', [])
        if not streams:
            return None, None
        # Длительность
        duration = float(streams[0].get('duration', 0))
        # FPS
        r_frame_rate = streams[0].get('r_frame_rate', '0/0')
        num, den = map(int, r_frame_rate.split('/'))
        fps = num / den if den != 0 else 30.0
        return duration, fps
    except Exception:
        return None, None

def cut_video_segments(src, dst, mode):
    """
    Создаёт обрезанную версию видео в соответствии с режимом.
    mode: "cutted" или "extracutted" (но сейчас всегда режем первые 30 секунд)
    Возвращает (True, dst_path) при успехе, (False, None) при неудаче.
    """
    # Получаем длительность
    duration, _ = get_video_info(src)
    if duration is None:
        # Альтернативный способ
        try:
            cmd = [FFPROBE_PATH, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', src]
            output = subprocess.check_output(cmd, universal_newlines=True).strip()
            duration = float(output)
        except:
            print("   ⚠️ Не удалось определить длительность видео.")
            return False, None

    print(f"   ✂️ Обрезка видео (первые 30 секунд)...")
    cmd = [
        FFMPEG_PATH, '-i', src,
        '-t', '30',          # ограничиваем 30 секундами
        '-c:v', 'libx264', '-c:a', 'aac',  # перекодируем для гарантии
        '-y', dst
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        err = result.stderr.decode('utf-8', errors='replace')
        print(f"   ⚠️ Ошибка при обрезке: {err[:200]}")
        return False, None
    return True, dst

def convert_direct(src, dst, crf):
    """Прямая конвертация через ffmpeg с заданным CRF."""
    cmd = [
        FFMPEG_PATH, '-i', src,
        '-c:v', 'libx264', '-crf', str(crf),
        '-c:a', 'aac',
        '-y', dst
    ]
    result = subprocess.run(cmd, capture_output=True)
    stderr = result.stderr.decode('utf-8', errors='replace')
    return result.returncode == 0, stderr

def convert_frames(src, dst, crf):
    """
    Конвертация через извлечение кадров с заданным CRF.
    ВНИМАНИЕ: аудио не сохраняется (так как собираем только видео).
    """
    # Получаем FPS исходного видео
    _, fps = get_video_info(src)
    if fps is None:
        fps = 30.0
        print("   ⚠️ Не удалось определить FPS, используется 30")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Извлекаем кадры
        pattern = os.path.join(tmpdir, 'frame_%04d.png')
        extract_cmd = [
            FFMPEG_PATH, '-i', src,
            '-vf', 'fps={}'.format(fps),
            pattern
        ]
        extract_result = subprocess.run(extract_cmd, capture_output=True)
        if extract_result.returncode != 0:
            err = extract_result.stderr.decode('utf-8', errors='replace')
            return False, err

        frames = list(Path(tmpdir).glob('frame_*.png'))
        if not frames:
            return False, "No frames extracted"

        # Собираем видео из кадров с CRF
        input_pattern = os.path.join(tmpdir, 'frame_%04d.png')
        assemble_cmd = [
            FFMPEG_PATH, '-framerate', str(fps),
            '-i', input_pattern,
            '-c:v', 'libx264', '-crf', str(crf),
            '-pix_fmt', 'yuv420p',
            '-y', dst
        ]
        assemble_result = subprocess.run(assemble_cmd, capture_output=True)
        if assemble_result.returncode != 0:
            err = assemble_result.stderr.decode('utf-8', errors='replace')
            return False, err

    return True, ""

def pause():
    """Ожидает нажатия Enter перед закрытием (если запущено в интерактивном режиме)."""
    if sys.stdin.isatty():
        input("\nНажмите Enter для выхода...")

# ------------------------------------------------------------
# ТЕСТОВЫЙ МОДУЛЬ ДЛЯ СРАВНЕНИЯ CRF
# ------------------------------------------------------------

def test_quality_comparison():
    """
    Тест: конвертирует один файл (возможно, обрезанный) двумя методами с тремя разными CRF,
    выводит таблицу размеров и сохраняет все файлы в удобную папку.
    """
    print("\n" + "="*70)
    print("🧪 ТЕСТОВЫЙ РЕЖИМ: Сравнение методов и уровней CRF")
    print("="*70)
    
    test_file = test_file_path
    if not os.path.exists(test_file):
        print(f"❌ Тестовый файл не найден: {test_file}")
        print("   Пожалуйста, укажите правильный путь в переменной test_file_path.")
        pause()
        return
    
    # Определяем базовую папку для сохранения результатов
    if test_output_dir:
        base_dir = test_output_dir
    else:
        # Папка рядом со скриптом
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.join(script_dir, "compare")
    
    os.makedirs(base_dir, exist_ok=True)
    
    # Создаём подпапку с текущей датой и временем
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(base_dir, timestamp)
    os.makedirs(output_dir, exist_ok=True)
    
    # Если нужно обрезать видео, создаём обрезанную копию в этой же папке
    source_for_test = test_file
    source_is_cut = False
    if test_cut_mode == "cut":
        # Обрезаем первые 30 секунд
        cut_filename = f"cut_{os.path.basename(test_file)}.mp4"
        cut_path = os.path.join(output_dir, cut_filename)
        success_cut, cut_file = cut_video_segments(test_file, cut_path, test_cut_mode)  # можно передавать любой mode, функция всё равно игнорирует
        if success_cut:
            source_for_test = cut_file
            source_is_cut = True
            print(f"✂️ Видео обрезано (режим: {test_cut_mode}) -> {cut_filename}")
        else:
            print("   ⚠️ Обрезка не выполнена, используем исходное видео.")
    
    base = os.path.splitext(os.path.basename(source_for_test))[0]
    original_size = os.path.getsize(source_for_test)
    
    crf_values = [24, 18, 14]
    methods = [
        ('Direct', convert_direct, 'direct'),
        ('Frames', convert_frames, 'frames')
    ]
    
    results = []  # список кортежей (method_name, crf, size)
    
    print(f"\n📁 Тестовый файл: {source_for_test} ({bytes_to_human(original_size)})")
    if source_is_cut:
        print(f"   (обрезанная версия исходного {test_file})")
    print(f"📁 Результаты будут сохранены в: {output_dir}\n")
    
    for method_name, func, suffix in methods:
        for crf in crf_values:
            out_filename = f"{base}_crf{crf}_{suffix}.mp4"
            out_path = os.path.join(output_dir, out_filename)
            print(f"🔄 {method_name} CRF {crf}...", end=' ')
            success, err = func(source_for_test, out_path, crf)
            if success:
                size = os.path.getsize(out_path)
                results.append((method_name, crf, size))
                print(f"✅ {bytes_to_human(size)}")
            else:
                print(f"❌ Ошибка: {err[:100]}")
    
    # Вывод сводной таблицы
    print("\n" + "-"*70)
    print("📊 СВОДНАЯ ТАБЛИЦА")
    print("-"*70)
    print(f"{'Метод':<8} {'CRF':<5} {'Размер':<12} {'% от исходного':<15} {'Комментарий'}")
    print("-"*70)
    
    for method, crf, size in results:
        percent = (size / original_size) * 100
        comment = ""
        if method == 'Direct' and crf == crf_default:
            comment = "(режим по умолчанию)"
        elif method == 'Frames' and crf == crf_default:
            comment = "(Frames без звука)"
        print(f"{method:<8} {crf:<5} {bytes_to_human(size):<12} {percent:>6.1f}%        {comment}")
    
    print("-"*70)
    print(f"\n📂 Все тестовые файлы сохранены в папке:\n   {output_dir}")
    if source_is_cut:
        print("   (включая обрезанную версию исходного видео)")
    print("   (Откройте их любым плеером для визуального сравнения качества)")
    print("="*70 + "\n")
    
    pause()

# ------------------------------------------------------------
# ОСНОВНАЯ ПРОГРАММА
# ------------------------------------------------------------

def main():
    global input_path, output_path, mode, crf_default

    # ЕСЛИ ХОТИТЕ ЗАПУСТИТЬ ТЕСТ, РАСКОММЕНТИРУЙТЕ СЛЕДУЮЩУЮ СТРОКУ
    #test_quality_comparison()
    #return  # возврат, чтобы не запускать основную конвертацию

    # Определяем исходную папку
    if not input_path:
        input_path = os.getcwd()
    input_path = os.path.abspath(input_path)

    # Определяем папку для результатов
    if not output_path:
        output_dir = os.path.join(input_path, "converted")
    else:
        output_dir = os.path.abspath(output_path)

    os.makedirs(output_dir, exist_ok=True)

    print("📁 Исходная папка:", input_path)
    print("📁 Папка для результатов:", output_dir)
    print("⚙️ Режим конвертации:", mode)
    print("⚙️ CRF (качество):", crf_default)
    print()

    # Собираем все .webm файлы
    webm_files = []
    for f in os.listdir(input_path):
        if f.lower().endswith('.webm'):
            full_path = os.path.join(input_path, f)
            if os.path.isfile(full_path):
                webm_files.append(f)

    total_files = len(webm_files)
    if total_files == 0:
        print("❌ WebM-файлы не найдены.")
        pause()
        return

    # Подсчитываем общий размер
    total_size = sum(os.path.getsize(os.path.join(input_path, f)) for f in webm_files)
    print(f"📊 Найдено файлов: {total_files}, общий размер: {bytes_to_human(total_size)}")
    print()

    # Статистика по конвертации
    stats = {
        'processed': 0,
        'success': 0,
        'skipped': 0,
        'errors': 0,
        'total_original': 0,
        'total_result': 0
    }

    for idx, filename in enumerate(webm_files, 1):
        src_path = os.path.join(input_path, filename)
        base = os.path.splitext(filename)[0]
        dst_filename = base + '.mp4'
        dst_path = os.path.join(output_dir, dst_filename)

        # Проверка на существование выходного файла
        if os.path.exists(dst_path):
            print(f"⏭️ [{idx}/{total_files}] {filename} -> {dst_filename} (уже существует, пропуск)")
            stats['skipped'] += 1
            stats['processed'] += 1
            continue

        print(f"🔄 [{idx}/{total_files}] {filename} -> {dst_filename}")

        success = False
        error_msg = ""
        original_size = os.path.getsize(src_path)

        # Выбор метода
        if mode == "Direct":
            success, error_msg = convert_direct(src_path, dst_path, crf_default)
        elif mode == "Frames":
            success, error_msg = convert_frames(src_path, dst_path, crf_default)
        else:  # Auto
            success, error_msg = convert_direct(src_path, dst_path, crf_default)
            if not success:
                print("   ⚠️ Direct не сработал, пробуем Frames...")
                success, error_msg = convert_frames(src_path, dst_path, crf_default)

        if success:
            result_size = os.path.getsize(dst_path)
            stats['success'] += 1
            stats['total_original'] += original_size
            stats['total_result'] += result_size
            print(f"   ✅ Успешно ({bytes_to_human(original_size)} -> {bytes_to_human(result_size)})")
        else:
            stats['errors'] += 1
            print(f"   ❌ Ошибка: {error_msg[:200]}")

        stats['processed'] += 1

        # Прогресс после каждых 5 файлов или последнего
        if idx % 5 == 0 or idx == total_files:
            print(f"   ... прогресс: {idx}/{total_files} обработано")
            print()

    # Итоговая статистика
    print("\n" + "="*50)
    print("🏁 КОНВЕРТАЦИЯ ЗАВЕРШЕНА")
    print("="*50)
    print(f"📊 Всего файлов в папке: {total_files}")
    print(f"✅ Успешно: {stats['success']}")
    print(f"⏭️ Пропущено (уже есть MP4): {stats['skipped']}")
    print(f"❌ Ошибок: {stats['errors']}")

    if stats['success'] > 0:
        orig_h = bytes_to_human(stats['total_original'])
        res_h = bytes_to_human(stats['total_result'])
        print(f"\n📈 Суммарный объём успешно обработанных:")
        print(f"   Исходные WebM: {orig_h}")
        print(f"   Результат MP4: {res_h}")
        if stats['total_original'] > 0:
            ratio = (stats['total_result'] / stats['total_original']) * 100
            print(f"   Соотношение: {res_h} / {orig_h} = {ratio:.1f}%")
    else:
        print("\n📊 Нет новых сконвертированных файлов.")

    print("\n👋 Программа завершена.")
    pause()

if __name__ == "__main__":
    main()