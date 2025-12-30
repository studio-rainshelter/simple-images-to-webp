
import os
import sys
import shutil
from PIL import Image
from pathlib import Path

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.core.webp_converter import convert_single, ConvertResult

def create_test_image(path, size=(100, 100), color=(255, 0, 0)):
    img = Image.new('RGB', size, color)
    img.save(path)
    return path

def test_conversion_options():
    test_dir = os.path.join(project_root, 'tests', 'temp_output')
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)

    src_image_path = os.path.join(test_dir, 'test_source.png')
    create_test_image(src_image_path, size=(200, 200))

    print("--- Test 1: WebP Quality ---")
    # Low quality
    options_low = {'quality': 10}
    res_low = convert_single((src_image_path, test_dir, options_low))
    print(f"Low Quality (10) Size: {res_low.converted_size} bytes")

    # High quality
    options_high = {'quality': 100}
    res_high = convert_single((src_image_path, test_dir, options_high))
    print(f"High Quality (100) Size: {res_high.converted_size} bytes")
    
    # Ideally high quality should be larger, but for simple red square it might be similar or small difference.
    # Let's clean up
    os.remove(res_low.dst_path)
    os.remove(res_high.dst_path)

    print("\n--- Test 2: Resizing ---")
    # Resize to 50x50
    options_resize = {
        'resize_enable': True,
        'resize_width': 50,
        'resize_height': 50,
        'keep_ratio': False
    }
    res_resize = convert_single((src_image_path, test_dir, options_resize))
    
    with Image.open(res_resize.dst_path) as img:
        print(f"Resized Image Size: {img.size}")
        if img.size == (50, 50):
            print("PASS: Resizing dimensions correct")
        else:
            print(f"FAIL: Expected (50, 50), got {img.size}")

    print("\n--- Test 3: Keep Ratio ---")
    # Source is 200x200. Target 100x50. Keep ratio -> should be 50x50 to fit? 
    # Wait, Image.thumbnail fits within the box.
    # If 200x200 resized to 100x50 with keep ratio, it should be 50x50 (limited by height)
    
    options_ratio = {
        'resize_enable': True,
        'resize_width': 100,
        'resize_height': 50,
        'keep_ratio': True
    }
    res_ratio = convert_single((src_image_path, test_dir, options_ratio))
    
    with Image.open(res_ratio.dst_path) as img:
        print(f"Ratio Preserved Image Size: {img.size}")
        if img.size == (50, 50):
            print("PASS: Aspect ratio preserved (limited by height)")
        else:
            print(f"FAIL: Expected (50, 50), got {img.size}")

    # Cleanup
    shutil.rmtree(test_dir)

if __name__ == "__main__":
    test_conversion_options()
