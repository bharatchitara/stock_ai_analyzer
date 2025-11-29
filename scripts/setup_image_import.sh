#!/bin/bash
# Setup script for Portfolio Image Import Feature

echo "Setting up Portfolio Image Import..."

# Install Python dependencies
echo "Installing Python packages..."
pip install Pillow==10.1.0 pytesseract==0.3.10

# Check OS and install Tesseract
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Detected macOS. Installing Tesseract via Homebrew..."
    if command -v brew &> /dev/null; then
        brew install tesseract
    else
        echo "Homebrew not found. Please install Homebrew first:"
        echo "/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "Detected Linux. Installing Tesseract..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr
    elif command -v yum &> /dev/null; then
        sudo yum install -y tesseract
    else
        echo "Package manager not found. Please install tesseract manually."
    fi
else
    echo "OS not detected. Please install Tesseract manually:"
    echo "Windows: https://github.com/UB-Mannheim/tesseract/wiki"
fi

# Verify installation
echo ""
echo "Verifying installation..."
if command -v tesseract &> /dev/null; then
    echo "✓ Tesseract installed: $(tesseract --version | head -n1)"
else
    echo "✗ Tesseract not found. OCR features will not work."
    echo "  AI Vision will still be available if OpenAI API key is configured."
fi

python -c "import PIL; print('✓ Pillow installed: ' + PIL.__version__)" 2>/dev/null || echo "✗ Pillow not installed"
python -c "import pytesseract; print('✓ pytesseract installed')" 2>/dev/null || echo "✗ pytesseract not installed"

echo ""
echo "Setup complete!"
echo ""
echo "To use AI-powered extraction, add to your .env file:"
echo "OPENAI_API_KEY=your-api-key-here"
echo ""
echo "Test the feature at: http://localhost:8000/portfolio/import/"
