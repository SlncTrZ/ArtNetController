# 🔐 ADMIN TOOLS - CONFIDENTIAL
## DO NOT DISTRIBUTE TO USERS

This directory contains tools for license generation.
**ONLY the software author should have access to these files.**

---

## ⚠️ CRITICAL FILES - KEEP SECRET

### 🔑 Private Key
- **File**: `tools/rsa_keys/private_key.pem`
- **Purpose**: Signs licenses (RSA-2048 private key)
- **Security**: NEVER commit to Git, NEVER share with anyone
- **Storage**: Keep offline backup in secure location

### 🛠️ License Generation Tools
- **File**: `tools/generate_rsa_keys.py`
  - Generates RSA key pair (run ONCE during initial setup)
  - Output: `private_key.pem` + `public_key.pem`

- **File**: `tools/generate_license.py`
  - Signs customer licenses using private key
  - Input: Customer Device ID + Email
  - Output: JSON license file to send to customer

---

## 🚀 SETUP (First Time Only)

### Step 1: Generate RSA Keys
```bash
cd H:\VSCode\ArtNetController\tools
python generate_rsa_keys.py
```

**Output:**
- `tools/rsa_keys/private_key.pem` ← **KEEP SECRET!**
- `tools/rsa_keys/public_key.pem` ← Embed in app
- `tools/rsa_keys/public_key_constant.py` ← Copy to `src/utils/license.py`

### Step 2: Embed Public Key in Application
1. Open `tools/rsa_keys/public_key_constant.py`
2. Copy the `PUBLIC_KEY_PEM` constant
3. Paste into `src/utils/license.py` (replace placeholder)

### Step 3: Secure Private Key
```bash
# Move private key to secure location
# Example: USB drive, encrypted cloud storage
mv tools/rsa_keys/private_key.pem /path/to/secure/backup/
```

### Step 4: Add to .gitignore
Ensure these are NEVER committed:
```
tools/rsa_keys/private_key.pem
tools/rsa_keys/*.pem
generated_licenses/
*.pem
```

---

## 💼 WORKFLOW: Customer Purchases License

### Customer Side:
1. Customer installs software (trial mode)
2. Opens `Help → License Activation`
3. Copies their **Device ID** (64-char hex string)
4. Emails Device ID to you with payment proof

### Your Side (Admin):
```bash
cd H:\VSCode\ArtNetController\tools

# Generate license for customer
python generate_license.py \
  --device-id abc123...def456 \
  --email customer@example.com

# Output: generated_licenses/license_customer_at_example_com_abc12345.json
```

### Delivery:
1. Send JSON file to customer via email
2. Customer pastes JSON content into activation dialog
3. License is validated offline using embedded public key
4. Software unlocks permanently on their device

---

## 🔒 SECURITY ARCHITECTURE

### Why This System is Secure:

1. **Private Key Never Leaves Your Control**
   - Only you can sign licenses
   - Impossible to generate valid licenses without private key
   - RSA-2048 is cryptographically unbreakable

2. **Hardware Binding**
   - Each license is tied to specific Device ID
   - Device ID = SHA-256(CPU Serial + MAC + Platform)
   - License won't work on different computers

3. **Offline Validation**
   - App validates signature using embedded public key
   - No internet required for customer after activation
   - Public key can't be used to generate licenses (only verify)

4. **Optional Online Revocation**
   - Background check to revocation server
   - You can remotely disable licenses if needed
   - Works offline with 24h cache grace period

### Attack Resistance:

❌ **Customer can't crack it:**
- No access to private key
- RSA signature verification (can't forge)
- Hardware-bound (can't transfer)

❌ **Decompiling won't help:**
- Public key is meant to be visible
- Signing requires private key (which they don't have)
- Can't reverse-engineer private key from public key

❌ **Key generators won't work:**
- Each license signed with your private key
- No algorithm to "generate" valid signatures
- Verification fails without proper signature

✅ **Only you control licenses:**
- Generate licenses with `generate_license.py`
- Revoke licenses via revocation server
- Full control over who gets access

---

## 📝 LICENSE GENERATION EXAMPLES

### Basic License:
```bash
python generate_license.py \
  --device-id a1b2c3d4e5f6... \
  --email john@company.com
```

### Custom Output Directory:
```bash
python generate_license.py \
  --device-id a1b2c3d4e5f6... \
  --email john@company.com \
  --output-dir ~/secure_licenses/
```

### Using Different Private Key Location:
```bash
python generate_license.py \
  --device-id a1b2c3d4e5f6... \
  --email john@company.com \
  --private-key /secure/usb/private_key.pem
```

---

## 🗂️ FILE STRUCTURE

```
ArtNetController/
├── tools/                          ← ADMIN ONLY (don't distribute)
│   ├── generate_rsa_keys.py       ← Generate RSA keys (run once)
│   ├── generate_license.py        ← Sign customer licenses
│   ├── rsa_keys/
│   │   ├── private_key.pem        ← SECRET! Your signing key
│   │   ├── public_key.pem         ← Embed in application
│   │   └── public_key_constant.py ← Copy to src/utils/license.py
│   └── generated_licenses/         ← Output directory for licenses
│
├── src/                            ← Distribute to users
│   ├── utils/
│   │   └── license.py             ← Contains PUBLIC KEY only
│   └── gui/
│       └── dialogs/
│           └── license_dialog.py  ← Shows Device ID, accepts JSON
│
├── server/                         ← Optional revocation server
│   └── license_server.py          ← Check revoked licenses
│
└── .gitignore                      ← Exclude private keys!
```

---

## 🛡️ BACKUP STRATEGY

### Essential Backups:

1. **Private Key** (`private_key.pem`)
   - Store on encrypted USB drive
   - Cloud backup (encrypted)
   - Paper backup (base64 printed)

2. **Customer License Database**
   - Spreadsheet: Device ID, Email, License ID, Date
   - Backup `generated_licenses/` folder

3. **Revocation List**
   - Backup `server/revoked_licenses.json`

### Recovery Plan:

If you lose private key:
- ❌ You CANNOT generate new licenses
- ❌ Existing licenses still work (verified with public key)
- ⚠️ Must generate NEW key pair → invalidates all old licenses
- 💡 This is why backup is CRITICAL

---

## 🔄 REVOCATION SERVER (Optional)

### Setup:
```bash
cd H:\VSCode\ArtNetController\server
python license_server.py
```

### Revoke a License:
```bash
curl -X POST http://localhost:5000/api/license/revoke \
  -H "Content-Type: application/json" \
  -d '{
    "license_id": "abc-123-def-456",
    "reason": "Violation of terms",
    "admin_key": "your-admin-key"
  }'
```

### Production Deployment:
```bash
# Use Gunicorn for production
gunicorn -w 4 -b 0.0.0.0:5000 license_server:app

# Behind nginx with HTTPS
# Update REVOCATION_SERVER in src/utils/license.py
```

---

## ❓ FAQ

### Q: Can users generate their own licenses?
**A:** No. They don't have the private key.

### Q: What if someone decompiles the app?
**A:** They only find the public key, which can't generate licenses.

### Q: Can I sell the software with source code?
**A:** Yes, but keep `tools/` directory and private key separate.

### Q: How to handle license transfers?
**A:** 
1. Customer emails requesting transfer
2. You revoke old license (revocation server)
3. Generate new license with new Device ID

### Q: What if customer reinstalls Windows?
**A:** Device ID may change (CPU serial usually persists). If changed, treat as new device.

---

## 📞 SUPPORT

For questions about this license system:
- Email: truongcongdinh@example.com
- Internal docs: See source code comments

**Remember: The security of this system relies on keeping the private key secret!**

---

*Last updated: November 3, 2025*
