import os
import time
import sys
from src.core.ffmpeg_wrapper import convert_video_to_webm

def run_benchmark():
    input_video = "vedio/Reshoot_stationary_202512310101_vaode.mp4"
    if not os.path.exists(input_video):
        print(f"Error: Video not found at {input_video}")
        return

    # Common options
    options = {
        'fps': 15,
        'crf': 30,
        'resize_enable': True,
        'max_width': 480,
        'max_height': 480,
        'duration_enable': True,
        'max_duration': 10  # Limit to 10s for quick test
    }

    print(f"Benchmarking with video: {input_video}")
    print(f"Options: {options}")
    print("-" * 50)

    # FFmpeg VP9/WebM Method
    output_webm = "benchmark_ffmpeg.webm"
    start_time = time.time()
    success, error = convert_video_to_webm(input_video, output_webm, options)
    ffmpeg_time = time.time() - start_time

    if success:
        ffmpeg_size = os.path.getsize(output_webm)
        print(f"[FFmpeg VP9/WebM Method]")
        print(f"  Time: {ffmpeg_time:.2f}s")
        print(f"  Size: {ffmpeg_size / 1024 / 1024:.2f} MB")
    else:
        print(f"[FFmpeg VP9/WebM Method] Failed: {error}")

    print("-" * 50)

if __name__ == "__main__":
    run_benchmark()
