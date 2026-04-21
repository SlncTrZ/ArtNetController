"""
Get Device ID for current machine
"""
import hashlib
import platform
import uuid
import subprocess

def get_device_id():
    """Get unique device ID based on hardware info"""
    # Get various hardware identifiers
    identifiers = []
    
    # 1. MAC Address
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                    for elements in range(0,2*6,2)][::-1])
    identifiers.append(f"MAC:{mac}")
    
    # 2. Machine name
    identifiers.append(f"HOST:{platform.node()}")
    
    # 3. Processor info
    identifiers.append(f"PROC:{platform.processor()}")
    
    # 4. Windows Product ID (if on Windows)
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["wmic", "csproduct", "get", "uuid"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    uuid_val = lines[1].strip()
                    identifiers.append(f"UUID:{uuid_val}")
    except:
        pass
    
    # Combine all identifiers
    combined = "|".join(identifiers)
    
    # Create SHA256 hash
    device_id = hashlib.sha256(combined.encode()).hexdigest()
    
    return device_id

if __name__ == "__main__":
    device_id = get_device_id()
    print("\n" + "="*70)
    print("  DEVICE ID - Máy hiện tại")
    print("="*70)
    print(f"\nDevice ID: {device_id}")
    print(f"\n Copy Device ID này để:")
    print(f"   1. Generate license mới với LicenseGenerator.exe")
    print(f"   2. Hoặc gửi cho admin để tạo license")
    print("="*70 + "\n")
