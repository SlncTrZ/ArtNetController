#!/bin/bash
# Install script for Art-Net Controller

echo "Installing Art-Net Controller..."

# Create virtual environment
python -m venv venv

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

echo "Installation complete!"
echo ""
echo "To run the application:"
echo "1. Activate virtual environment:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "   venv\\Scripts\\activate"
else
    echo "   source venv/bin/activate"
fi
echo "2. Run the application:"
echo "   python run.py"
echo ""
echo "Or simply:"
echo "   python main.py"