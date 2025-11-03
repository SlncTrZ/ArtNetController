# ✅ Pre-Upload Security Checklist

## 🔒 CRITICAL: Verify Before Git Push

**Run this checklist BEFORE pushing to GitHub!**

---

## Step 1: Check Sensitive Files

### ❌ Files That MUST NOT Be Uploaded:

```bash
# Run this command to check:
git ls-files | grep -E "(private.*key|\.pem$|license\.lic|secret|password)"
```

**Expected: NO RESULTS**

If any files found:
```bash
# Remove from staging
git rm --cached <file_path>

# Add to .gitignore
echo "<file_path>" >> .gitignore
```

---

## Step 2: Verify .gitignore Working

```bash
# Check what will be committed
git status

# These should NOT appear:
❌ tools/rsa_keys/private_key.pem
❌ config/license.lic
❌ config/license.dat
❌ Any .pem files (except public_key.pem)
❌ generated_licenses/*.json
❌ *.pyc, __pycache__
```

---

## Step 3: Inspect Staged Files

```bash
# List all files to be committed
git ls-tree -r HEAD --name-only

# Manual check:
```

### ✅ Safe to Upload:
- [x] src/**/*.py (source code)
- [x] tools/generate_rsa_keys.py
- [x] tools/generate_license.py
- [x] tools/rsa_keys/public_key.pem
- [x] requirements.txt
- [x] README.md
- [x] .gitignore
- [x] Documentation (*.md files)

### ❌ NEVER Upload:
- [ ] tools/rsa_keys/private_key.pem ← SECRET!
- [ ] config/license.lic
- [ ] generated_licenses/*.json
- [ ] Any customer data
- [ ] .env files with secrets

---

## Step 4: Check Private Key Protection

```bash
# Verify private key is ignored
git check-ignore tools/rsa_keys/private_key.pem

# Expected output: tools/rsa_keys/private_key.pem
# If nothing → ADD TO .gitignore IMMEDIATELY!
```

---

## Step 5: Search for Hardcoded Secrets

```bash
# Search for potential secrets in code
git grep -i "password\|secret\|api.*key\|token" src/

# Review each result:
# ✅ OK: Variable names, comments
# ❌ BAD: Actual passwords/keys/tokens
```

### Common Issues:
```python
# ❌ BAD:
API_KEY = "abc123secret"

# ✅ GOOD:
API_KEY = os.getenv("API_KEY", "default-for-testing")
```

---

## Step 6: Remove Build Artifacts

```bash
# Clean build files (these don't need to be uploaded)
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name "*.egg-info" -exec rm -rf {} +
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete

# Verify clean
git status
```

---

## Step 7: Check File Sizes

```bash
# Find large files (GitHub limit: 100MB)
find . -type f -size +10M -exec ls -lh {} \;

# If any files > 50MB:
# - Add to .gitignore
# - Use Git LFS (Large File Storage)
# - Or host elsewhere
```

---

## Step 8: Review Commit History

```bash
# Check what you're about to push
git log --oneline -10

# Verify:
# ✅ Commit messages make sense
# ❌ No commits with "fix password" or "remove secret"
```

If you accidentally committed secrets:
```bash
# Rewrite history (BEFORE first push)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch <secret_file>" \
  --prune-empty --tag-name-filter cat -- --all
```

---

## Step 9: Test Clean Clone

```bash
# Clone to temporary directory
cd /tmp
git clone /path/to/your/repo test-clone
cd test-clone

# Verify:
# ✅ All files present
# ❌ No secret files
# ✅ App runs: python main.py
```

---

## Step 10: Final Verification

### Run This Command:
```bash
# Check for common sensitive patterns
git grep -n -E "(password|secret|api.*key|private.*key|token).*=.*['\"]" | grep -v "placeholder\|example\|YOUR_"
```

**Expected: NO RESULTS or only placeholder values**

---

## ✅ All Clear? Push!

If all checks pass:

```bash
# Push to GitHub
git push -u origin main
```

---

## 🚨 Emergency: Secrets Exposed on GitHub

If you accidentally pushed secrets:

### Immediate Actions:

1. **Revoke Compromised Credentials**
   ```bash
   # Regenerate:
   # - Private keys (run generate_rsa_keys.py)
   # - API tokens
   # - Passwords
   # - Database credentials
   ```

2. **Remove from GitHub**
   ```bash
   # Contact GitHub support
   # Request cache purge
   # https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
   ```

3. **Clean Git History**
   ```bash
   # Use BFG Repo-Cleaner
   # https://rtyley.github.io/bfg-repo-cleaner/
   
   java -jar bfg.jar --delete-files private_key.pem
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   git push --force
   ```

4. **Re-issue All Licenses**
   ```bash
   # With new keys, all old licenses are invalid
   # Generate new licenses for all customers
   ```

---

## 📋 Daily Workflow After Initial Push

### Before Each Commit:

```bash
# Quick check
git status
git diff

# Verify no secrets
git diff | grep -i "secret\|password\|api.*key"

# If clean
git add .
git commit -m "Your message"
git push
```

---

## 🛡️ Best Practices

### DO:
- ✅ Use environment variables for secrets
- ✅ Keep .gitignore updated
- ✅ Review diffs before committing
- ✅ Use git hooks for automatic checks
- ✅ Backup private keys offline

### DON'T:
- ❌ Commit secrets/passwords
- ❌ Push directly to main (use branches)
- ❌ Ignore .gitignore warnings
- ❌ Share repository with untrusted people
- ❌ Commit large binary files

---

## 🔍 Automated Check Script

Save this as `check_before_push.sh`:

```bash
#!/bin/bash

echo "🔍 Running pre-push security checks..."

# Check for private keys
if git ls-files | grep -q "private.*key"; then
    echo "❌ FAIL: Private key detected!"
    exit 1
fi

# Check for .pem files (except public keys)
if git ls-files | grep "\.pem$" | grep -v "public"; then
    echo "❌ FAIL: .pem file detected!"
    exit 1
fi

# Check for hardcoded secrets
if git grep -E "(password|secret|api.*key).*=.*['\"][^'\"]{20,}" src/; then
    echo "⚠️  WARNING: Potential secrets found!"
    echo "   Review above results manually"
    read -p "Continue? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ All checks passed!"
```

Run before push:
```bash
chmod +x check_before_push.sh
./check_before_push.sh && git push
```

---

## 📞 Help

If unsure about anything:
1. **STOP** - Don't push yet
2. Review this checklist again
3. Ask for help: truongcongdinh97@gmail.com
4. Better safe than sorry!

---

**Remember: Once pushed to public GitHub, consider it PUBLIC FOREVER!**

Even after deletion, it may be cached/archived.

**Prevention is the best security!** 🔒

---

*Last updated: November 3, 2025*
