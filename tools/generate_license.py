#!/usr/bin/env python3
"""
License Generator Tool - Admin Only
====================================
Generates RSA-signed licenses for customers.

Usage:
    python generate_license.py --device-id <device_id> --email <customer_email>

Requirements:
    - RSA private key (tools/rsa_keys/private_key.pem)
    - Customer's Device ID (from their installation)
    
Output:
    - JSON license file to send to customer
"""

import argparse
import json
import uuid
import base64
from datetime import datetime
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend


def load_private_key(key_path: Path):
    """Load RSA private key from PEM file"""
    try:
        with open(key_path, 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        print(f"✅ Private key loaded from {key_path}")
        return private_key
    except FileNotFoundError:
        print(f"❌ Private key not found: {key_path}")
        print("   Run generate_rsa_keys.py first!")
        exit(1)
    except Exception as e:
        print(f"❌ Failed to load private key: {e}")
        exit(1)


def generate_license(device_id: str, customer_email: str, private_key) -> dict:
    """
    Generate license for a specific device
    
    Args:
        device_id: Customer's hardware ID (SHA-256 hash)
        customer_email: Customer contact email
        private_key: RSA private key for signing
        
    Returns:
        License data dictionary
    """
    # Generate unique license ID
    license_id = str(uuid.uuid4())
    issued_date = datetime.now().isoformat()
    
    # Construct message to sign
    message = f"{device_id}|{license_id}|{issued_date}"
    message_bytes = message.encode('utf-8')
    
    # Sign with RSA private key
    signature = private_key.sign(
        message_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    # Encode signature to base64
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    
    # Build license data
    license_data = {
        'device_id': device_id,
        'license_id': license_id,
        'issued_date': issued_date,
        'customer_email': customer_email,
        'signature': signature_b64,
        'license_type': 'perpetual',
        'version': '1.0.0'
    }
    
    return license_data


def save_license_file(license_data: dict, output_dir: Path):
    """Save license to file"""
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    license_id = license_data['license_id']
    email = license_data['customer_email'].replace('@', '_at_').replace('.', '_')
    filename = f"license_{email}_{license_id[:8]}.json"
    output_path = output_dir / filename
    
    # Save JSON
    with open(output_path, 'w') as f:
        json.dump(license_data, f, indent=2)
    
    print(f"\n✅ License generated: {output_path}")
    return output_path


def display_license_info(license_data: dict):
    """Display license information"""
    print("\n" + "="*60)
    print("LICENSE INFORMATION")
    print("="*60)
    print(f"License ID:      {license_data['license_id']}")
    print(f"Device ID:       {license_data['device_id'][:32]}...")
    print(f"Customer Email:  {license_data['customer_email']}")
    print(f"Issued Date:     {license_data['issued_date']}")
    print(f"License Type:    {license_data['license_type']}")
    print("="*60)
    print("\n📧 Send this JSON file to the customer")
    print("   They should paste the entire JSON content into the license activation dialog\n")


def main():
    parser = argparse.ArgumentParser(
        description='Generate RSA-signed license for ArtNet Controller'
    )
    parser.add_argument(
        '--device-id',
        required=True,
        help='Customer device ID (SHA-256 hash from their installation)'
    )
    parser.add_argument(
        '--email',
        required=True,
        help='Customer email address'
    )
    parser.add_argument(
        '--output-dir',
        default='generated_licenses',
        help='Output directory for license files (default: generated_licenses)'
    )
    parser.add_argument(
        '--private-key',
        default='tools/rsa_keys/private_key.pem',
        help='Path to RSA private key (default: tools/rsa_keys/private_key.pem)'
    )
    
    args = parser.parse_args()
    
    # Validate device ID format (should be 64-char hex)
    device_id = args.device_id.strip()
    if len(device_id) != 64 or not all(c in '0123456789abcdefABCDEF' for c in device_id):
        print("❌ Invalid device ID format")
        print("   Device ID should be a 64-character SHA-256 hash")
        exit(1)
    
    # Load private key
    key_path = Path(args.private_key)
    private_key = load_private_key(key_path)
    
    # Generate license
    print(f"\n🔐 Generating license for {args.email}...")
    license_data = generate_license(device_id, args.email, private_key)
    
    # Save to file
    output_dir = Path(args.output_dir)
    license_file = save_license_file(license_data, output_dir)
    
    # Display info
    display_license_info(license_data)
    
    print("\n📋 INSTRUCTIONS FOR CUSTOMER:")
    print("   1. Open ArtNet Controller")
    print("   2. Go to Help → License Activation")
    print("   3. Paste the entire content of the JSON file")
    print("   4. Click Activate License")
    print("\n✨ Done!")


if __name__ == '__main__':
    main()
