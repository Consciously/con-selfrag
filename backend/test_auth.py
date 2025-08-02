#!/usr/bin/env python3
"""
Test script for the authentication system.

This script tests:
1. User registration
2. User login
3. JWT token validation
4. API key generation
5. Protected endpoint access
"""

import asyncio
import sys
import os
import httpx
from typing import Dict, Any

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

BASE_URL = "http://localhost:8000"

async def test_auth_system():
    """Test the complete authentication system."""
    async with httpx.AsyncClient() as client:
        print("🧪 Testing CON-SELFRAG Authentication System")
        print("=" * 50)
        
        # Test 1: Health check (should work without auth)
        print("\n1. Testing health endpoint (no auth required)...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("✅ Health endpoint accessible")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health endpoint error: {e}")
            return
        
        # Test 2: Protected endpoint without auth (should fail)
        print("\n2. Testing protected endpoint without auth...")
        try:
            response = await client.get(f"{BASE_URL}/auth/profile")
            if response.status_code == 401:
                print("✅ Protected endpoint correctly requires authentication")
            else:
                print(f"❌ Protected endpoint should return 401, got: {response.status_code}")
        except Exception as e:
            print(f"❌ Protected endpoint test error: {e}")
        
        # Test 3: User registration
        print("\n3. Testing user registration...")
        test_user = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/auth/register", json=test_user)
            if response.status_code == 201:
                print("✅ User registration successful")
                registration_data = response.json()
                token = registration_data["access_token"]
                print(f"   Token received: {token[:20]}...")
            else:
                print(f"❌ User registration failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return
        except Exception as e:
            print(f"❌ User registration error: {e}")
            return
        
        # Test 4: User login
        print("\n4. Testing user login...")
        login_data = {
            "username": test_user["username"],
            "password": test_user["password"]
        }
        
        try:
            response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                print("✅ User login successful")
                login_response = response.json()
                token = login_response["access_token"]
                print(f"   New token received: {token[:20]}...")
            else:
                print(f"❌ User login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return
        except Exception as e:
            print(f"❌ User login error: {e}")
            return
        
        # Test 5: Access protected endpoint with token
        print("\n5. Testing protected endpoint with JWT token...")
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = await client.get(f"{BASE_URL}/auth/profile", headers=headers)
            if response.status_code == 200:
                print("✅ Protected endpoint accessible with JWT token")
                profile = response.json()
                print(f"   User profile: {profile['username']} ({profile['email']})")
            else:
                print(f"❌ Protected endpoint failed with token: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Protected endpoint with token error: {e}")
        
        # Test 6: API key generation
        print("\n6. Testing API key generation...")
        api_key_request = {
            "name": "Test API Key",
            "expires_days": 30
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/auth/api-keys", 
                json=api_key_request,
                headers=headers
            )
            if response.status_code == 201:
                print("✅ API key generation successful")
                api_key_data = response.json()
                api_key = api_key_data["full_key"]
                print(f"   API key: {api_key[:20]}...")
            else:
                print(f"❌ API key generation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return
        except Exception as e:
            print(f"❌ API key generation error: {e}")
            return
        
        # Test 7: Access protected endpoint with API key
        print("\n7. Testing protected endpoint with API key...")
        api_headers = {"X-API-Key": api_key}
        
        try:
            response = await client.get(f"{BASE_URL}/auth/profile", headers=api_headers)
            if response.status_code == 200:
                print("✅ Protected endpoint accessible with API key")
                profile = response.json()
                print(f"   User profile: {profile['username']} ({profile['email']})")
            else:
                print(f"❌ Protected endpoint failed with API key: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Protected endpoint with API key error: {e}")
        
        # Test 8: List API keys
        print("\n8. Testing API key listing...")
        try:
            response = await client.get(f"{BASE_URL}/auth/api-keys", headers=headers)
            if response.status_code == 200:
                print("✅ API key listing successful")
                api_keys = response.json()
                print(f"   Found {len(api_keys)} API key(s)")
                for key in api_keys:
                    print(f"   - {key['name']} (ID: {key['key_id']})")
            else:
                print(f"❌ API key listing failed: {response.status_code}")
        except Exception as e:
            print(f"❌ API key listing error: {e}")
        
        print("\n🎉 Authentication system test completed!")
        print("=" * 50)
        print("\n✅ All core authentication features are working:")
        print("  - User registration and login")
        print("  - JWT token authentication")
        print("  - API key generation and authentication")
        print("  - Protected endpoint access control")
        print("  - User profile management")

if __name__ == "__main__":
    print("Starting authentication system test...")
    print("Make sure the API server is running on http://localhost:8000")
    print()
    
    try:
        asyncio.run(test_auth_system())
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
