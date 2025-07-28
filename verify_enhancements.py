#!/usr/bin/env python3
"""
Simple verification script to check FastAPI enhancements.
Can be run directly to verify the service is working correctly.
"""

import sys
import os
import subprocess
import json
from pathlib import Path


def check_file_syntax(file_path: str) -> bool:
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r') as f:
            compile(f.read(), file_path, 'exec')
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking {file_path}: {e}")
        return False


def check_imports(file_path: str) -> bool:
    """Check if all imports in a file can be resolved."""
    try:
        # Add the backend directory to Python path
        backend_dir = Path(file_path).parent.parent
        sys.path.insert(0, str(backend_dir))
        
        # Try to import the module
        module_name = Path(file_path).stem
        if module_name == 'main':
            import backend.app.main
        elif module_name == 'models':
            import backend.app.models
        elif module_name == 'config':
            import backend.app.config
        
        return True
    except ImportError as e:
        print(f"❌ Import error in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error importing {file_path}: {e}")
        return False


def verify_dependencies() -> bool:
    """Verify that required dependencies are listed in pyproject.toml."""
    try:
        pyproject_path = "backend/pyproject.toml"
        with open(pyproject_path, 'r') as f:
            content = f.read()
        
        required_deps = [
            "fastapi",
            "prometheus-client", 
            "prometheus-fastapi-instrumentator",
            "loguru",
            "pydantic",
            "uvicorn"
        ]
        
        missing_deps = []
        for dep in required_deps:
            if dep not in content:
                missing_deps.append(dep)
        
        if missing_deps:
            print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
            return False
        
        print("✅ All required dependencies found in pyproject.toml")
        return True
        
    except Exception as e:
        print(f"❌ Error checking dependencies: {e}")
        return False


def verify_enhanced_features() -> bool:
    """Verify that enhanced features are present in the code."""
    try:
        # Check main.py for enhancements
        with open("backend/app/main.py", 'r') as f:
            main_content = f.read()
        
        # Check models.py for enhancements  
        with open("backend/app/models.py", 'r') as f:
            models_content = f.read()
        
        enhancements = [
            ("Prometheus metrics", "prometheus_client" in main_content),
            ("Async operations", "asyncio.to_thread" in main_content),
            ("Health endpoints", "/health/live" in main_content),
            ("Enhanced OpenAPI", "openapi_tags" in main_content),
            ("Rich descriptions", "🤖" in main_content),
            ("Example payloads", "json_schema_extra" in models_content),
            ("Comprehensive models", "LivenessCheck" in models_content),
        ]
        
        all_present = True
        for feature, check in enhancements:
            if check:
                print(f"✅ {feature} - Present")
            else:
                print(f"❌ {feature} - Missing")
                all_present = False
        
        return all_present
        
    except Exception as e:
        print(f"❌ Error verifying features: {e}")
        return False


def main():
    """Main verification function."""
    print("🔍 Verifying FastAPI Enhancements\n")
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    checks = [
        ("Dependencies", verify_dependencies),
        ("Python Syntax - main.py", lambda: check_file_syntax("backend/app/main.py")),
        ("Python Syntax - models.py", lambda: check_file_syntax("backend/app/models.py")),
        ("Enhanced Features", verify_enhanced_features),
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"📋 {check_name}:")
        result = check_func()
        results.append(result)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("="*50)
    print(f"📊 VERIFICATION SUMMARY")
    print(f"Checks Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All verifications passed!")
        print("\n🚀 Next steps:")
        print("1. Start the service: docker-compose up -d")
        print("2. Visit http://localhost:8000/docs for interactive API docs")
        print("3. Check health: curl http://localhost:8000/health")
        print("4. View metrics: curl http://localhost:8000/metrics")
        return True
    else:
        print(f"\n⚠️  {total - passed} checks failed.")
        print("Please review the errors above before starting the service.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
