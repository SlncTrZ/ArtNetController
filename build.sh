#!/bin/bash
# =========================================
# Build Script for ArtNet Controller (Linux)
# Compiles license module with Cython
# =========================================

echo ""
echo "========================================"
echo "  ArtNet Controller - Build Script"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found!"
    echo "Please install Python 3.8+ first"
    exit 1
fi

echo "[1/5] Checking dependencies..."
pip3 install --quiet cython cryptography numpy pyinstaller

echo "[2/5] Compiling license module with Cython..."
python3 setup_cython.py build_ext --inplace

if [ $? -ne 0 ]; then
    echo "ERROR: Cython compilation failed!"
    exit 1
fi

echo "[3/5] Verifying compiled binary..."
if ls src/utils/license*.so 1> /dev/null 2>&1; then
    echo "  ✅ SUCCESS: license.so compiled"
else
    echo "  ❌ ERROR: Compiled binary not found!"
    exit 1
fi

echo "[4/5] Backing up original source..."
if [ -f "src/utils/license.py" ]; then
    cp "src/utils/license.py" "src/utils/license.py.original"
    echo "  Backup created: license.py.original"
fi

echo "[5/5] Cleaning build artifacts..."
rm -rf build/
rm -f src/utils/license.c

echo ""
echo "========================================"
echo "  BUILD SUCCESSFUL!"
echo "========================================"
echo ""
echo "Compiled files:"
ls -lh src/utils/license*.so 2>/dev/null
echo ""
echo "IMPORTANT:"
echo "  - license.so contains the protected code"
echo "  - You can now delete license.py before distribution"
echo "  - Keep license.py.original for development"
echo ""
echo "Next steps:"
echo "  1. Test the application with compiled module"
echo "  2. Create distribution package (see SECURITY_ARCHITECTURE.md)"
echo "  3. Delete original license.py before shipping"
echo ""
