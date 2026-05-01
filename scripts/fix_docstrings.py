"""Auto-fix module docstrings to add Topic: and Last Updated: fields."""
import os, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TODAY = "2026-05-01"

files = [
    ('src/artnet/controller.py', 'artnet'),
    ('src/gui/main_window.py', 'gui'),
    ('src/gui/tabs/dmx_view.py', 'gui'),
    ('src/gui/tabs/hardware_manager.py', 'gui'),
    ('src/gui/tabs/record.py', 'gui'),
    ('src/gui/tabs/settings.py', 'gui'),
    ('src/gui/tabs/show_manager.py', 'gui'),
    ('src/gui/widgets/timeline_editor.py', 'gui'),
    ('src/gui/widgets/ip_info_widget.py', 'gui'),
    ('src/serial/serial_controller.py', 'serial'),
    ('src/serial/ioboard_protocol.py', 'serial'),
    ('src/serial/port_scanner.py', 'serial'),
    ('src/show/manager.py', 'show'),
    ('src/show/dmx_recorder.py', 'show'),
    ('src/system/config_manager.py', 'system'),
    ('src/system/timecode_receiver.py', 'system'),
    ('src/system/crash_reporter.py', 'system'),
    ('src/system/update_manager.py', 'system'),
    ('src/utils/license.py', 'utils'),
    ('src/utils/network.py', 'utils'),
    ('src/utils/network_utils.py', 'utils'),
    ('src/webserver/server.py', 'webserver'),
]

for fpath, topic in files:
    if not os.path.exists(fpath):
        print(f"MISSING: {fpath}")
        continue
    
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already has both fields
    if f'Topic: {topic}' in content and 'Last Updated:' in content:
        print(f"SKIP (OK): {fpath}")
        continue
    
    # Find the module docstring end (closing """)
    # Pattern: opening """ ... closing """
    # We need to find the FIRST """ pair (module docstring)
    lines = content.split('\n')
    
    # Find first non-comment, non-empty line
    first_code = 0
    while first_code < len(lines) and (lines[first_code].strip().startswith('#') or lines[first_code].strip() == ''):
        first_code += 1
    
    if first_code >= len(lines) or '"""' not in lines[first_code]:
        print(f"NO DOCSTRING: {fpath}")
        continue
    
    # Check if it's a one-liner like """something"""
    line = lines[first_code]
    if line.count('"""') >= 2 and not line.strip().endswith('"""'):
        # One-liner: """text"""
        # Convert to multi-line
        text = line.strip().strip('"').strip()
        lines[first_code] = f'{lines[first_code][:len(lines[first_code])-len(lines[first_code].lstrip())]}"""{text}'
        lines.insert(first_code + 1, '')
        lines.insert(first_code + 2, f'Topic: {topic}')
        lines.insert(first_code + 3, f'Last Updated: {TODAY}')
        lines.insert(first_code + 4, '"""')
        content = '\n'.join(lines)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"FIXED (one-liner): {fpath}")
        continue
    
    # Multi-line docstring: find closing """
    # The opening is on `first_code` line
    close_idx = None
    for i in range(first_code + 1, min(first_code + 100, len(lines))):
        if '"""' in lines[i]:
            close_idx = i
            break
    
    if close_idx is None:
        print(f"NO CLOSE: {fpath}")
        continue
    
    # Check if Topic and Last Updated already exist before close
    ds_block = '\n'.join(lines[first_code:close_idx+1])
    
    needs_topic = f'Topic: {topic}' not in ds_block
    needs_updated = 'Last Updated:' not in ds_block
    
    if not needs_topic and not needs_updated:
        print(f"SKIP (OK): {fpath}")
        continue
    
    # Insert before closing """
    insert_lines = []
    if needs_topic:
        insert_lines.append(f'Topic: {topic}')
    if needs_updated:
        insert_lines.append(f'Last Updated: {TODAY}')
    
    # Add blank line before metadata if closing """ follows content
    if lines[close_idx - 1].strip() and not lines[close_idx - 1].strip() == '':
        insert_lines.insert(0, '')
    
    for j, ins_line in enumerate(insert_lines):
        lines.insert(close_idx + j, ins_line)
    
    content = '\n'.join(lines)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"FIXED: {fpath} (+{len(insert_lines)} lines)")