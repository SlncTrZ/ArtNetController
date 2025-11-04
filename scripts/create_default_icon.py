"""
Tạo icon mặc định cho DMX Master
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_default_icon():
    """Tạo icon mặc định với chữ 'DMX'"""
    
    # Tạo ảnh 256x256
    img = Image.new('RGBA', (256, 256), (45, 45, 48, 255))  # Dark background
    draw = ImageDraw.Draw(img)
    
    # Vẽ border
    draw.rectangle([10, 10, 245, 245], outline=(0, 150, 255, 255), width=8)
    
    # Vẽ text "DMX"
    try:
        # Try to use a system font
        font = ImageFont.truetype("arial.ttf", 80)
    except:
        font = ImageFont.load_default()
    
    # Draw "DMX" text
    text = "DMX"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (256 - text_width) // 2
    y = (256 - text_height) // 2 - 20
    
    # Shadow
    draw.text((x+3, y+3), text, fill=(0, 0, 0, 180), font=font)
    # Main text
    draw.text((x, y), text, fill=(0, 200, 255, 255), font=font)
    
    # Sub text "MASTER"
    try:
        small_font = ImageFont.truetype("arial.ttf", 28)
    except:
        small_font = font
    
    subtext = "MASTER"
    bbox2 = draw.textbbox((0, 0), subtext, font=small_font)
    sub_width = bbox2[2] - bbox2[0]
    sub_x = (256 - sub_width) // 2
    sub_y = y + text_height + 10
    
    draw.text((sub_x, sub_y), subtext, fill=(180, 180, 180, 255), font=small_font)
    
    # Save as PNG first
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    assets_dir = os.path.join(project_root, 'assets')
    
    png_path = os.path.join(assets_dir, 'DMXMaster.png')
    img.save(png_path, 'PNG')
    print(f"✅ PNG saved: {png_path}")
    
    # Create ICO with multiple sizes
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    ico_path = os.path.join(assets_dir, 'DMXMaster_new.ico')
    
    img.save(ico_path, format='ICO', sizes=sizes)
    
    size_bytes = os.path.getsize(ico_path)
    print(f"✅ ICO saved: {ico_path}")
    print(f"   Size: {size_bytes:,} bytes ({size_bytes/1024:.1f} KB)")
    print(f"   Resolutions: {len(sizes)} levels")
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("🎨 CREATE DEFAULT ICON")
    print("=" * 60)
    create_default_icon()
    print("=" * 60)
