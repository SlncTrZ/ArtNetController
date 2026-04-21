"""
Quick License Generator Script
Generate license for a specific Device ID
"""

import sys
import json
import base64
import uuid
from datetime import datetime
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend


def load_private_key():
    """Load RSA private key"""
    key_path = Path("tools/rsa_keys/private_key.pem")
    
    if not key_path.exists():
        print(f"❌ Error: Private key not found at {key_path}")
        print("   Run tools/Generate_RSA_Keys.bat first")
        return None
    
    try:
        with open(key_path, 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        print(f"✅ Private key loaded: {key_path}")
        return private_key
    except Exception as e:
        print(f"❌ Error loading private key: {e}")
        return None


def generate_license(device_id, customer_email="customer@example.com", license_type="perpetual"):
    """Generate license for device"""
    
    print(f"\n{'='*70}")
    print(f"Generating License")
    print(f"{'='*70}")
    
    # Validate device ID
    if len(device_id) != 64:
        print(f"❌ Error: Device ID must be exactly 64 characters")
        print(f"   Got: {len(device_id)} characters")
        return None
    
    try:
        int(device_id, 16)  # Validate hex
    except ValueError:
        print(f"❌ Error: Device ID must be a valid hex string")
        return None
    
    print(f"✅ Device ID validated: {device_id[:16]}...{device_id[-16:]}")
    
    # Load private key
    private_key = load_private_key()
    if not private_key:
        return None
    
    # Generate license data
    license_id = str(uuid.uuid4())
    issued_date = datetime.now().isoformat()
    
    # CRITICAL: Use pipe separators (device_id|license_id|issued_date)
    # This matches the verification logic in src/utils/license.py
    message = f"{device_id}|{license_id}|{issued_date}"
    message_bytes = message.encode('utf-8')
    
    print(f"\n📝 License Information:")
    print(f"   Device ID:      {device_id}")
    print(f"   License ID:     {license_id}")
    print(f"   Customer:       {customer_email}")
    print(f"   Issued Date:    {issued_date}")
    print(f"   License Type:   {license_type}")
    
    # Sign the message
    try:
        signature = private_key.sign(
            message_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        print(f"   Signature:      {signature_b64[:50]}...")
        
    except Exception as e:
        print(f"❌ Error signing license: {e}")
        return None
    
    # Create license JSON
    license_data = {
        "device_id": device_id,
        "license_id": license_id,
        "issued_date": issued_date,
        "customer_email": customer_email,
        "license_type": license_type,
        "version": "1.3.0",
        "signature": signature_b64
    }
    
    # Save to file
    output_dir = Path("tools/generated_licenses")
    output_dir.mkdir(exist_ok=True)
    
    filename = f"license_{device_id[:16]}.json"
    output_path = output_dir / filename
    
    with open(output_path, 'w') as f:
        json.dump(license_data, f, indent=2)
    
    print(f"\n✅ License generated successfully!")
    print(f"   Saved to: {output_path}")
    
    print(f"\n{'='*70}")
    print(f"License JSON (copy this to customer):")
    print(f"{'='*70}")
    print(json.dumps(license_data, indent=2))
    print(f"{'='*70}")
    
    return license_data


if __name__ == "__main__":
    # Device ID to generate license for
    DEVICE_ID = "827603596daa140eba04dca516eaa13bb1b0183f0ff3d691982cd40f49dcb669"
    CUSTOMER_EMAIL = "customer@example.com"  # Change this
    LICENSE_TYPE = "perpetual"  # perpetual or trial
    
    print("🔑 DMX Master License Generator")
    print("Version: 1.3.0")
    print("=" * 70)
    
    license_data = generate_license(
        device_id=DEVICE_ID,
        customer_email=CUSTOMER_EMAIL,
        license_type=LICENSE_TYPE
    )
    
    if license_data:
        print("\n✅ SUCCESS: License ready to send to customer")
        print("\n📋 Instructions for customer:")
        print("   1. Copy the license JSON above")
        print("   2. Open DMX Master")
        print("   3. Go to Help > Activate License")
        print("   4. Paste the license JSON")
        print("   5. Click Activate")
        print("   6. Restart DMX Master")
        print("   7. Status bar will show: ✓ LICENSED - 512 Universes")
    else:
        print("\n❌ FAILED: Could not generate license")
        sys.exit(1)
