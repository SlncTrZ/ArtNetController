#!/usr/bin/env python3
"""Remove all emoji from logger.info() calls in Python files"""

import re
from pathlib import Path

# Emoji to remove from logger calls (not from button text)
LOGGER_EMOJIS = [
    '📥', '📡', '✅', '🖥️', '📺', '🎵', '🧪',  # main_window.py
    '🌐', '🛑',  # timecode_receiver.py
    '🔐',  # hardware_manager.py
]

def remove_emojis_from_logger(file_path: Path):
    """Remove emojis from logger.info/debug/warning calls only"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Remove emojis only from logger calls
        for emoji in LOGGER_EMOJIS:
            # Pattern: logger.info(f"emoji text")
            pattern = rf'(logger\.(info|debug|warning|error)\(f?"){emoji} '
            replacement = r'\1'
            content = re.sub(pattern, replacement, content)
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            print(f"✓ Cleaned {file_path}")
            return True
        return False
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False

def main():
    """Process all Python files in src/"""
    src_dir = Path("src")
    files_changed = 0
    
    for py_file in src_dir.rglob("*.py"):
        if remove_emojis_from_logger(py_file):
            files_changed += 1
    
    print(f"\nDone! {files_changed} files cleaned.")

if __name__ == "__main__":
    main()
