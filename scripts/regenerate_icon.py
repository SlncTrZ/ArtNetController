"""
Script tạo lại icon DMXMaster.ico với kích thước tối ưu
Sử dụng Pillow để tạo multi-resolution icon
"""

from PIL import Image
import os

def create_optimized_icon():
    """Tạo icon tối ưu từ ảnh gốc"""
    
    # Đường dẫn
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    assets_dir = os.path.join(project_root, 'assets')
    
    # Tìm file PNG gốc (nếu có) hoặc dùng ICO cũ
    source_file = None
    for ext in ['.png', '.jpg', '.jpeg', '.ico']:
        test_path = os.path.join(assets_dir, f'DMXMaster{ext}')
        if os.path.exists(test_path):
            source_file = test_path
            break
    
    if not source_file:
        print("❌ Không tìm thấy file ảnh nguồn trong assets/")
        return False
    
    print(f"📁 Đang đọc: {source_file}")
    
    try:
        # Đọc ảnh gốc
        img = Image.open(source_file)
        
        # Chuyển sang RGBA nếu cần
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        print(f"📐 Kích thước gốc: {img.size}")
        
        # Tạo các kích thước chuẩn cho Windows icon
        # Windows icon nên có: 16x16, 32x32, 48x48, 256x256
        sizes = [(16, 16), (32, 32), (48, 48), (128, 128), (256, 256)]
        
        # Resize và tạo danh sách các icon
        icon_images = []
        for size in sizes:
            resized = img.resize(size, Image.Resampling.LANCZOS)
            icon_images.append(resized)
            print(f"  ✅ Tạo: {size[0]}x{size[1]}")
        
        # Lưu icon mới
        output_path = os.path.join(assets_dir, 'DMXMaster_new.ico')
        
        # Lưu icon mới - Pillow tự động lưu tất cả sizes
        img.save(
            output_path,
            format='ICO',
            sizes=sizes  # Pass list of sizes
        )
        
        print(f"💾 Icon mới đã tạo: DMXMaster_new.ico (cần thay thế thủ công)")
        
        # Kiểm tra kích thước
        new_size = os.path.getsize(output_path)
        print(f"\n✅ Icon mới đã tạo:")
        print(f"   📁 {output_path}")
        print(f"   📊 Kích thước: {new_size:,} bytes ({new_size/1024:.1f} KB)")
        print(f"   🎨 Độ phân giải: {len(sizes)} levels (16-256px)")
        
        if new_size < 100000:  # < 100KB
            print(f"   ✅ Kích thước tối ưu cho PyInstaller!")
        else:
            print(f"   ⚠️  Vẫn còn hơi nặng, nhưng chấp nhận được")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("🎨 REGENERATE ICON - DMX Master V2.0")
    print("=" * 60)
    
    success = create_optimized_icon()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ HOÀN THÀNH! Icon đã được tối ưu hóa")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ THẤT BẠI! Vui lòng kiểm tra lỗi")
        print("=" * 60)
