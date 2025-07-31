#!/usr/bin/env python3
"""
PostgreSQL Connection Diagnostic Script
Tests PostgreSQL connection with explicit parameters to debug authentication issues.
"""

import asyncio
import os
import sys
import asyncpg

async def test_postgres_connection():
    """Test PostgreSQL connection with various parameter combinations."""
    
    # Test parameters
    test_configs = [
        {
            "name": "Environment Variables",
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "user": os.getenv("POSTGRES_USER", "con_selfrag"),
            "password": os.getenv("POSTGRES_PASSWORD", "con_selfrag_password"),
            "database": os.getenv("POSTGRES_DB", "con_selfrag")
        },
        {
            "name": "Hardcoded Values",
            "host": "localhost",
            "port": 5432,
            "user": "con_selfrag",
            "password": "con_selfrag_password",
            "database": "con_selfrag"
        },
        {
            "name": "Trust Authentication (No Password)",
            "host": "localhost",
            "port": 5432,
            "user": "con_selfrag",
            "password": None,
            "database": "con_selfrag"
        },
        {
            "name": "Default PostgreSQL User",
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "con_selfrag_password",
            "database": "con_selfrag"
        },
        {
            "name": "Postgres User - Trust Auth",
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": None,
            "database": "con_selfrag"
        }
    ]
    
    print("🔍 PostgreSQL Connection Diagnostic")
    print("=" * 50)
    
    # Print environment variables
    print("\n📋 Environment Variables:")
    env_vars = ["POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"]
    for var in env_vars:
        value = os.getenv(var, "NOT SET")
        if "PASSWORD" in var and value != "NOT SET":
            value = "*" * len(value)  # Hide password
        print(f"  {var}: {value}")
    
    # Test each configuration
    for config in test_configs:
        print(f"\n🧪 Testing: {config['name']}")
        print(f"  Host: {config['host']}")
        print(f"  Port: {config['port']}")
        print(f"  User: {config['user']}")
        print(f"  Database: {config['database']}")
        if config['password'] is None:
            print(f"  Password: None (Trust Authentication)")
        else:
            print(f"  Password: {'*' * len(config['password'])}")
        
        try:
            if config['password'] is None:
                conn = await asyncpg.connect(
                    host=config["host"],
                    port=config["port"],
                    user=config["user"],
                    database=config["database"]
                )
            else:
                conn = await asyncpg.connect(
                    host=config["host"],
                    port=config["port"],
                    user=config["user"],
                    password=config["password"],
                    database=config["database"]
                )
            
            # Test basic query
            result = await conn.fetchval("SELECT 1")
            await conn.close()
            
            print(f"  ✅ SUCCESS: Connection established, query result: {result}")
            return True
            
        except Exception as e:
            print(f"  ❌ FAILED: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("Starting PostgreSQL diagnostic...")
    success = asyncio.run(test_postgres_connection())
    
    if not success:
        print("\n🔧 Troubleshooting suggestions:")
        print("1. Check if PostgreSQL container is running: docker ps | grep postgres")
        print("2. Check PostgreSQL logs: docker logs postgres")
        print("3. Try connecting directly: docker exec -it postgres psql -U con_selfrag -d con_selfrag")
        print("4. Reset PostgreSQL data: docker compose down && docker volume rm con-selfrag_postgres-data && docker compose up -d")
        sys.exit(1)
    else:
        print("\n🎉 PostgreSQL connection successful!")
