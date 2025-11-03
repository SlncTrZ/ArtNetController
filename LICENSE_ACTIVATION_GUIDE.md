# 📋 LICENSE ACTIVATION GUIDE
## For ArtNet Controller Users

---

## 🎯 Overview

ArtNet Controller uses a **hardware-bound perpetual license** system:
- ✅ **Trial**: 7 days free, all features included
- ✅ **License**: One-time purchase, use forever on your device
- ✅ **Offline**: Works without internet after activation
- ✅ **Secure**: License tied to your specific computer

---

## 🚀 How to Activate Your License

### Step 1: Get Your Device ID

1. Open ArtNet Controller
2. Go to menu: **Help → License Activation**
3. You'll see your **Device ID** (64-character code)
4. Click **📋 Copy** button to copy it

**Example Device ID:**
```
a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

### Step 2: Purchase License

Contact the software author to purchase a license:
- **Email**: truongcongdinh@example.com
- **Website**: https://your-website.com

Provide:
- Your **Device ID** (copied in Step 1)
- Your **email address**
- Payment proof

### Step 3: Receive License File

You will receive a **JSON file** like this:

```json
{
  "device_id": "a1b2c3d4e5f6...",
  "license_id": "abc-123-def-456",
  "issued_date": "2025-11-03T10:30:00",
  "customer_email": "you@example.com",
  "signature": "base64_encoded_signature...",
  "license_type": "perpetual",
  "version": "1.0.0"
}
```

### Step 4: Activate in Software

1. Open ArtNet Controller
2. Go to **Help → License Activation**
3. In **Step 2** section, paste the entire JSON content
4. Click **✅ Activate License**
5. Done! Software is now permanently activated

---

## ❓ Frequently Asked Questions

### Q: Do I need internet to use the software?
**A:** After activation, no. The license is validated offline using cryptographic signature.

### Q: Can I use my license on multiple computers?
**A:** No. Each license is tied to one specific Device ID (hardware fingerprint).

### Q: What if I reinstall Windows or upgrade hardware?
**A:** Your Device ID may change. Contact support to transfer your license to the new Device ID.

### Q: How long is the trial period?
**A:** 7 days from first installation. All features are available during trial.

### Q: What happens after trial expires?
**A:** The software will require license activation to continue working.

### Q: Is my license lifetime?
**A:** Yes! Perpetual license - pay once, use forever (on the same device).

### Q: Can I get a refund?
**A:** Please contact the software author for refund policy.

---

## 🔧 Troubleshooting

### "Invalid license key or device mismatch"

**Cause:** License was generated for different Device ID

**Solution:**
1. Double-check you copied the correct Device ID
2. Ensure JSON paste is complete (no missing characters)
3. Contact support if issue persists

### "License signature validation failed"

**Cause:** Corrupted or modified license file

**Solution:**
1. Request a fresh license file from support
2. Copy/paste carefully (don't manually edit JSON)

### Trial expired but I have a license

**Cause:** License not activated yet

**Solution:**
1. Open License Activation dialog
2. Paste your license JSON
3. Click Activate

---

## 📞 Support

Need help?
- **Email**: truongcongdinh@example.com
- **Include**: Your Device ID and error message

---

## 🔒 Privacy & Security

### What data is collected?

During license activation:
- ✅ Device ID (hardware fingerprint)
- ✅ Platform info (Windows/Linux)
- ❌ No personal data
- ❌ No usage tracking

### Optional Online Check

The software may periodically check with the license server to verify your license hasn't been revoked. This check:
- Happens in background (every 24 hours)
- Requires internet connection
- Caches result (works offline for 24h)
- Can be disabled in settings

You can always use the software offline after initial activation.

---

*ArtNet Controller - Professional DMX Control Software*
*Version 1.0.0 | © 2025 Trương Công Định*
