#!/usr/bin/env python3
"""
Quick test script for RAG API endpoints
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8001"

def test_endpoint(endpoint: str, method: str = "GET", data: Dict[Any, Any] = None) -> None:
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🔍 Testing {method} {endpoint}")
    print(f"URL: {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Success!")
            if response.headers.get('content-type', '').startswith('application/json'):
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
            else:
                print(f"Response: {response.text[:200]}...")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the server running?")
    except requests.exceptions.Timeout:
        print("⏰ Request timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Test all RAG API endpoints"""
    print("🚀 Testing RAG API Endpoints")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        ("/health/status", "GET"),
        ("/rag/health", "GET"),
        ("/rag/collections/stats", "GET"),
        ("/docs", "GET"),  # OpenAPI docs
    ]
    
    # Test POST endpoint with sample data
    sample_content = {
        "text": "This is a test document for the RAG pipeline.",
        "metadata": {"source": "test", "type": "sample"}
    }
    
    for endpoint, method in endpoints:
        test_endpoint(endpoint, method)
    
    print(f"\n🔍 Testing POST /ingest/content")
    test_endpoint("/ingest/content", "POST", sample_content)
    
    # Test query endpoint
    query_data = {
        "query": "test document",
        "limit": 5
    }
    
    print(f"\n🔍 Testing POST /query/content")
    test_endpoint("/query/content", "POST", query_data)
    
    print(f"\n🎉 RAG API testing completed!")
    print(f"\n📚 Visit {BASE_URL}/docs for interactive API documentation")

if __name__ == "__main__":
    main()
