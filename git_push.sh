#!/bin/bash
# =========================================
# Git Setup & Push to GitHub
# Repository: https://github.com/truongcongdinh97/DMX-Master
# =========================================

echo ""
echo "========================================"
echo "  Git Setup for DMX-Master Project"
echo "========================================"
echo ""

# Step 1: Initialize Git (if not already)
if [ ! -d ".git" ]; then
    echo "[1/6] Initializing Git repository..."
    git init
    echo "  ✅ Git initialized"
else
    echo "[1/6] Git repository already exists"
fi

# Step 2: Configure Git user (update with your info)
echo "[2/6] Configuring Git user..."
git config user.name "Truong Cong Dinh"
git config user.email "truongcongdinh97@gmail.com"
echo "  ✅ Git user configured"

# Step 3: Add remote (if not already)
if ! git remote | grep -q "origin"; then
    echo "[3/6] Adding GitHub remote..."
    git remote add origin https://github.com/truongcongdinh97/DMX-Master.git
    echo "  ✅ Remote added"
else
    echo "[3/6] Remote already exists"
    git remote -v
fi

# Step 4: Stage all files (respecting .gitignore)
echo "[4/6] Staging files..."
git add .
echo "  ✅ Files staged"

# Step 5: Show what will be committed
echo ""
echo "Files to be committed:"
git status --short
echo ""

# Step 6: Commit
echo "[5/6] Creating commit..."
read -p "Enter commit message (or press Enter for default): " commit_msg
if [ -z "$commit_msg" ]; then
    commit_msg="🚀 Upload DMX-Master project with advanced license system"
fi

git commit -m "$commit_msg"
echo "  ✅ Committed"

# Step 7: Push to GitHub
echo "[6/6] Pushing to GitHub..."
echo ""
echo "⚠️  You will be prompted for GitHub credentials"
echo "    Use Personal Access Token instead of password"
echo "    Generate at: https://github.com/settings/tokens"
echo ""
read -p "Press Enter to continue..."

git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "  ✅ SUCCESS!"
    echo "========================================"
    echo ""
    echo "Project uploaded to:"
    echo "https://github.com/truongcongdinh97/DMX-Master"
    echo ""
else
    echo ""
    echo "========================================"
    echo "  ❌ Push failed!"
    echo "========================================"
    echo ""
    echo "Common issues:"
    echo "1. Wrong credentials"
    echo "2. Need to create Personal Access Token"
    echo "3. Repository doesn't exist on GitHub"
    echo ""
    echo "Solutions:"
    echo "1. Go to https://github.com/settings/tokens"
    echo "2. Generate new token (classic)"
    echo "3. Select 'repo' scope"
    echo "4. Copy token and use as password"
    echo ""
fi
