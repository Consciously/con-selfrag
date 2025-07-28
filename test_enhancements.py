#!/usr/bin/env python3
"""
Comprehensive test script for FastAPI enhancements.
Tests OpenAPI documentation, async operations, Prometheus metrics, and health checks.
"""

import asyncio
import json
import time
import requests
from typing import Dict, Any
import sys


class FastAPIEnhancementTester:
    """Test suite for FastAPI service enhancements."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    def test_service_availability(self) -> bool:
        """Test if the service is running and accessible."""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Service Availability", 
                    True, 
                    f"Service running - {data.get('name', 'Unknown')}"
                )
                return True
            else:
                self.log_test(
                    "Service Availability", 
                    False, 
                    f"HTTP {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test("Service Availability", False, str(e))
            return False
    
    def test_openapi_documentation(self) -> bool:
        """Test OpenAPI documentation enhancements."""
        try:
            # Test OpenAPI spec
            response = self.session.get(f"{self.base_url}/openapi.json")
            if response.status_code != 200:
                self.log_test("OpenAPI Spec", False, f"HTTP {response.status_code}")
                return False
            
            openapi_spec = response.json()
            
            # Check for enhanced documentation
            checks = [
                ("title" in openapi_spec and "🤖" in openapi_spec["title"], "Enhanced title with emoji"),
                ("description" in openapi_spec and len(openapi_spec["description"]) > 100, "Rich description"),
                ("tags" in openapi_spec and len(openapi_spec["tags"]) >= 5, "Comprehensive tags"),
                ("paths" in openapi_spec, "API paths defined"),
            ]
            
            all_passed = True
            for check, description in checks:
                if check:
                    self.log_test(f"OpenAPI - {description}", True)
                else:
                    self.log_test(f"OpenAPI - {description}", False)
                    all_passed = False
            
            # Test interactive docs accessibility
            docs_response = self.session.get(f"{self.base_url}/docs")
            docs_available = docs_response.status_code == 200
            self.log_test("Interactive Docs (/docs)", docs_available)
            
            return all_passed and docs_available
            
        except Exception as e:
            self.log_test("OpenAPI Documentation", False, str(e))
            return False
    
    def test_health_endpoints(self) -> bool:
        """Test health check endpoints."""
        endpoints = [
            ("/health", "Comprehensive Health Check"),
            ("/health/live", "Liveness Probe"),
            ("/health/ready", "Readiness Probe")
        ]
        
        all_passed = True
        for endpoint, description in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    # Check for timestamp in response
                    has_timestamp = "timestamp" in data or "alive" in data or "ready" in data
                    self.log_test(
                        description, 
                        True, 
                        f"Status: {data.get('status', data.get('alive', data.get('ready', 'OK')))}"
                    )
                else:
                    self.log_test(description, False, f"HTTP {response.status_code}")
                    all_passed = False
            except Exception as e:
                self.log_test(description, False, str(e))
                all_passed = False
        
        return all_passed
    
    def test_prometheus_metrics(self) -> bool:
        """Test Prometheus metrics endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/metrics")
            if response.status_code == 200:
                metrics_text = response.text
                
                # Check for expected metrics
                expected_metrics = [
                    "http_requests_total",
                    "http_request_duration_seconds",
                    "ollama_requests_total", 
                    "ollama_request_duration_seconds"
                ]
                
                found_metrics = []
                for metric in expected_metrics:
                    if metric in metrics_text:
                        found_metrics.append(metric)
                
                success = len(found_metrics) >= 2  # At least basic HTTP metrics
                self.log_test(
                    "Prometheus Metrics", 
                    success, 
                    f"Found {len(found_metrics)}/{len(expected_metrics)} expected metrics"
                )
                return success
            else:
                self.log_test("Prometheus Metrics", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Prometheus Metrics", False, str(e))
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test main API endpoints with example payloads."""
        all_passed = True
        
        # Test /models endpoint
        try:
            response = self.session.get(f"{self.base_url}/models")
            if response.status_code == 200:
                data = response.json()
                has_models = "models" in data and "count" in data
                self.log_test(
                    "Models Endpoint", 
                    has_models, 
                    f"Found {data.get('count', 0)} models" if has_models else "Invalid response format"
                )
            else:
                self.log_test("Models Endpoint", False, f"HTTP {response.status_code}")
                all_passed = False
        except Exception as e:
            self.log_test("Models Endpoint", False, str(e))
            all_passed = False
        
        # Test /generate endpoint (without actually generating - just check validation)
        try:
            # Test with invalid payload to check validation
            invalid_payload = {"prompt": "", "temperature": 3.0}  # Invalid temperature
            response = self.session.post(f"{self.base_url}/generate", json=invalid_payload)
            
            # Should return 422 for validation error
            validation_works = response.status_code == 422
            self.log_test(
                "Generate Endpoint Validation", 
                validation_works, 
                f"Validation {'working' if validation_works else 'not working'}"
            )
            
        except Exception as e:
            self.log_test("Generate Endpoint Validation", False, str(e))
            all_passed = False
        
        # Test /ask endpoint validation
        try:
            invalid_payload = {"question": "", "temperature": -1.0}  # Invalid temperature
            response = self.session.post(f"{self.base_url}/ask", json=invalid_payload)
            
            validation_works = response.status_code == 422
            self.log_test(
                "Ask Endpoint Validation", 
                validation_works, 
                f"Validation {'working' if validation_works else 'not working'}"
            )
            
        except Exception as e:
            self.log_test("Ask Endpoint Validation", False, str(e))
            all_passed = False
        
        return all_passed
    
    def test_response_schemas(self) -> bool:
        """Test that responses match expected schemas."""
        try:
            # Test root endpoint response structure
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                
                expected_fields = ["name", "version", "description", "endpoints", "features"]
                has_all_fields = all(field in data for field in expected_fields)
                
                self.log_test(
                    "Root Endpoint Schema", 
                    has_all_fields, 
                    f"Has {sum(1 for field in expected_fields if field in data)}/{len(expected_fields)} expected fields"
                )
                return has_all_fields
            else:
                self.log_test("Root Endpoint Schema", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Root Endpoint Schema", False, str(e))
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return summary."""
        print("🧪 Starting FastAPI Enhancement Tests\n")
        
        # Check if service is available first
        if not self.test_service_availability():
            print("\n❌ Service not available. Please start the service first:")
            print("   docker-compose up -d")
            return {"success": False, "message": "Service not available"}
        
        print()
        
        # Run all test suites
        test_suites = [
            ("OpenAPI Documentation", self.test_openapi_documentation),
            ("Health Endpoints", self.test_health_endpoints),
            ("Prometheus Metrics", self.test_prometheus_metrics),
            ("API Endpoints", self.test_api_endpoints),
            ("Response Schemas", self.test_response_schemas),
        ]
        
        suite_results = []
        for suite_name, test_func in test_suites:
            print(f"\n📋 Testing {suite_name}:")
            result = test_func()
            suite_results.append(result)
            print()
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        print("="*50)
        print(f"📊 TEST SUMMARY")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        overall_success = passed_tests == total_tests
        if overall_success:
            print("\n🎉 All enhancements are working correctly!")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} tests failed. Check the details above.")
        
        return {
            "success": overall_success,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "results": self.test_results
        }


def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test FastAPI enhancements")
    parser.add_argument(
        "--url", 
        default="http://localhost:8000", 
        help="Base URL of the FastAPI service"
    )
    
    args = parser.parse_args()
    
    tester = FastAPIEnhancementTester(args.url)
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()
