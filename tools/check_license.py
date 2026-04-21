"""
Quick script to check license validity
"""

import json
from src.utils.license import get_license_manager

# License to check
license_json = """
{
  "device_id": "226e6b3a1bf085b0ba538f7139d210cfbcf2acfe6d434079d39da1f06b1b3775",
  "license_id": "4e2c9471-e95b-4ba1-9ed0-e59c67f4a13d",
  "issued_date": "2025-11-05T14:35:16.511095",
  "customer_email": "dinh@gmail.com",
  "license_type": "perpetual",
  "version": "1.0.0",
  "signature": "MqcbH08B4MX7pkMpFiN/hu9iT2H18I4tC5haFqoV/yEYBVbFeHCKof3agkqCQ94eBFkpibXauDQg886timIGVf0y0qKYHdat/epWAbcE9cWSJyPN2mp2RghMKZi2DozL97e24naFSkYCGVKKki30GPCdFvAP+CraKMKMb2HajvZuwdLQPTxu6qVniKPUY/dbt1ATHybtqIX8N2tdHTqtLtsiezz8kpBO5vR/7xpN6ItmBz1puYt0qIuOsX5TmkLs5PD3P+J88ALe2zth6Dw6stpBmB97lDYn/ff//yqB+4Reo6zzeLtSMq1b6IA6mfKfxRY7P7Q7pHpb+/OPbldOBQ=="
}
"""

def main():
    print("=" * 70)
    print("DMX Master - License Validation Check")
    print("=" * 70)
    
    # Get license manager
    lm = get_license_manager()
    
    # Get current device ID
    device_id = lm.get_device_id()
    print(f"\n📱 Current Device ID:")
    print(f"   {device_id}")
    
    # Parse license
    try:
        license_data = json.loads(license_json)
        print(f"\n📄 License Information:")
        print(f"   Device ID:      {license_data['device_id']}")
        print(f"   License ID:     {license_data['license_id']}")
        print(f"   Customer:       {license_data['customer_email']}")
        print(f"   Issued Date:    {license_data['issued_date']}")
        print(f"   License Type:   {license_data['license_type']}")
        print(f"   Version:        {license_data['version']}")
        
        # Check 1: Device ID match
        print(f"\n🔍 Validation Checks:")
        
        device_match = license_data['device_id'] == device_id
        if device_match:
            print(f"   ✅ Device ID Match: YES")
        else:
            print(f"   ❌ Device ID Match: NO")
            print(f"      License device: {license_data['device_id'][:16]}...")
            print(f"      Current device: {device_id[:16]}...")
        
        # Check 2: Signature validation
        try:
            is_valid = lm._validate_license_offline(license_data)
            if is_valid:
                print(f"   ✅ Signature Valid: YES")
            else:
                print(f"   ❌ Signature Valid: NO")
        except Exception as e:
            print(f"   ❌ Signature Valid: NO - {e}")
            is_valid = False
        
        # Final result
        print(f"\n{'=' * 70}")
        if device_match and is_valid:
            print("✅ LICENSE IS VALID FOR THIS DEVICE")
            print(f"   Universe Limit: 512 universes")
            print(f"   License Type: {license_data['license_type'].upper()}")
            print(f"   Customer: {license_data['customer_email']}")
        elif not device_match:
            print("❌ LICENSE INVALID - Device ID Mismatch")
            print(f"   This license was issued for a different computer")
            print(f"   Please request a new license for this device")
        elif not is_valid:
            print("❌ LICENSE INVALID - Signature Verification Failed")
            print(f"   The license signature is invalid or corrupted")
            print(f"   Please contact support for a valid license")
        
        print("=" * 70)
        
        # Get current license status
        print(f"\n📊 Current License Status:")
        current_info = lm.get_license_info()
        print(f"   Currently Licensed: {current_info['is_licensed']}")
        print(f"   Max Universes: {lm.get_max_universes()}")
        print(f"   License Tier: {lm.get_license_tier()}")
        print(f"   Trial Days Remaining: {current_info['trial_days_remaining']}")
        
    except json.JSONDecodeError as e:
        print(f"\n❌ ERROR: Invalid JSON format - {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
