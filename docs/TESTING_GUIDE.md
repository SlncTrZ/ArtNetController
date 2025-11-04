# 🧪 Testing the Secure License System

## Quick Test Guide

### ✅ Test 1: Hardware Binding

**Objective:** Verify license can't be copied to another machine

```bash
# On Machine A (your dev machine)
python main.py
# Go to Help → License Activation
# Copy Device ID: abc123...

# Generate license for Machine A
python tools/generate_license.py \
  --device-id abc123... \
  --email test@example.com

# Activate on Machine A
# → Should work ✅

# Copy config/license.lic to Machine B
# → Should FAIL ❌ (different hardware ID, can't decrypt)
```

**Expected Results:**
- ✅ Machine A: License works
- ❌ Machine B: "License file is corrupted or not for this machine"

---

### ✅ Test 2: AES Encryption (Tamper Protection)

**Objective:** Verify license file can't be edited

```bash
# Activate a valid license
# File created: config/license.lic (encrypted binary)

# Try to edit with text editor
notepad config/license.lic
# → Shows binary garbage (encrypted)

# Try to manually edit bytes
# → Decryption will fail (authentication tag broken)
```

**Expected Results:**
- ❌ Can't read JSON in text editor (binary encrypted)
- ❌ Any modification breaks authentication tag
- ❌ App shows "License corrupted" error

---

### ✅ Test 3: RSA Signature Validation

**Objective:** Verify only admin can generate valid licenses

```bash
# User tries to create fake license JSON
{
  "device_id": "their_real_device_id",
  "license_id": "fake-uuid-1234",
  "issued_date": "2025-11-03T00:00:00",
  "customer_email": "hacker@example.com",
  "signature": "fake_signature_base64",
  "license_type": "perpetual",
  "version": "1.0.0"
}

# Paste into activation dialog
# → Should FAIL ❌
```

**Expected Results:**
- ❌ RSA signature verification fails
- ❌ Error: "Invalid license signature"

---

### ✅ Test 4: Trial Period

**Objective:** Verify trial expiration works

```bash
# Fresh install
rm config/install_date.txt
rm config/license.lic

# Launch app
python main.py
# → Trial starts (7 days)

# Check status
Help → License Activation
# → Shows "Trial: 7 days remaining"

# Simulate time travel (manual test)
# Edit config/install_date.txt
# Change date to 8 days ago

# Restart app
# → Should block with "Trial expired" ❌
```

**Expected Results:**
- ✅ Fresh install: 7 days trial
- ⏰ After 7 days: App blocks, requires license
- ❌ Can't bypass by deleting install_date.txt (recreated with original date)

---

### ✅ Test 5: Cython Compilation

**Objective:** Verify source code is hidden after compilation

```bash
# Before compilation
ls src/utils/license.py
# → Python source code visible

# Compile
python setup_cython.py build_ext --inplace

# After compilation
ls src/utils/license*.pyd  # Windows
ls src/utils/license*.so   # Linux
# → Binary file (not readable)

# Try to read
cat src/utils/license.pyd
# → Binary garbage

# Try to import in Python
python -c "import src.utils.license as lic; print(lic.__file__)"
# → Shows .pyd path (compiled)

# Delete original source
rm src/utils/license.py

# App should still work
python main.py
# → Imports from compiled .pyd ✅
```

**Expected Results:**
- ✅ Compiled binary works
- ❌ Can't read source code from .pyd/.so
- ✅ App runs without original .py file

---

### ✅ Test 6: License Activation Flow

**Full end-to-end test:**

```bash
# 1. Fresh install (user side)
rm -rf config/
python main.py

# 2. User gets Device ID
Help → License Activation → Copy Device ID
# Device ID: abc123def456...

# 3. Admin generates license (your side)
python tools/generate_license.py \
  --device-id abc123def456... \
  --email customer@example.com

# Output: generated_licenses/license_customer_abc12345.json

# 4. User activates (paste JSON)
Help → License Activation
→ Paste JSON into box
→ Click "Activate License"

# 5. Verify activation
# → Should show "✅ ACTIVATED"
# → File created: config/license.lic (encrypted binary)

# 6. Restart app
# → Should start normally (no trial message)

# 7. Check license info
Help → License Activation
# → Status: "✅ ACTIVATED"
# → Licensed to: customer@example.com
```

**Expected Results:**
- ✅ Device ID generated correctly
- ✅ JSON license pasted successfully
- ✅ RSA signature validates
- ✅ License encrypted and saved
- ✅ App unlocked permanently

---

### ✅ Test 7: Online Revocation (Optional)

**If you deployed the revocation server:**

```bash
# 1. Start revocation server
cd server
python license_server.py

# 2. Activate a license in app
# Background thread starts checking every 24h

# 3. Revoke license via API
curl -X POST http://localhost:5000/api/license/revoke \
  -H "Content-Type: application/json" \
  -d '{
    "license_id": "abc-123-def-456",
    "reason": "Testing revocation",
    "admin_key": "change-this-admin-key-in-production"
  }'

# 4. Wait for next check (or restart app)
# → License should be marked as revoked
# → App shows "License revoked" message

# 5. Offline grace period
# Stop server, disconnect internet
# → App should still work for 24 hours (cache)
# → After 24h: Shows "Offline grace period expired"
```

**Expected Results:**
- ✅ Revocation server responds
- ✅ Revoked license detected
- ✅ Offline grace period works (24h)

---

## 🐛 Common Issues

### Issue: "License decryption failed"
**Causes:**
- Wrong machine (different hardware ID)
- Corrupted license file
- License generated with old device ID

**Solution:**
- Verify Device ID matches
- Re-download license file
- Generate fresh license

### Issue: "Invalid license signature"
**Causes:**
- Fake/modified license JSON
- Wrong public key embedded in app

**Solution:**
- Get legitimate license from admin
- Verify public key in src/utils/license.py matches private key

### Issue: "ModuleNotFoundError: license"
**Causes:**
- Cython compilation failed
- Compiled binary not found

**Solution:**
```bash
# Rebuild
python setup_cython.py build_ext --inplace

# Check output
ls src/utils/license*.pyd  # Windows
ls src/utils/license*.so   # Linux
```

### Issue: Trial doesn't work
**Causes:**
- install_date.txt corrupted
- System time changed

**Solution:**
```bash
# Reset trial (for testing only!)
rm config/install_date.txt
# Restart app
```

---

## 📊 Security Checklist

Before distribution:

- [ ] Generated RSA keys (`tools/generate_rsa_keys.py`)
- [ ] Embedded public key in `src/utils/license.py`
- [ ] Compiled license module with Cython
- [ ] Tested compiled binary works
- [ ] Deleted original `license.py` source
- [ ] Tested license activation end-to-end
- [ ] Tested hardware binding (different machines)
- [ ] Tested AES encryption (can't edit file)
- [ ] Verified private key is NOT in distribution
- [ ] Verified `tools/` folder is NOT in distribution
- [ ] Updated `.gitignore` to exclude private key
- [ ] Backed up private key securely

---

## 🎯 Performance Check

```bash
# License validation should be fast
time python -c "
from src.utils.license import get_license_manager
mgr = get_license_manager()
print('Licensed:', mgr.is_licensed())
"

# Expected: < 100ms
```

---

## 📞 Support

Issues with license system:
- Check logs: `logs/app.log`
- Enable debug: Set `logging.DEBUG` in main.py
- Contact: truongcongdinh@example.com

---

**Happy Testing! 🚀**

Remember: This is a professional-grade license system.
Test thoroughly before deploying to production!
