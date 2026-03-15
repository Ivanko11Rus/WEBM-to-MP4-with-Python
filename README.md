English (russian will be there too):

# 🎥 WebM to MP4 Converter

Two Python scripts for batch converting **WebM** video files to **MP4** using FFmpeg.  
Supports three conversion modes, quality control via CRF, and automatic skipping of existing output files.

- **`Webm_To_Mp4_Basic.py`** – simple batch converter.
- **`Webm_To_Mp4_Testing.py`** – includes a test module to compare different CRF values on a single file.

---

## ⚙️ Basic Version – `Webm_To_Mp4_Basic.py`

### 📌 Features
- Converts all `.webm` files from a specified folder (or the current folder) to `.mp4`.
- Three conversion modes:
  - **Direct** – fast direct FFmpeg conversion.
  - **Frames** – frame-by-frame processing (slower, but reliable for problematic files).
  - **Auto** – tries Direct first; if it fails, falls back to Frames.
- Quality controlled by **CRF** (Constant Rate Factor): **lower value = higher quality / larger file**.
- Automatically skips files that already have an MP4 version in the output folder.
- Clear progress output and final statistics.

### 🔧 Settings (edit at the top of the file)
```python
input_path = r""          # folder with source WebM files (empty = current folder)
output_path = r""         # folder for MP4 results (empty = creates "converted" subfolder)
mode = "Auto"             # Direct / Frames / Auto
crf_default = 18          # default quality (18 recommended – visually lossless)
FFMPEG_PATH = "ffmpeg"    # path to ffmpeg (if not in PATH, specify full path)
FFPROBE_PATH = "ffprobe"  
⚠️ Windows paths: Always use r"..." (raw string) to avoid escape sequence errors, e.g. r"C:\Users\Name\Videos".

📁 Source folder: D:\video
📁 Output folder: D:\video\converted
⚙️ Conversion mode: Auto
⚙️ CRF (quality): 18

📊 Found files: 5, total size: 120.5 MB

🔄 [1/5] clip1.webm -> clip1.mp4
   ✅ Success (12.3 MB -> 15.1 MB)
🔄 [2/5] clip2.webm -> clip2.mp4
   ⚠️ Direct failed, trying Frames...
   ✅ Success (24.7 MB -> 26.3 MB)
   ... progress: 5/5 processed

🏁 CONVERSION COMPLETED
✅ Successful: 5  ⏭️ Skipped: 0  ❌ Errors: 0

📈 Total size of successfully processed files:
   Source WebM: 120.5 MB
   Result MP4: 141.2 MB
   Ratio: 141.2 MB / 120.5 MB = 117.2%

🧪 Testing Version – Webm_To_Mp4_Testing.py
Includes everything from the basic version, plus a test module that converts one file with different CRF settings and both conversion methods, helping you choose the optimal CRF.


➕ Additional Test Settings

test_file_path = r"D:\video\sample.webm"   # path to a .webm file for testing
test_output_dir = r""                       # folder for test results (empty = creates "compare" next to script)
test_cut_mode = "cut"                        # "default" – whole video, "cut" – trim first 30 sec (faster)
🧪 How to Run the Test
Set test_file_path to a real .webm file.

In the main() function, uncomment these two lines:

#test_quality_comparison()
#return
Run the script.

📊 Tested CRF Values
The test uses three CRF values:

CRF 24 – size close to original (typically 90–101% of original). Good for a baseline.

CRF 18 – optimal balance: visually lossless, size noticeably larger than original.

CRF 14 – excessively high quality; file size grows disproportionately, with negligible visual improvement.

Both Direct and Frames methods are tested for each CRF.

🔍 What the Test Does
(Optional) Trims the first 30 seconds of the video to speed up testing.

Converts the (trimmed) video with both methods and all three CRF values.

Saves all generated files in a timestamped subfolder inside the compare folder.

Prints a summary table with file sizes and percentages.

📈 Example Test Output

🧪 TEST MODE: Comparison of methods and CRF levels
   ✂️ Trimming video (first 30 seconds)...
✂️ Video trimmed (mode: cut) -> cut_sample.mp4

📁 Test file: cut_sample.mp4 (2.1 MB)
📁 Results will be saved in: compare\20250315_143022

🔄 Direct CRF 24... ✅ 2.0 MB
🔄 Direct CRF 18... ✅ 2.4 MB
🔄 Direct CRF 14... ✅ 3.2 MB
🔄 Frames CRF 24... ✅ 2.1 MB
🔄 Frames CRF 18... ✅ 2.5 MB
🔄 Frames CRF 14... ✅ 3.3 MB

📊 SUMMARY TABLE
Method   CRF  Size       % of original  Comment
Direct   24   2.0 MB     95.2%          
Direct   18   2.4 MB     114.3%         (default mode)
Direct   14   3.2 MB     152.4%         
Frames   24   2.1 MB     100.0%         
Frames   18   2.5 MB     119.0%         
Frames   14   3.3 MB     157.1%         

📂 All test files are saved in the folder:
   compare\20250315_143022
   (including the trimmed version of the original video)
   (Open them with any player for visual quality comparison)

📦 Requirements
FFmpeg installed and accessible from the command line (or set FFMPEG_PATH/FFPROBE_PATH to the full executable paths).

Python 3.6+ (only standard libraries used – no extra installations needed).

🚀 Running the Scripts
Save the desired .py file.

Edit the settings at the top if needed.

Double-click the file or run from terminal:


python Webm_To_Mp4_Basic.py
Follow the console output – the program shows progress and pauses at the end (press Enter to close).

🙏 Acknowledgements
Special thanks to @anttiluode for the inspiration behind the three conversion modes (Direct, Frames, Auto).
His original WebP2Mp4-Converter project (also MIT licensed) introduced the idea of handling problematic WebP animations via frame extraction, which we adapted for WebM videos.

📝 License
This project is open-source and available under the MIT License.


Русский


🎥 Конвертер WebM в MP4
Два Python-скрипта для пакетной конвертации видео из формата WebM в MP4 с использованием FFmpeg.
Поддерживаются три режима конвертации, настройка качества через CRF и автоматический пропуск уже существующих выходных файлов.

Webm_To_Mp4_Basic.py – простая программа для пакетной конвертации.

Webm_To_Mp4_Testing.py – включает тестовый модуль для сравнения разных значений CRF на одном файле.

⚙️ Базовая версия – Webm_To_Mp4_Basic.py

📌 Возможности
Конвертирует все .webm файлы из указанной папки (или текущей) в .mp4.

Три режима:

Direct – быстрая прямая конвертация FFmpeg.

Frames – покадровая обработка (медленно, но надёжно для проблемных файлов).

Auto – сначала пробует Direct, при ошибке переключается на Frames.

Настройка качества через CRF (Constant Rate Factor): меньше значение = выше качество / больше размер.

Автоматический пропуск файлов, для которых уже есть MP4 в выходной папке.

Понятный вывод прогресса и итоговая статистика.

🔧 Настройки (в начале файла)

input_path = r""          # папка с исходными WebM (пусто = текущая папка)
output_path = r""         # папка для результатов (пусто = создаст подпапку "converted")
mode = "Auto"             # Direct / Frames / Auto
crf_default = 18          # качество по умолчанию (18 рекомендуется – визуально без потерь)
FFMPEG_PATH = "ffmpeg"    # путь к ffmpeg (если не в PATH, укажите полный путь)
FFPROBE_PATH = "ffprobe"  
⚠️ При копировании пути с Windows используйте особый тип строки - r"...", где вместо ... Ваш путь к папке, скопированный из Windows. Это поможет избежать ошибки, при которой Python воспримет \U или любой другой символ после косой черты в пути к папке как команду (а ошибка точно будет!).

🖥️ Пример вывода

📁 Исходная папка: D:\video
📁 Папка для результатов: D:\video\converted
⚙️ Режим конвертации: Auto
⚙️ CRF (качество): 18

📊 Найдено файлов: 5, общий размер: 120.5 МБ

🔄 [1/5] clip1.webm -> clip1.mp4
   ✅ Успешно (12.3 МБ -> 15.1 МБ)
🔄 [2/5] clip2.webm -> clip2.mp4
   ⚠️ Direct не сработал, пробуем Frames...
   ✅ Успешно (24.7 МБ -> 26.3 МБ)
   ... прогресс: 5/5 обработано

🏁 КОНВЕРТАЦИЯ ЗАВЕРШЕНА
✅ Успешно: 5  ⏭️ Пропущено: 0  ❌ Ошибок: 0

📈 Суммарный объём успешно обработанных:
   Исходные WebM: 120.5 МБ
   Результат MP4: 141.2 МБ
   Соотношение: 141.2 МБ / 120.5 МБ = 117.2%

🧪 Версия с тестированием – Webm_To_Mp4_Testing.py
Включает всё то же, что и базовая версия, плюс тестовый модуль, который конвертирует один файл с разными CRF и обоими методами, помогая выбрать оптимальное значение.

➕ Дополнительные настройки тестирования

test_file_path = r"D:\video\sample.webm"   # путь к .webm файлу для теста
test_output_dir = r""                       # папка для результатов теста (пусто = создаст "compare" рядом со скриптом)
test_cut_mode = "cut"                        # "default" – всё видео, "cut" – обрезать первые 30 сек (быстрее)

🧪 Как запустить тест
Укажите реальный путь к .webm файлу в test_file_path.

В функции main() раскомментируйте эти две строки:

#test_quality_comparison()
#return
Запустите скрипт.

📊 Тестируемые значения CRF
В тесте используются три значения CRF:

CRF 24 – размер близок к исходному (обычно 90–101% от оригинала).

CRF 18 – оптимальный баланс: визуально без потерь, размер больше оригинала.

CRF 14 – избыточно высокое качество; размер растёт непропорционально, при этом визуальное улучшение часто незаметно.

Для каждого CRF тестируются оба метода: Direct и Frames.

🔍 Что делает тест
(Опционально) обрезает первые 30 секунд видео для ускорения.

Конвертирует (обрезанное) видео обоими методами со всеми тремя CRF.

Сохраняет все полученные файлы в подпапку с меткой времени внутри папки compare.

Выводит сводную таблицу с размерами и процентами.

📈 Пример вывода теста

🧪 ТЕСТОВЫЙ РЕЖИМ: Сравнение методов и уровней CRF
   ✂️ Обрезка видео (первые 30 секунд)...
✂️ Видео обрезано (режим: cut) -> cut_sample.mp4

📁 Тестовый файл: cut_sample.mp4 (2.1 МБ)
📁 Результаты будут сохранены в: compare\20250315_143022

🔄 Direct CRF 24... ✅ 2.0 МБ
🔄 Direct CRF 18... ✅ 2.4 МБ
🔄 Direct CRF 14... ✅ 3.2 МБ
🔄 Frames CRF 24... ✅ 2.1 МБ
🔄 Frames CRF 18... ✅ 2.5 МБ
🔄 Frames CRF 14... ✅ 3.3 МБ

📊 СВОДНАЯ ТАБЛИЦА
Метод   CRF  Размер     % от исходного  Комментарий
Direct  24   2.0 МБ     95.2%          
Direct  18   2.4 МБ     114.3%         (режим по умолчанию)
Direct  14   3.2 МБ     152.4%         
Frames  24   2.1 МБ     100.0%         
Frames  18   2.5 МБ     119.0%         
Frames  14   3.3 МБ     157.1%         

📂 Все тестовые файлы сохранены в папке:
   compare\20250315_143022
   (включая обрезанную версию исходного видео)
   (Откройте их любым плеером для визуального сравнения качества)

📦 Требования к системе
Установленный FFmpeg (доступный из командной строки, либо пропишите полный путь в FFMPEG_PATH/FFPROBE_PATH).

Python 3.6+ (используются только стандартные библиотеки – ничего дополнительно устанавливать не нужно).

🚀 Запуск скриптов
Сохраните нужный .py файл.

При необходимости отредактируйте настройки в начале.

Запустите двойным щелчком или из командной строки:


python Webm_To_Mp4_Basic.py
Следуйте выводу в консоли – программа покажет прогресс и остановится в конце (нажмите Enter для выхода).

🙏 Благодарности
Особая благодарность @anttiluode за идею трёх режимов конвертации (Direct, Frames, Auto).
Его оригинальный проект WebP2Mp4-Converter (также под лицензией MIT) познакомил нас с концепцией обработки проблемных WebP-анимаций через покадровое извлечение, которую мы адаптировали для WebM-видео.

📝 Лицензия
Этот проект является открытым и доступен под лицензией MIT.

P.S. Оказывается писать readme сложнее чем питонировать.