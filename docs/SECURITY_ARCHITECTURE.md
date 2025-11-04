# 🔒 Advanced License Protection System

## Security Layers Implemented

### 1. 🧬 **AES-256-GCM Encryption** (License File Protection)

**What it does:**
- License file (`config/license.lic`) is encrypted with AES-256-GCM
- Encryption key derived from hardware ID (PBKDF2 with 100,000 iterations)
- Authentication tag prevents tampering

**Why it's secure:**
- ❌ Users can't edit JSON license file directly
- ❌ Copying license file to another machine won't work (different hardware ID = different AES key)
- ❌ Tampering detection: Any modification breaks the authentication tag

**Technical details:**
```python
# Encryption
AES_KEY = PBKDF2(device_id, salt, 100000 iterations)
nonce = random(12 bytes)
encrypted = AESGCM(key).encrypt(nonce, json_data, aad=None)
file_content = nonce + encrypted
```

---

### 2. 🔐 **Cython Compilation** (Source Code Protection)

**What it does:**
- Compiles `src/utils/license.py` to binary `.pyd` (Windows) or `.so` (Linux)
- Removes original Python source code
- Distributes only compiled binary

**Why it's secure:**
- ❌ Users can't read the license validation logic
- ❌ Reverse engineering is extremely difficult (compiled C code)
- ❌ Can't see the embedded RSA public key easily

**How to compile:**
```bash
# Install Cython
pip install cython

# Compile license module
python setup_cython.py build_ext --inplace

# Result:
# src/utils/license.cp311-win_amd64.pyd (Windows)
# src/utils/license.cpython-311-x86_64-linux-gnu.so (Linux)

# Delete original Python file
rm src/utils/license.py
```

---

### 3. 🧲 **Hardware Binding** (Machine Lock)

**What it does:**
- Generates unique Device ID from:
  - **CPU Serial Number** (Windows: WMIC ProcessorId, Linux: /proc/cpuinfo Serial)
  - **MAC Address** (Network adapter)
  - **Platform Info** (OS, machine type)
- License is cryptographically signed with this Device ID
- AES encryption key is derived from Device ID

**Why it's secure:**
- ❌ License won't work on different computer (different Device ID)
- ❌ Can't clone license to multiple machines
- ❌ Reinstalling OS usually preserves CPU serial (license still works)
- ❌ Changing network card changes MAC (may require new license)

**Device ID generation:**
```python
components = [
    platform.system(),      # "Windows", "Linux"
    platform.node(),        # Computer name
    platform.machine(),     # "AMD64", "x86_64"
    MAC_address,            # "aa:bb:cc:dd:ee:ff"
    CPU_serial              # Platform-specific
]
device_id = SHA256("|".join(components))
```

---

### 4. 🔑 **RSA-2048 Digital Signatures** (Anti-Forgery)

**What it does:**
- Admin signs license with RSA-2048 private key
- App verifies signature with embedded public key
- Signature covers: Device ID + License ID + Timestamp

**Why it's secure:**
- ❌ Only admin (with private key) can generate valid licenses
- ❌ Users can't forge licenses (RSA-2048 is cryptographically secure)
- ❌ Public key can verify but not create signatures

---

### 5. 🌐 **Online Revocation Check** (Remote Control)

**What it does:**
- Background thread checks revocation server every 24 hours
- Server maintains blacklist of revoked licenses
- Works offline with 24-hour grace period

**Why it's useful:**
- ✅ Remotely disable licenses (refunds, violations)
- ✅ Track active installations
- ✅ Enforce licensing terms

---

## 🛡️ Complete Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User's Computer                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [App Launches]                                             │
│       ↓                                                      │
│  ┌──────────────────────────────────────┐                  │
│  │ license.pyd (Compiled Cython)        │ ← Can't read     │
│  │ ✓ RSA Public Key embedded            │   source code    │
│  │ ✓ Validation logic hidden            │                  │
│  └──────────────────────────────────────┘                  │
│       ↓                                                      │
│  [Read License File]                                        │
│       ↓                                                      │
│  ┌──────────────────────────────────────┐                  │
│  │ config/license.lic                   │                  │
│  │ (AES-256-GCM encrypted binary)       │ ← Can't edit     │
│  │ 0x1A2B3C4D5E6F...                    │   or copy        │
│  └──────────────────────────────────────┘                  │
│       ↓                                                      │
│  [Derive AES Key from Hardware ID]                         │
│       ↓                                                      │
│  ┌──────────────────────────────────────┐                  │
│  │ Hardware Fingerprint                 │                  │
│  │ • CPU: 1234567890                    │ ← Unique to      │
│  │ • MAC: aa:bb:cc:dd:ee:ff             │   this machine   │
│  │ • Platform: Windows 11 AMD64         │                  │
│  └──────────────────────────────────────┘                  │
│       ↓                                                      │
│  [Decrypt License]                                          │
│       ↓                                                      │
│  ┌──────────────────────────────────────┐                  │
│  │ Decrypted License JSON               │                  │
│  │ {                                     │                  │
│  │   "device_id": "abc123...",          │                  │
│  │   "signature": "RSA_sig...",         │ ← Verify with    │
│  │   "license_id": "uuid..."            │   public key     │
│  │ }                                     │                  │
│  └──────────────────────────────────────┘                  │
│       ↓                                                      │
│  [Verify RSA Signature]                                    │
│       ↓                                                      │
│  [Check Online Revocation] ─────→ [Server: Not Revoked]   │
│       ↓                                                      │
│  ✅ LICENSE VALID - App Unlocked                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Build Instructions for Distribution

### Step 1: Generate RSA Keys (Admin Only - Once)
```bash
cd tools
python generate_rsa_keys.py

# Output:
# ✅ tools/rsa_keys/private_key.pem (KEEP SECRET!)
# ✅ tools/rsa_keys/public_key.pem
# ✅ tools/rsa_keys/public_key_constant.py

# Copy public key to src/utils/license.py
```

### Step 2: Compile License Module with Cython
```bash
# Install dependencies
pip install cython cryptography

# Compile to binary
python setup_cython.py build_ext --inplace

# Verify output
ls src/utils/license*.pyd  # Windows
ls src/utils/license*.so   # Linux
```

### Step 3: Prepare Distribution Package
```bash
# Create distribution folder
mkdir ArtNetController_Release

# Copy application files
cp -r src/ ArtNetController_Release/
cp -r config/ ArtNetController_Release/
cp main.py ArtNetController_Release/

# IMPORTANT: Delete original Python source
rm ArtNetController_Release/src/utils/license.py

# Keep only compiled binary
# license.cp311-win_amd64.pyd (Windows)
# OR
# license.cpython-311-x86_64-linux-gnu.so (Linux)

# DO NOT INCLUDE:
# ❌ tools/ directory (license generation)
# ❌ tools/rsa_keys/private_key.pem
# ❌ server/ (optional revocation server)
# ❌ setup_cython.py
```

### Step 4: Create Installer (Optional)
```bash
# Using PyInstaller
pip install pyinstaller

pyinstaller --onefile \
  --add-data "config:config" \
  --add-binary "src/utils/license.pyd:src/utils" \
  --name ArtNetController \
  main.py
```

---

## 🔓 How Customer Activates License

### Customer Side:
1. Install software (trial mode - 7 days)
2. Open `Help → License Activation`
3. Copy **Device ID** (64-char hex)
4. Email Device ID to you

### Your Side (Admin):
```bash
python tools/generate_license.py \
  --device-id abc123...def \
  --email customer@example.com

# Output: generated_licenses/license_customer_abc12345.json
```

### Customer Activates:
1. Receives JSON file via email
2. Pastes JSON into activation dialog
3. License is:
   - ✅ RSA signature verified (offline)
   - ✅ AES encrypted and saved to `config/license.lic`
   - ✅ Tied to their hardware (can't copy)
4. Software permanently unlocked!

---

## 🛡️ Attack Resistance Analysis

### ❌ Attack: Copy license file to another computer
**Defense:** AES key is different (derived from hardware ID)
**Result:** Decryption fails → License invalid

### ❌ Attack: Edit JSON license file
**Defense:** File is AES-encrypted binary, not plain JSON
**Result:** Can't open in text editor

### ❌ Attack: Decompile .pyd to read validation code
**Defense:** Cython → C binary → very difficult to reverse engineer
**Result:** Validation logic is hidden

### ❌ Attack: Generate fake license with public key
**Defense:** Public key can only verify, not sign
**Result:** RSA signature verification fails

### ❌ Attack: Patch binary to skip license check
**Defense:** Possible but requires advanced skills + breaks with updates
**Result:** Most users won't attempt this

### ❌ Attack: Use debugger to bypass validation
**Defense:** Add anti-debugging checks (optional)
**Result:** Advanced attack, not practical for most

### ✅ Only Valid Attack: Pay for legitimate license
**Defense:** None needed - this is the desired outcome! 😄

---

## 📊 Security Rating

| Feature | Protection Level | Bypass Difficulty |
|---------|-----------------|-------------------|
| RSA Signatures | ⭐⭐⭐⭐⭐ | Cryptographically impossible |
| Hardware Binding | ⭐⭐⭐⭐⭐ | Extremely difficult |
| AES Encryption | ⭐⭐⭐⭐⭐ | Cryptographically impossible |
| Cython Compilation | ⭐⭐⭐⭐☆ | Very difficult (requires C reversing) |
| Online Revocation | ⭐⭐⭐☆☆ | Can work offline with cache |

**Overall Security: ⭐⭐⭐⭐⭐ (Excellent)**

This is a professional-grade license system suitable for commercial software.

---

## 🔧 Maintenance

### Revoke a License:
```bash
# Via revocation server
curl -X POST http://server/api/license/revoke \
  -H "Content-Type: application/json" \
  -d '{
    "license_id": "abc-123",
    "reason": "Refund requested",
    "admin_key": "your-admin-key"
  }'
```

### Transfer License to New Computer:
1. Customer emails new Device ID
2. Generate new license with new Device ID
3. Old license can be revoked (optional)

---

## 📞 Support

Questions about license system security:
- Email: truongcongdinh@example.com
- Internal docs: See source code comments

---

**Remember:**
- 🔒 Keep `private_key.pem` SECRET
- 🔒 Don't distribute `tools/` folder
- 🔒 Only ship compiled `.pyd`/`.so` files
- 🔒 Test on clean machine before release

*Last updated: November 3, 2025*
