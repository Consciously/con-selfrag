#!/bin/bash

# =============================================================================
# CON-SELFRAG Authentication Setup Script
# =============================================================================
# This script sets up the authentication system for con-selfrag
# 
# What it does:
# 1. Installs authentication dependencies
# 2. Creates database tables
# 3. Sets up initial admin user (optional)
# 4. Generates JWT secret key
# =============================================================================

set -e  # Exit on any error

echo "🚀 Setting up CON-SELFRAG Authentication System..."
echo "=================================================="

# Check if we're in the backend directory
if [[ ! -f "pyproject.toml" ]]; then
    echo "❌ Error: Please run this script from the backend directory"
    echo "   cd backend && ./setup_auth.sh"
    exit 1
fi

# Install dependencies
echo ""
echo "📦 Installing authentication dependencies..."
echo "-------------------------------------------"

if command -v uv &> /dev/null; then
    echo "Using uv package manager..."
    uv sync
elif command -v pip &> /dev/null; then
    echo "Using pip package manager..."
    pip install -e .
else
    echo "❌ Error: Neither uv nor pip found. Please install one of them first."
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Generate JWT secret key if not exists in .env
echo ""
echo "🔐 Setting up JWT secret key..."
echo "------------------------------"

ENV_FILE="../.env"
if [[ ! -f "$ENV_FILE" ]]; then
    echo "Creating .env file from template..."
    cp ../.env.example "$ENV_FILE"
fi

# Generate a secure JWT secret key
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Check if JWT_SECRET_KEY is already set
if grep -q "^JWT_SECRET_KEY=" "$ENV_FILE"; then
    echo "JWT_SECRET_KEY already exists in .env file"
    read -p "Do you want to generate a new JWT secret key? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sed -i.bak "s/^JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" "$ENV_FILE"
        echo "✅ New JWT secret key generated and saved to .env"
    fi
else
    echo "JWT_SECRET_KEY=$JWT_SECRET" >> "$ENV_FILE"
    echo "✅ JWT secret key generated and saved to .env"
fi

# Check database connection
echo ""
echo "🗄️  Setting up database tables..."
echo "---------------------------------"

# Check if PostgreSQL is running
if command -v docker-compose &> /dev/null; then
    echo "Checking if PostgreSQL is running via Docker Compose..."
    if docker-compose ps postgres | grep -q "Up"; then
        echo "✅ PostgreSQL is running"
    else
        echo "⚠️  PostgreSQL not running. Starting services..."
        cd .. && docker-compose up -d postgres redis qdrant
        echo "Waiting 10 seconds for services to start..."
        sleep 10
        cd backend
    fi
else
    echo "⚠️  Docker Compose not found. Make sure PostgreSQL is running locally."
fi

# Run database migrations
echo "Running database migrations..."
if command -v alembic &> /dev/null; then
    alembic upgrade head
    echo "✅ Database tables created successfully"
else
    echo "⚠️  Alembic not found in environment. It should have been installed with dependencies."
    echo "Trying to run migration anyway..."
    
    # Try with uv first, then fallback to direct python execution
    if command -v uv &> /dev/null; then
        echo "Using uv to run alembic..."
        uv run alembic upgrade head
    else
        echo "Using python -m alembic..."
        python -m alembic upgrade head
    fi
    echo "✅ Database tables created successfully"
fi

# Create initial admin user (optional)
echo ""
echo "👤 Creating initial admin user..."
echo "--------------------------------"

read -p "Do you want to create an initial admin user? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "Creating admin user..."
    
    # Create a Python script to add admin user
    cat > create_admin.py << 'EOF'
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.auth_service import AuthService
from app.database.connection import get_database_pools
from app.config import config

async def create_admin():
    print("Enter admin user details:")
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    
    if not username or not email or not password:
        print("❌ All fields are required")
        return
    
    auth_service = AuthService(
        secret_key=config.jwt_secret_key,
        algorithm=config.jwt_algorithm,
        token_expire_minutes=config.jwt_expire_minutes
    )
    
    try:
        pools = get_database_pools()
        await pools.initialize_all()
        
        async with pools.postgres.get_session() as db:
            user = auth_service.register_user(
                db=db,
                username=username,
                email=email,
                password=password,
                is_admin=True
            )
            
            if user:
                print(f"✅ Admin user '{username}' created successfully")
                print(f"   Email: {email}")
                print(f"   Admin: Yes")
            else:
                print("❌ Failed to create admin user (username or email may already exist)")
                
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
    finally:
        await pools.close_all()

if __name__ == "__main__":
    asyncio.run(create_admin())
EOF

    python3 create_admin.py
    rm create_admin.py
fi

# Success message
echo ""
echo "🎉 Authentication system setup complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Start the application: uvicorn app.main:app --reload"
echo "2. Open the API docs: http://localhost:8000/docs"
echo "3. Test authentication endpoints:"
echo "   - POST /auth/register - Register new users"
echo "   - POST /auth/login - Login and get JWT token"
echo "   - GET /auth/profile - Get user profile (requires auth)"
echo "   - POST /auth/api-keys - Generate API keys"
echo ""
echo "🔐 Security Notes:"
echo "- JWT secret key has been generated and saved to .env"
echo "- Change the secret key before production deployment"
echo "- All endpoints except /health and /auth are now protected"
echo "- Use Authorization: Bearer <token> or X-API-Key: <key> headers"
echo ""
echo "📚 Documentation:"
echo "- API docs: http://localhost:8000/docs"
echo "- ReDoc: http://localhost:8000/redoc"
echo ""
