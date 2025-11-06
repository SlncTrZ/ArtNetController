"""Clean emoji icons from log messages"""
import re

def clean_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove emojis from logger statements
    emoji_patterns = [
        ('🔌 ', ''),
        ('✅ ', ''),
        ('❌ ', ''),
        ('🎵 ', ''),
        ('⏱️ ', ''),
        ('🔧 ', ''),
        ('🌐 ', ''),
        ('🎹 ', ''),
        ('💡 ', ''),
        ('🎭 ', ''),
        ('🎬 ', ''),
        ('▶️  ', ''),
        ('⏸️  ', ''),
        ('⚠️  ', ''),
        ('🔍 ', ''),
        ('📦 ', ''),
        ('🔔 ', ''),
        ('🚫 ', ''),
        ('🌑 ', ''),
        ('🔄 ', ''),
        ('⏩ ', ''),
    ]
    
    for emoji, replacement in emoji_patterns:
        content = content.replace(emoji, replacement)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Cleaned {filepath}")

if __name__ == '__main__':
    clean_file('src/gui/tabs/record.py')
    print("Done!")
