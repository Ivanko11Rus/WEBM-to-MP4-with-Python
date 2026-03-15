import os
import subprocess
import sys
import tempfile
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
# Рекомендации: 24-22 - примерное значение для объёма как у оригинала; 18 - отличное качество (визуально lossless); 16 - очень высокое, 14 - избыточно высоко. Тесты показали, что значение 18 - имеет не слишком большой объём при замечательном качестве картинки, а crf 16 и 14 значительно тяжелее при невидимой без микроскопа разнице.
crf_default = 18

# Путь к исполняемому файлу ffmpeg (если не прописан в PATH, укажите полный путь)
FFMPEG_PATH = "ffmpeg"  # или "C:\\ffmpeg\\bin\\ffmpeg.exe" для Windows
FFPROBE_PATH = "ffprobe"  # нужен для получения информации о видео

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
    """Получает длительность и fps видео с помощью ffprobe (нужно для FPS)."""
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
        # FPS (длительность не используем, только fps)
        r_frame_rate = streams[0].get('r_frame_rate', '0/0')
        num, den = map(int, r_frame_rate.split('/'))
        fps = num / den if den != 0 else 30.0
        return None, fps  # длительность не возвращаем, она не нужна
    except Exception:
        return None, None

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
# ОСНОВНАЯ ПРОГРАММА
# ------------------------------------------------------------

def main():
    global input_path, output_path, mode, crf_default

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