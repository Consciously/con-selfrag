#!/usr/bin/env python3
"""
Quick test for Step 5 endpoints using only standard library modules.
This avoids dependency issues and provides immediate feedback.
"""

import json
import sys
import urllib.request
import urllib.error
from typing import Dict, Any


def test_endpoint(url: str, endpoint_name: str) -> Dict[str, Any]:
    """Test a single endpoint and return results."""
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            status_code = response.getcode()
            content = response.read().decode('utf-8')
            
            try:
                data = json.loads(content)
                return {
                    "success": True,
                    "status_code": status_code,
                    "data": data,
                    "content_length": len(content)
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "status_code": status_code,
                    "data": None,
                    "raw_content": content[:200] + "..." if len(content) > 200 else content,
                    "content_length": len(content)
                }
                
    except urllib.error.HTTPError as e:
        try:
            error_content = e.read().decode('utf-8')
            error_data = json.loads(error_content)
        except:
            error_data = error_content
            
        return {
            "success": False,
            "status_code": e.code,
            "error": str(e),
            "error_data": error_data
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": None,
            "error": str(e)
        }


def main():
    """Run quick tests for Step 5 endpoints."""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print(f"🔍 Quick Step 5 Endpoint Test")
    print(f"Testing endpoints at: {base_url}")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        ("/models", "Models Listing"),
        ("/health/llm", "LLM Health Check"),
        ("/llm/models", "LLM Models (for comparison)"),
        ("/llm/health", "LLM Health (for comparison)"),
    ]
    
    results = {}
    
    for endpoint, name in endpoints:
        print(f"\n🧪 Testing {name}: {endpoint}")
        url = f"{base_url}{endpoint}"
        result = test_endpoint(url, name)
        results[endpoint] = result
        
        if result["success"]:
            print(f"  ✅ SUCCESS (HTTP {result['status_code']})")
            print(f"  📊 Response size: {result['content_length']} bytes")
            
            if result.get("data"):
                if isinstance(result["data"], list):
                    print(f"  📋 Response type: list with {len(result['data'])} items")
                    if result["data"] and isinstance(result["data"][0], dict):
                        print(f"  🔑 First item keys: {list(result['data'][0].keys())}")
                elif isinstance(result["data"], dict):
                    print(f"  📋 Response type: dict with keys: {list(result['data'].keys())}")
                    if "status" in result["data"]:
                        print(f"  🏥 Health status: {result['data']['status']}")
                    if "checks" in result["data"]:
                        checks = result["data"]["checks"]
                        print(f"  🔍 Health checks: {len(checks)} checks")
                        for check_name, check_data in checks.items():
                            status = check_data.get("status", "unknown")
                            print(f"    - {check_name}: {status}")
            else:
                print(f"  📄 Raw content: {result.get('raw_content', 'No content')}")
        else:
            print(f"  ❌ FAILED")
            if result.get("status_code"):
                print(f"  📊 HTTP Status: {result['status_code']}")
            print(f"  ⚠️  Error: {result['error']}")
            if result.get("error_data"):
                print(f"  📄 Error data: {result['error_data']}")
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    success_count = sum(1 for r in results.values() if r["success"])
    total_count = len(results)
    
    print(f"✅ Successful: {success_count}/{total_count}")
    print(f"❌ Failed: {total_count - success_count}/{total_count}")
    
    # Check consistency between /models and /llm/models
    if "/models" in results and "/llm/models" in results:
        models_result = results["/models"]
        llm_models_result = results["/llm/models"]
        
        if models_result["success"] and llm_models_result["success"]:
            models_data = models_result.get("data", [])
            llm_models_data = llm_models_result.get("data", [])
            
            if models_data == llm_models_data:
                print("🔄 Endpoint consistency: ✅ /models matches /llm/models")
            else:
                print("🔄 Endpoint consistency: ❌ /models differs from /llm/models")
                print(f"   /models count: {len(models_data) if isinstance(models_data, list) else 'not a list'}")
                print(f"   /llm/models count: {len(llm_models_data) if isinstance(llm_models_data, list) else 'not a list'}")
    
    # Overall assessment
    if success_count == total_count:
        print("\n🎉 All endpoints are working correctly!")
        return 0
    else:
        print(f"\n⚠️  {total_count - success_count} endpoint(s) failed. Check the service logs.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
