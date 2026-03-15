import os
import subprocess
import sys
import tempfile
import shutil
import time
import json
from pathlib import Path

# ------------------------------------------------------------
# SETTINGS (can be changed)
# ------------------------------------------------------------


#⚠️⚠️⚠️ When copying a Windows path, use a special string type - r"..." , where ... is your folder path copied from Windows. This helps avoid an error where Python interprets \U or any other character after a backslash in the folder path as an escape sequence (and the error will definitely occur!)



# Path to the folder with source .webm files.
# If left empty, the current folder will be used.
input_path = r""

# Path to save the converted .mp4 files.
# If left empty, a folder 'converted' will be created in the source folder.
output_path = r""

# Conversion mode: "Direct", "Frames" or "Auto"
mode = "Auto"  # Direct / Frames / Auto

# Default CRF value for all conversions (lower value = higher quality / larger file size)
# Recommendations: 18 - excellent quality (visually lossless), 16 - very high, 14 - excessively high
crf_default = 18

# Path to the ffmpeg executable (if not in PATH, specify the full path)
FFMPEG_PATH = "ffmpeg"  # or "C:\\ffmpeg\\bin\\ffmpeg.exe" for Windows
FFPROBE_PATH = "ffprobe"  # needed to obtain video information



# ------------------------------------------------------------
# TEST MODE SETTINGS. You can use it to compare the resulting files and decide which crf you prefer. From my observations, I don't see a difference between the original and crf 24 (except for artifacts visible only under a microscope), and after crf 18 the file size increases significantly.
# ------------------------------------------------------------
# Specify the path to any .webm file for testing
test_file_path = r"D:\webm to mp4\пример.webm"  # ⚠️ REPLACE WITH A REAL FILE!

# Folder to save test results.
# If left empty, a folder "compare" will be created next to the script.
test_output_dir = r""

# Trimming mode for tests:
# "default" - process the whole video
# "cut"     - trim the first 30 seconds (to speed up testing)
test_cut_mode = "cut"  # default / cut

# To run the test mode, uncomment lines 300-301 at the beginning of the main program. (With time and program updates, line numbers may change, and the developer might forget about it. Read the comments in that area - you won't go wrong.)

# ------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------

def bytes_to_human(size):
    """Converts bytes to a human-readable format (B, KB, MB, GB)."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def get_video_info(video_path):
    """Gets duration and fps of the video using ffprobe."""
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
        # Duration
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
    Creates a trimmed version of the video according to the mode.
    mode: "cutted" or "extracutted" (but currently always trims the first 30 seconds)
    Returns (True, dst_path) on success, (False, None) on failure.
    """
    # Get duration
    duration, _ = get_video_info(src)
    if duration is None:
        # Alternative method
        try:
            cmd = [FFPROBE_PATH, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', src]
            output = subprocess.check_output(cmd, universal_newlines=True).strip()
            duration = float(output)
        except:
            print("   ⚠️ Could not determine video duration.")
            return False, None

    print(f"   ✂️ Trimming video (first 30 seconds)...")
    cmd = [
        FFMPEG_PATH, '-i', src,
        '-t', '30',          # limit to 30 seconds
        '-c:v', 'libx264', '-c:a', 'aac',  # re-encode to be safe
        '-y', dst
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        err = result.stderr.decode('utf-8', errors='replace')
        print(f"   ⚠️ Error during trimming: {err[:200]}")
        return False, None
    return True, dst

def convert_direct(src, dst, crf):
    """Direct conversion via ffmpeg with the specified CRF."""
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
    Conversion by extracting frames with the specified CRF.
    NOTE: audio is not preserved (since we assemble only video).
    """
    # Get FPS of the source video
    _, fps = get_video_info(src)
    if fps is None:
        fps = 30.0
        print("   ⚠️ Could not determine FPS, using 30")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract frames
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

        # Assemble video from frames with CRF
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
    """Waits for Enter press before closing (if running in interactive mode)."""
    if sys.stdin.isatty():
        input("\nPress Enter to exit...")

# ------------------------------------------------------------
# TEST MODULE FOR CRF COMPARISON
# ------------------------------------------------------------

def test_quality_comparison():
    """
    Test: converts one file (possibly trimmed) by two methods with three different CRF values,
    outputs a size table and saves all files to a convenient folder.
    """
    print("\n" + "="*70)
    print("🧪 TEST MODE: Comparison of methods and CRF levels")
    print("="*70)
    
    test_file = test_file_path
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        print("   Please specify the correct path in the test_file_path variable.")
        pause()
        return
    
    # Determine the base folder for saving results
    if test_output_dir:
        base_dir = test_output_dir
    else:
        # Folder next to the script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.join(script_dir, "compare")
    
    os.makedirs(base_dir, exist_ok=True)
    
    # Create a subfolder with the current date and time
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(base_dir, timestamp)
    os.makedirs(output_dir, exist_ok=True)
    
    # If video needs to be trimmed, create a trimmed copy in the same folder
    source_for_test = test_file
    source_is_cut = False
    if test_cut_mode == "cut":
        # Trim the first 30 seconds
        cut_filename = f"cut_{os.path.basename(test_file)}.mp4"
        cut_path = os.path.join(output_dir, cut_filename)
        success_cut, cut_file = cut_video_segments(test_file, cut_path, test_cut_mode)  # can pass any mode, the function ignores it anyway
        if success_cut:
            source_for_test = cut_file
            source_is_cut = True
            print(f"✂️ Video trimmed (mode: {test_cut_mode}) -> {cut_filename}")
        else:
            print("   ⚠️ Trimming failed, using original video.")
    
    base = os.path.splitext(os.path.basename(source_for_test))[0]
    original_size = os.path.getsize(source_for_test)
    
    crf_values = [24, 18, 14]
    methods = [
        ('Direct', convert_direct, 'direct'),
        ('Frames', convert_frames, 'frames')
    ]
    
    results = []  # list of tuples (method_name, crf, size)
    
    print(f"\n📁 Test file: {source_for_test} ({bytes_to_human(original_size)})")
    if source_is_cut:
        print(f"   (trimmed version of {test_file})")
    print(f"📁 Results will be saved in: {output_dir}\n")
    
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
                print(f"❌ Error: {err[:100]}")
    
    # Output summary table
    print("\n" + "-"*70)
    print("📊 SUMMARY TABLE")
    print("-"*70)
    print(f"{'Method':<8} {'CRF':<5} {'Size':<12} {'% of original':<15} {'Comment'}")
    print("-"*70)
    
    for method, crf, size in results:
        percent = (size / original_size) * 100
        comment = ""
        if method == 'Direct' and crf == crf_default:
            comment = "(default mode)"
        elif method == 'Frames' and crf == crf_default:
            comment = "(Frames without audio)"
        print(f"{method:<8} {crf:<5} {bytes_to_human(size):<12} {percent:>6.1f}%        {comment}")
    
    print("-"*70)
    print(f"\n📂 All test files are saved in the folder:\n   {output_dir}")
    if source_is_cut:
        print("   (including the trimmed version of the original video)")
    print("   (Open them with any player for visual quality comparison)")
    print("="*70 + "\n")
    
    pause()

# ------------------------------------------------------------
# MAIN PROGRAM
# ------------------------------------------------------------

def main():
    global input_path, output_path, mode, crf_default

    # IF YOU WANT TO RUN THE TEST, UNCOMMENT THE FOLLOWING LINE
    #test_quality_comparison()
    #return  # return to avoid running the main conversion

    # Determine source folder
    if not input_path:
        input_path = os.getcwd()
    input_path = os.path.abspath(input_path)

    # Determine output folder
    if not output_path:
        output_dir = os.path.join(input_path, "converted")
    else:
        output_dir = os.path.abspath(output_path)

    os.makedirs(output_dir, exist_ok=True)

    print("📁 Source folder:", input_path)
    print("📁 Output folder:", output_dir)
    print("⚙️ Conversion mode:", mode)
    print("⚙️ CRF (quality):", crf_default)
    print()

    # Collect all .webm files
    webm_files = []
    for f in os.listdir(input_path):
        if f.lower().endswith('.webm'):
            full_path = os.path.join(input_path, f)
            if os.path.isfile(full_path):
                webm_files.append(f)

    total_files = len(webm_files)
    if total_files == 0:
        print("❌ No WebM files found.")
        pause()
        return

    # Calculate total size
    total_size = sum(os.path.getsize(os.path.join(input_path, f)) for f in webm_files)
    print(f"📊 Found files: {total_files}, total size: {bytes_to_human(total_size)}")
    print()

    # Conversion statistics
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

        # Check if output file already exists
        if os.path.exists(dst_path):
            print(f"⏭️ [{idx}/{total_files}] {filename} -> {dst_filename} (already exists, skipping)")
            stats['skipped'] += 1
            stats['processed'] += 1
            continue

        print(f"🔄 [{idx}/{total_files}] {filename} -> {dst_filename}")

        success = False
        error_msg = ""
        original_size = os.path.getsize(src_path)

        # Method selection
        if mode == "Direct":
            success, error_msg = convert_direct(src_path, dst_path, crf_default)
        elif mode == "Frames":
            success, error_msg = convert_frames(src_path, dst_path, crf_default)
        else:  # Auto
            success, error_msg = convert_direct(src_path, dst_path, crf_default)
            if not success:
                print("   ⚠️ Direct failed, trying Frames...")
                success, error_msg = convert_frames(src_path, dst_path, crf_default)

        if success:
            result_size = os.path.getsize(dst_path)
            stats['success'] += 1
            stats['total_original'] += original_size
            stats['total_result'] += result_size
            print(f"   ✅ Success ({bytes_to_human(original_size)} -> {bytes_to_human(result_size)})")
        else:
            stats['errors'] += 1
            print(f"   ❌ Error: {error_msg[:200]}")

        stats['processed'] += 1

        # Progress every 5 files or at the end
        if idx % 5 == 0 or idx == total_files:
            print(f"   ... progress: {idx}/{total_files} processed")
            print()

    # Final statistics
    print("\n" + "="*50)
    print("🏁 CONVERSION COMPLETED")
    print("="*50)
    print(f"📊 Total files in folder: {total_files}")
    print(f"✅ Successful: {stats['success']}")
    print(f"⏭️ Skipped (MP4 already exists): {stats['skipped']}")
    print(f"❌ Errors: {stats['errors']}")

    if stats['success'] > 0:
        orig_h = bytes_to_human(stats['total_original'])
        res_h = bytes_to_human(stats['total_result'])
        print(f"\n📈 Total size of successfully processed files:")
        print(f"   Source WebM: {orig_h}")
        print(f"   Result MP4: {res_h}")
        if stats['total_original'] > 0:
            ratio = (stats['total_result'] / stats['total_original']) * 100
            print(f"   Ratio: {res_h} / {orig_h} = {ratio:.1f}%")
    else:
        print("\n📊 No new converted files.")

    print("\n👋 Program finished.")
    pause()

if __name__ == "__main__":
    main()