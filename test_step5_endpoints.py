#!/usr/bin/env python3
"""
Test script for Step 5 - /models and /health/llm endpoints

This script tests the newly implemented endpoints for full transparency and testability:
- GET /models - List available LLM models
- GET /health/llm - Comprehensive LLM health check with operational verification

Usage:
    python test_step5_endpoints.py [BASE_URL] [interactive]
    
Examples:
    python test_step5_endpoints.py
    python test_step5_endpoints.py http://localhost:8000
    python test_step5_endpoints.py http://localhost:8000 interactive
"""

import asyncio
import json
import sys
import time
from typing import Any, Dict

import httpx


class Step5EndpointTester:
    """Test suite for Step 5 endpoints - /models and /health/llm"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_test(self, test_name: str, status: str, details: Dict[str, Any] = None):
        """Log test results with emoji indicators"""
        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{emoji} {test_name}: {status}")
        
        if details:
            for key, value in details.items():
                if isinstance(value, (dict, list)):
                    print(f"   {key}: {json.dumps(value, indent=2)}")
                else:
                    print(f"   {key}: {value}")
        
        self.test_results.append({
            "test": test_name,
            "status": status,
            "details": details or {}
        })
        print()
    
    async def test_models_endpoint(self):
        """Test GET /models endpoint"""
        print("🔍 Testing GET /models endpoint...")
        
        try:
            response = await self.client.get(f"{self.base_url}/models")
            
            if response.status_code == 200:
                models = response.json()
                
                if isinstance(models, list):
                    self.log_test(
                        "Models Endpoint - Structure",
                        "PASS",
                        {
                            "status_code": response.status_code,
                            "model_count": len(models),
                            "response_type": "list"
                        }
                    )
                    
                    # Test model data structure
                    if models:
                        first_model = models[0]
                        expected_fields = ["name"]  # Minimum expected fields
                        
                        has_required_fields = all(field in first_model for field in expected_fields)
                        
                        self.log_test(
                            "Models Endpoint - Data Structure",
                            "PASS" if has_required_fields else "FAIL",
                            {
                                "first_model": first_model,
                                "has_required_fields": has_required_fields,
                                "available_models": [model.get("name", "unknown") for model in models[:5]]
                            }
                        )
                    else:
                        self.log_test(
                            "Models Endpoint - Empty Response",
                            "WARN",
                            {"message": "No models returned - LocalAI may not have models loaded"}
                        )
                else:
                    self.log_test(
                        "Models Endpoint - Invalid Response Type",
                        "FAIL",
                        {
                            "expected": "list",
                            "actual": type(models).__name__,
                            "response": models
                        }
                    )
            else:
                self.log_test(
                    "Models Endpoint - HTTP Error",
                    "FAIL",
                    {
                        "status_code": response.status_code,
                        "response": response.text
                    }
                )
                
        except Exception as e:
            self.log_test(
                "Models Endpoint - Connection Error",
                "FAIL",
                {"error": str(e)}
            )
    
    async def test_health_llm_endpoint(self):
        """Test GET /health/llm endpoint"""
        print("🏥 Testing GET /health/llm endpoint...")
        
        try:
            start_time = time.time()
            response = await self.client.get(f"{self.base_url}/health/llm")
            duration = time.time() - start_time
            
            if response.status_code in [200, 503]:
                health_data = response.json()
                
                # Test response structure
                expected_fields = ["status", "service", "timestamp", "checks"]
                has_required_fields = all(field in health_data for field in expected_fields)
                
                self.log_test(
                    "LLM Health - Response Structure",
                    "PASS" if has_required_fields else "FAIL",
                    {
                        "status_code": response.status_code,
                        "has_required_fields": has_required_fields,
                        "response_time_ms": int(duration * 1000),
                        "overall_status": health_data.get("status", "unknown")
                    }
                )
                
                # Test individual health checks
                if "checks" in health_data:
                    checks = health_data["checks"]
                    expected_checks = ["connectivity", "models", "embedding"]
                    
                    for check_name in expected_checks:
                        if check_name in checks:
                            check_data = checks[check_name]
                            check_status = check_data.get("status", "unknown")
                            
                            self.log_test(
                                f"LLM Health - {check_name.title()} Check",
                                "PASS" if check_status == "healthy" else "WARN" if check_status == "warning" else "FAIL",
                                {
                                    "check_status": check_status,
                                    "message": check_data.get("message", ""),
                                    **{k: v for k, v in check_data.items() if k not in ["status", "message"]}
                                }
                            )
                        else:
                            self.log_test(
                                f"LLM Health - Missing {check_name.title()} Check",
                                "FAIL",
                                {"missing_check": check_name}
                            )
                
                # Overall health assessment
                overall_status = health_data.get("status", "unknown")
                if response.status_code == 200 and overall_status == "healthy":
                    self.log_test(
                        "LLM Health - Overall Status",
                        "PASS",
                        {
                            "status": overall_status,
                            "message": health_data.get("message", ""),
                            "all_checks_passed": True
                        }
                    )
                elif response.status_code == 503:
                    self.log_test(
                        "LLM Health - Service Unavailable",
                        "WARN",
                        {
                            "status": overall_status,
                            "message": health_data.get("message", ""),
                            "service_degraded": True
                        }
                    )
                else:
                    self.log_test(
                        "LLM Health - Unexpected Status",
                        "FAIL",
                        {
                            "status": overall_status,
                            "status_code": response.status_code,
                            "response": health_data
                        }
                    )
            else:
                self.log_test(
                    "LLM Health - HTTP Error",
                    "FAIL",
                    {
                        "status_code": response.status_code,
                        "response": response.text
                    }
                )
                
        except Exception as e:
            self.log_test(
                "LLM Health - Connection Error",
                "FAIL",
                {"error": str(e)}
            )
    
    async def test_endpoint_consistency(self):
        """Test consistency between /models and /llm/models endpoints"""
        print("🔄 Testing endpoint consistency...")
        
        try:
            # Get models from both endpoints
            models_response = await self.client.get(f"{self.base_url}/models")
            llm_models_response = await self.client.get(f"{self.base_url}/llm/models")
            
            if models_response.status_code == 200 and llm_models_response.status_code == 200:
                models_data = models_response.json()
                llm_models_data = llm_models_response.json()
                
                # Compare by extracting and sorting model names for robust comparison
                models_names = sorted([model.get("name", "") for model in models_data]) if isinstance(models_data, list) else []
                llm_models_names = sorted([model.get("name", "") for model in llm_models_data]) if isinstance(llm_models_data, list) else []
                
                # Check if the model lists are equivalent (same models, regardless of order)
                are_consistent = models_names == llm_models_names
                
                self.log_test(
                    "Endpoint Consistency - /models vs /llm/models",
                    "PASS" if are_consistent else "FAIL",
                    {
                        "models_count": len(models_data) if isinstance(models_data, list) else "invalid",
                        "llm_models_count": len(llm_models_data) if isinstance(llm_models_data, list) else "invalid",
                        "responses_match": are_consistent,
                        "models_sample": models_names[:5] if models_names else [],
                        "llm_models_sample": llm_models_names[:5] if llm_models_names else []
                    }
                )
            else:
                self.log_test(
                    "Endpoint Consistency - HTTP Errors",
                    "FAIL",
                    {
                        "models_status": models_response.status_code,
                        "llm_models_status": llm_models_response.status_code
                    }
                )
                
        except Exception as e:
            self.log_test(
                "Endpoint Consistency - Connection Error",
                "FAIL",
                {"error": str(e)}
            )
    
    async def test_openapi_documentation(self):
        """Test that new endpoints are documented in OpenAPI schema"""
        print("📚 Testing OpenAPI documentation...")
        
        try:
            response = await self.client.get(f"{self.base_url}/openapi.json")
            
            if response.status_code == 200:
                openapi_spec = response.json()
                paths = openapi_spec.get("paths", {})
                
                # Check for /models endpoint
                models_documented = "/models" in paths
                health_llm_documented = "/health/llm" in paths
                
                self.log_test(
                    "OpenAPI Documentation - Endpoint Coverage",
                    "PASS" if models_documented and health_llm_documented else "FAIL",
                    {
                        "models_endpoint_documented": models_documented,
                        "health_llm_endpoint_documented": health_llm_documented,
                        "total_endpoints": len(paths)
                    }
                )
                
                # Check endpoint details
                if models_documented:
                    models_spec = paths["/models"].get("get", {})
                    has_summary = "summary" in models_spec
                    has_description = "description" in models_spec
                    
                    self.log_test(
                        "OpenAPI Documentation - /models Details",
                        "PASS" if has_summary and has_description else "WARN",
                        {
                            "has_summary": has_summary,
                            "has_description": has_description,
                            "summary": models_spec.get("summary", "")
                        }
                    )
                
                if health_llm_documented:
                    health_spec = paths["/health/llm"].get("get", {})
                    has_summary = "summary" in health_spec
                    has_description = "description" in health_spec
                    
                    self.log_test(
                        "OpenAPI Documentation - /health/llm Details",
                        "PASS" if has_summary and has_description else "WARN",
                        {
                            "has_summary": has_summary,
                            "has_description": has_description,
                            "summary": health_spec.get("summary", "")
                        }
                    )
            else:
                self.log_test(
                    "OpenAPI Documentation - Access Error",
                    "FAIL",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "OpenAPI Documentation - Connection Error",
                "FAIL",
                {"error": str(e)}
            )
    
    async def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Step 5 Endpoint Tests")
        print("=" * 50)
        print()
        
        # Run all test suites
        await self.test_models_endpoint()
        await self.test_health_llm_endpoint()
        await self.test_endpoint_consistency()
        await self.test_openapi_documentation()
        
        # Summary
        print("📊 Test Summary")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        warning_tests = len([r for r in self.test_results if r["status"] == "WARN"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"⚠️  Warnings: {warning_tests}")
        print(f"❌ Failed: {failed_tests}")
        print()
        
        if failed_tests == 0:
            print("🎉 All critical tests passed! Step 5 endpoints are working correctly.")
        else:
            print("⚠️  Some tests failed. Please check the LocalAI service and configuration.")
        
        return failed_tests == 0
    
    async def interactive_mode(self):
        """Interactive testing mode for manual verification"""
        print("🔧 Interactive Testing Mode")
        print("Available commands:")
        print("  models    - Test /models endpoint")
        print("  health    - Test /health/llm endpoint")
        print("  consistency - Test endpoint consistency")
        print("  docs      - Test OpenAPI documentation")
        print("  all       - Run all tests")
        print("  quit      - Exit interactive mode")
        print()
        
        while True:
            try:
                command = input("Enter command: ").strip().lower()
                
                if command == "quit":
                    break
                elif command == "models":
                    await self.test_models_endpoint()
                elif command == "health":
                    await self.test_health_llm_endpoint()
                elif command == "consistency":
                    await self.test_endpoint_consistency()
                elif command == "docs":
                    await self.test_openapi_documentation()
                elif command == "all":
                    await self.run_all_tests()
                else:
                    print("Unknown command. Available: models, health, consistency, docs, all, quit")
                
                print()
                
            except KeyboardInterrupt:
                print("\nExiting interactive mode...")
                break


async def main():
    """Main test runner"""
    # Parse command line arguments
    base_url = "http://localhost:8000"
    interactive = False
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    if len(sys.argv) > 2 and sys.argv[2].lower() == "interactive":
        interactive = True
    
    print(f"Testing Step 5 endpoints at: {base_url}")
    print()
    
    async with Step5EndpointTester(base_url) as tester:
        if interactive:
            await tester.interactive_mode()
        else:
            success = await tester.run_all_tests()
            sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
