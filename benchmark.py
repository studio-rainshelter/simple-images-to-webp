import os
import time
import sys
from src.core.pillow_webp_encoder import convert_video_to_webp_pillow
from src.core.ffmpeg_wrapper import convert_video_to_webp

def run_benchmark():
    input_video = "vedio/Reshoot_stationary_202512310101_vaode.mp4"
    if not os.path.exists(input_video):
        print(f"Error: Video not found at {input_video}")
        return

    # Common options
    options = {
        'fps': 15,
        'quality': 75,
        'resize_enable': True,
        'max_width': 480,
        'max_height': 480,
        'loop': 0,
        'duration_enable': True,
        'max_duration': 10  # Limit to 10s for quick test
    }

    print(f"Benchmarking with video: {input_video}")
    print(f"Options: {options}")
    print("-" * 50)

    # 1. Pillow Method
    output_pillow = "benchmark_pillow.webp"
    start_time = time.time()
    result_pillow = convert_video_to_webp_pillow(input_video, output_pillow, options)
    pillow_time = time.time() - start_time
    
    if result_pillow.success:
        pillow_size = os.path.getsize(output_pillow)
        print(f"[Pillow Method]")
        print(f"  Time: {pillow_time:.2f}s")
        print(f"  Size: {pillow_size / 1024 / 1024:.2f} MB")
    else:
        print(f"[Pillow Method] Failed: {result_pillow.error}")
        pillow_size = -1

    print("-" * 50)

    # 2. FFmpeg Method
    output_ffmpeg = "benchmark_ffmpeg.webp"
    start_time = time.time()
    success, error = convert_video_to_webp(input_video, output_ffmpeg, options)
    ffmpeg_time = time.time() - start_time

    if success:
        ffmpeg_size = os.path.getsize(output_ffmpeg)
        print(f"[FFmpeg Direct Method]")
        print(f"  Time: {ffmpeg_time:.2f}s")
        print(f"  Size: {ffmpeg_size / 1024 / 1024:.2f} MB")
    else:
        print(f"[FFmpeg Direct Method] Failed: {error}")
        ffmpeg_size = -1

    print("-" * 50)
    
    if pillow_size > 0 and ffmpeg_size > 0:
        ratio = (ffmpeg_size - pillow_size) / ffmpeg_size * 100
        print(f"Comparison:")
        print(f"  Pillow is {ratio:.1f}% smaller than FFmpeg")

if __name__ == "__main__":
    run_benchmark()
