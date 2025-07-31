#!/bin/bash

# Install uv - The fast Python package installer
# https://github.com/astral-sh/uv

set -e

echo "⚡ Installing uv - Fast Python Package Installer"
echo "==============================================="

# Check if uv is already installed
if command -v uv >/dev/null 2>&1; then
    echo "✅ uv is already installed!"
    uv --version
    echo ""
    echo "You can now run the fix scripts with uv support:"
    echo "- ./quick_fix.sh"
    echo "- ./fix_milestone2_issues.sh"
    exit 0
fi

echo "📦 Installing uv..."

# Install uv using the official installer
if curl -LsSf https://astral.sh/uv/install.sh | sh; then
    echo "✅ uv installed successfully!"
    
    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    # Check if uv is now available
    if command -v uv >/dev/null 2>&1; then
        echo "✅ uv is now available in PATH"
        uv --version
    else
        echo "⚠️  uv installed but not in PATH. Please restart your shell or run:"
        echo "export PATH=\"\$HOME/.cargo/bin:\$PATH\""
    fi
    
    echo ""
    echo "🚀 Next steps:"
    echo "1. Restart your shell or run: source ~/.bashrc"
    echo "2. Run the fix script: ./quick_fix.sh"
    echo ""
    echo "Benefits of uv:"
    echo "- 🚀 10-100x faster than pip"
    echo "- 🔒 Deterministic dependency resolution"
    echo "- 🎯 Drop-in replacement for pip"
    echo "- 📦 Built in Rust for performance"
    
else
    echo "❌ Failed to install uv"
    echo ""
    echo "Alternative installation methods:"
    echo "1. Using pip: pip install uv"
    echo "2. Using conda: conda install -c conda-forge uv"
    echo "3. Using homebrew (macOS): brew install uv"
    echo ""
    echo "Or continue with pip by running: ./quick_fix.sh"
    exit 1
fi
