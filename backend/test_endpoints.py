#!/usr/bin/env python3
"""
Test script to verify all FastAPI endpoints are working correctly.
Tests the /health, /ingest, and /query endpoints.
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}


def test_endpoint(method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Test an endpoint and return the response."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=HEADERS)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=HEADERS)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"✅ {method.upper()} {endpoint} - Status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"❌ {method.upper()} {endpoint} - Connection failed (server not running?)")
        return None
    except Exception as e:
        print(f"❌ {method.upper()} {endpoint} - Error: {str(e)}")
        return None


def main():
    """Test all endpoints."""
    print("🧪 Testing FastAPI Endpoints")
    print("=" * 50)
    
    # Test /health endpoint
    print("\n1. Testing /health endpoint...")
    health_response = test_endpoint("GET", "/health")
    if health_response:
        print(f"   Status: {health_response.get('status')}")
        print(f"   LocalAI Connected: {health_response.get('localai_connected')}")
    
    # Test /ingest endpoint
    print("\n2. Testing /ingest endpoint...")
    ingest_data = {
        "content": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints.",
        "source": "test_script",
        "metadata": {
            "type": "documentation",
            "language": "en",
            "tags": ["fastapi", "python", "web"]
        }
    }
    ingest_response = test_endpoint("POST", "/ingest", ingest_data)
    if ingest_response:
        doc_id = ingest_response.get('id')
        print(f"   Document ID: {doc_id}")
        print(f"   Status: {ingest_response.get('status')}")
    
    # Test /query endpoint
    print("\n3. Testing /query endpoint...")
    query_data = {
        "query": "What is FastAPI?",
        "limit": 5,
        "filters": {"tags": ["fastapi"]}
    }
    query_response = test_endpoint("POST", "/query", query_data)
    if query_response:
        print(f"   Query: {query_response.get('query')}")
        print(f"   Total Results: {query_response.get('total_results')}")
        print(f"   Query Time: {query_response.get('query_time_ms')}ms")
        
        results = query_response.get('results', [])
        for i, result in enumerate(results[:2], 1):
            print(f"   Result {i}: {result.get('content')[:100]}...")
    
    # Test /health/live and /health/ready
    print("\n4. Testing health probes...")
    test_endpoint("GET", "/health/live")
    test_endpoint("GET", "/health/ready")
    
    print("\n" + "=" * 50)
    print("✨ Endpoint testing complete!")
    
    # Instructions for running the tests
    print("\n📋 To run these tests:")
    print("1. Start the FastAPI server: cd backend && python -m app.main")
    print("2. Wait for server to start (usually takes a few seconds)")
    print("3. Run this test script: python test_endpoints.py")


if __name__ == "__main__":
    main()
