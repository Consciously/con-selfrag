#!/bin/bash
"""
Selfrag CLI Setup Script

This script sets up the Selfrag CLI for easy use.
It can be run to install dependencies and create shortcuts.
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "selfrag_cli.py" ]; then
    print_error "selfrag_cli.py not found. Please run this script from the backend directory."
    exit 1
fi

print_status "Setting up Selfrag CLI..."

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "Python not found. Please install Python 3.11 or later."
    exit 1
fi

print_success "Found Python: $PYTHON_CMD"

# Test CLI basic functionality
print_status "Testing CLI functionality..."
if $PYTHON_CMD selfrag_cli.py --help > /dev/null 2>&1; then
    print_success "CLI is working correctly"
else
    print_error "CLI test failed. Check dependencies."
    exit 1
fi

# Create a convenient wrapper script
print_status "Creating wrapper script..."
cat > selfrag << 'EOF'
#!/bin/bash
# Selfrag CLI wrapper script
cd "$(dirname "${BASH_SOURCE[0]}")"
python3 selfrag_cli.py "$@"
EOF

chmod +x selfrag

print_success "Created './selfrag' wrapper script"

# Optionally install to user bin
if [ "$1" = "--install" ]; then
    print_status "Installing to ~/.local/bin..."
    
    # Create user bin directory if it doesn't exist
    mkdir -p ~/.local/bin
    
    # Copy the CLI script
    cp selfrag_cli.py ~/.local/bin/
    
    # Create wrapper in user bin
    cat > ~/.local/bin/selfrag << EOF
#!/bin/bash
# Selfrag CLI - Installed version
python3 ~/.local/bin/selfrag_cli.py "\$@"
EOF
    
    chmod +x ~/.local/bin/selfrag
    
    print_success "Installed to ~/.local/bin/selfrag"
    print_warning "Make sure ~/.local/bin is in your PATH"
    
    # Check if in PATH
    if echo "$PATH" | grep -q "$HOME/.local/bin"; then
        print_success "~/.local/bin is in your PATH"
    else
        print_warning "Add ~/.local/bin to your PATH by adding this line to your ~/.bashrc or ~/.zshrc:"
        echo 'export PATH="$HOME/.local/bin:$PATH"'
    fi
fi

print_status "Setup complete! Usage examples:"
echo ""
echo "  # Using the wrapper script:"
echo "  ./selfrag health"
echo "  ./selfrag query 'machine learning'"
echo ""
echo "  # Using directly:"
echo "  $PYTHON_CMD selfrag_cli.py health"
echo "  $PYTHON_CMD selfrag_cli.py ingest document.txt"
echo ""

if [ "$1" = "--install" ]; then
    echo "  # Using installed version (after adding to PATH):"
    echo "  selfrag health"
    echo "  selfrag chat"
fi

print_status "For more help, run: ./selfrag --help"
