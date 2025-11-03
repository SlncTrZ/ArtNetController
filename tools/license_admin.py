"""
License Admin Tool
Tool để generate và quản lý licenses từ command line
"""

import requests
import json
import sys
from datetime import datetime

# Server configuration
LICENSE_SERVER = "http://localhost:5000"  # Thay bằng server thật
ADMIN_PASSWORD = "admin-password-change-this"  # Phải giống server

def generate_license(customer, email="", notes=""):
    """Generate new license"""
    url = f"{LICENSE_SERVER}/api/license/generate"
    
    data = {
        'admin_password': ADMIN_PASSWORD,
        'customer': customer,
        'email': email,
        'notes': notes
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        
        if result.get('success'):
            print("\n" + "=" * 60)
            print("✅ LICENSE GENERATED SUCCESSFULLY")
            print("=" * 60)
            print(f"\nCustomer: {customer}")
            print(f"Email:    {email}")
            print(f"License:  {result['license_key']}")
            print("\nSend this license key to the customer.")
            print("=" * 60)
            return result['license_key']
        else:
            print(f"❌ Failed: {result.get('message')}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def revoke_license(license_key, reason=""):
    """Revoke a license"""
    url = f"{LICENSE_SERVER}/api/license/revoke"
    
    data = {
        'admin_password': ADMIN_PASSWORD,
        'license_key': license_key,
        'reason': reason
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        
        if result.get('success'):
            print(f"✅ License revoked: {license_key}")
        else:
            print(f"❌ Failed: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def list_licenses():
    """List all licenses"""
    url = f"{LICENSE_SERVER}/api/license/list"
    
    data = {
        'admin_password': ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        
        if result.get('success'):
            licenses = result.get('licenses', [])
            
            print("\n" + "=" * 120)
            print(f"  LICENSES ({result['count']} total)")
            print("=" * 120)
            
            if not licenses:
                print("No licenses found.")
            else:
                # Header
                print(f"{'License Key':<25} {'Customer':<20} {'Platform':<10} {'Status':<12} {'Activations':<12} {'Last Check':<20}")
                print("-" * 120)
                
                for lic in licenses:
                    key = lic['key']
                    customer = lic['customer'][:19]
                    platform = lic.get('platform', 'N/A')[:9]
                    
                    if lic['revoked']:
                        status = "❌ REVOKED"
                    elif lic['hardware_id'] == 'Not activated':
                        status = "⏳ Pending"
                    else:
                        status = "✅ Active"
                    
                    activations = str(lic.get('validation_count', 0))
                    
                    last_check = lic.get('last_validation', 'Never')
                    if last_check != 'Never':
                        try:
                            dt = datetime.fromisoformat(last_check)
                            last_check = dt.strftime('%Y-%m-%d %H:%M')
                        except:
                            pass
                    
                    print(f"{key:<25} {customer:<20} {platform:<10} {status:<12} {activations:<12} {last_check:<20}")
            
            print("=" * 120)
            
        else:
            print(f"❌ Failed: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("=" * 60)
    print("  ART-NET CONTROLLER - LICENSE ADMIN TOOL")
    print("=" * 60)
    print(f"  Server: {LICENSE_SERVER}")
    print("=" * 60)
    print()
    
    while True:
        print("\nOptions:")
        print("1. Generate New License")
        print("2. List All Licenses")
        print("3. Revoke License")
        print("4. Check Server Health")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            print("\n--- Generate New License ---")
            customer = input("Customer name: ").strip()
            email = input("Email (optional): ").strip()
            notes = input("Notes (optional): ").strip()
            
            if customer:
                generate_license(customer, email, notes)
            else:
                print("❌ Customer name is required!")
        
        elif choice == '2':
            list_licenses()
        
        elif choice == '3':
            print("\n--- Revoke License ---")
            license_key = input("License key to revoke: ").strip()
            reason = input("Reason (optional): ").strip()
            
            if license_key:
                confirm = input(f"Revoke {license_key}? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    revoke_license(license_key, reason)
            else:
                print("❌ License key is required!")
        
        elif choice == '4':
            try:
                response = requests.get(f"{LICENSE_SERVER}/health", timeout=5)
                result = response.json()
                print(f"\n✅ Server is healthy: {result.get('service')}")
            except Exception as e:
                print(f"\n❌ Server is down: {e}")
        
        elif choice == '5':
            print("\nGoodbye!")
            break
        
        else:
            print("❌ Invalid option!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
