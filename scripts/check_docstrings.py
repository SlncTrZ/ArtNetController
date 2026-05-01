"""Check module docstrings format compliance."""
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

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
        lines = f.readlines()
    
    # Find module docstring
    first_line = 0
    while first_line < len(lines) and lines[first_line].strip().startswith('#'):
        first_line += 1
    
    if first_line < len(lines) and '"""' in lines[first_line]:
        # Get full docstring (first 3-5 lines usually)
        ds_lines = []
        for i in range(first_line, min(first_line + 50, len(lines))):
            ds_lines.append(lines[i].rstrip())
            if i > first_line and '"""' in lines[i]:
                break
        ds = '\n'.join(ds_lines)
        has_topic = 'Topic:' in ds
        has_updated = 'Last Updated:' in ds
        status = "OK" if (has_topic and has_updated) else "NEEDS FIX"
        short_ds = ds[:100].replace('\n', ' | ')
        print(f"{status}: {fpath} -> {short_ds}")
    else:
        print(f"NO DOCSTRING: {fpath} -> {lines[first_line].strip()[:60] if first_line < len(lines) else 'EMPTY'}")