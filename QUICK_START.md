# 🚀 QUICK START - For Admin (You)

## ⚡ 3 Steps to Production

### Step 1: Generate Keys (Once)
```bash
cd tools
python generate_rsa_keys.py
```
- Creates `private_key.pem` (KEEP SECRET!)
- Creates `public_key_constant.py`
- Copy public key to `src/utils/license.py`

### Step 2: Build App
```bash
# Windows
build.bat

# Linux
chmod +x build.sh
./build.sh
```
- Compiles license.py → license.pyd
- Protects source code

### Step 3: Generate Customer License
```bash
cd tools
python generate_license.py \
  --device-id <customer_device_id> \
  --email customer@example.com
```
- Creates JSON license file
- Send to customer

---

## 📋 Customer Instructions (Send This)

1. Install ArtNet Controller
2. Open **Help → License Activation**
3. Copy **Device ID**
4. Email Device ID to: **truongcongdinh@example.com**
5. Receive JSON license file
6. Paste JSON into activation dialog
7. Done!

---

## 🔒 Security Checklist

Before distributing:
- [ ] Private key backed up (USB + cloud)
- [ ] Compiled with Cython (`license.pyd` exists)
- [ ] Deleted `license.py` from distribution
- [ ] Excluded `tools/` folder
- [ ] Tested on clean machine
- [ ] Changed revocation server admin key

---

## 📁 What to Distribute

**Include:**
- ✅ `src/` (with `license.pyd`, NO `license.py`)
- ✅ `config/` (empty folder)
- ✅ `main.py`
- ✅ `requirements.txt`
- ✅ `LICENSE_ACTIVATION_GUIDE.md` (for users)

**DO NOT Include:**
- ❌ `tools/` folder
- ❌ `tools/rsa_keys/private_key.pem`
- ❌ `server/` (optional, deploy separately)
- ❌ `build.bat` / `setup_cython.py`
- ❌ `ADMIN_TOOLS_README.md`

---

## 🛠️ Common Commands

### Generate License
```bash
python tools/generate_license.py \
  --device-id abc123... \
  --email customer@example.com
```

### Revoke License
```bash
curl -X POST http://localhost:5000/api/license/revoke \
  -H "Content-Type: application/json" \
  -d '{"license_id":"abc-123","reason":"Refund","admin_key":"your-key"}'
```

### Rebuild App
```bash
python setup_cython.py build_ext --inplace
```

---

## 📖 Full Documentation

- **ADMIN_TOOLS_README.md** - Detailed admin guide
- **SECURITY_ARCHITECTURE.md** - Technical security details
- **TESTING_GUIDE.md** - How to test everything
- **LICENSE_SYSTEM_SUMMARY.md** - Complete overview

---

## 🎯 System Overview

```
User gets trial (7 days)
    ↓
User sends Device ID to you
    ↓
You generate signed license (RSA)
    ↓
User activates (JSON paste)
    ↓
License encrypted with AES (hardware-bound)
    ↓
Software unlocked forever!
```

**Security Layers:**
1. RSA-2048 signatures (can't forge)
2. Hardware binding (can't copy)
3. AES-256 encryption (can't edit)
4. Cython compilation (can't read code)
5. Online revocation (remote control)

---

## ⚠️ CRITICAL: Never Share

- ❌ `tools/rsa_keys/private_key.pem`
- ❌ `tools/` folder
- ❌ Admin passwords
- ❌ Uncompiled `license.py` source

---

## 📞 Questions?

Check full docs in:
- `ADMIN_TOOLS_README.md`
- `SECURITY_ARCHITECTURE.md`

**Contact:** truongcongdinh@example.com

---

*License System v1.0 | Nov 3, 2025*
