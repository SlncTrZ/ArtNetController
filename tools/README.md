# ⚠️ ADMIN TOOLS - CONFIDENTIAL

## 🔒 THIS DIRECTORY IS FOR SOFTWARE AUTHOR ONLY

**DO NOT DISTRIBUTE THESE TOOLS TO USERS!**

---

## Contents

### 1. `generate_rsa_keys.py`
- **Purpose**: Generate RSA-2048 key pair
- **Run**: ONCE during initial setup
- **Output**: 
  - `rsa_keys/private_key.pem` ← **KEEP SECRET!**
  - `rsa_keys/public_key.pem` ← Embed in app
  - `rsa_keys/public_key_constant.py` ← Copy to src

### 2. `generate_license.py`
- **Purpose**: Sign customer licenses
- **Input**: Customer Device ID + Email
- **Output**: JSON license file for customer
- **Requires**: `rsa_keys/private_key.pem`

### 3. `rsa_keys/` Directory
- **Contains**: RSA key pair
- **Security**: 
  - ✅ `public_key.pem` - Safe to embed in app
  - ❌ `private_key.pem` - **NEVER SHARE OR COMMIT!**

---

## 🚨 Security Warning

### The private key is the ONLY way to generate valid licenses!

If compromised:
- ❌ Anyone can generate unlimited licenses
- ❌ Your licensing system is broken
- ❌ No way to revoke fraudulent licenses

**Protect it like your bank password!**

---

## 📖 Full Documentation

See: [ADMIN_TOOLS_README.md](../ADMIN_TOOLS_README.md)

---

## ✅ Quick Start

```bash
# 1. Generate keys (first time only)
python generate_rsa_keys.py

# 2. Copy public key to application
# Open rsa_keys/public_key_constant.py
# Copy PUBLIC_KEY_PEM to src/utils/license.py

# 3. Secure private key
# Move rsa_keys/private_key.pem to safe location

# 4. Generate customer license
python generate_license.py \
  --device-id <customer_device_id> \
  --email <customer_email>

# 5. Send generated JSON to customer
```

---

**Remember: Only YOU should have access to these tools!**
