#!/usr/bin/env python3
"""
Standalone test for the logging system - no app dependencies
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add the backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import directly from logging_utils
from app.logging_utils import get_logger, log_request

def test_basic_logging():
    """Test basic logging functionality"""
    print("🧪 Testing basic logging...")
    
    # Create a test logger
    logger = get_logger("test_logger")
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print("✅ Basic logging test completed")

def test_structured_logging():
    """Test structured logging with extra data"""
    print("🧪 Testing structured logging...")
    
    logger = get_logger("structured_test")
    
    # Test with structured data
    logger.info(
        "Processing request",
        extra={
            "endpoint": "/test",
            "method": "POST",
            "user_id": 12345,
            "request_size": 1024,
            "processing_time_ms": 45.67
        }
    )
    
    print("✅ Structured logging test completed")

def test_file_output():
    """Test that logs are written to files"""
    print("🧪 Testing file output...")
    
    # Check if log files exist
    log_dir = Path("logs")
    app_log = log_dir / "app.log"
    error_log = log_dir / "error.log"
    
    print(f"📁 Log directory exists: {log_dir.exists()}")
    if log_dir.exists():
        print(f"📄 app.log exists: {app_log.exists()}")
        print(f"📄 error.log exists: {error_log.exists()}")
        
        if app_log.exists():
            with open(app_log, 'r') as f:
                lines = f.readlines()
                print(f"📊 Lines in app.log: {len(lines)}")
                if lines:
                    print(f"📝 Last log line: {lines[-1].strip()}")
    
    print("✅ File output test completed")

async def test_async_logging():
    """Test async logging"""
    print("🧪 Testing async logging...")
    
    logger = get_logger("async_test")
    
    async def async_task(task_id: int):
        logger.info(
            "Starting async task",
            extra={"task_id": task_id, "task_type": "async_test"}
        )
        await asyncio.sleep(0.1)
        logger.info(
            "Completed async task",
            extra={"task_id": task_id, "duration_ms": 100}
        )
    
    # Run multiple async tasks
    tasks = [async_task(i) for i in range(3)]
    await asyncio.gather(*tasks)
    
    print("✅ Async logging test completed")

def test_error_logging():
    """Test error logging with exception info"""
    print("🧪 Testing error logging...")
    
    logger = get_logger("error_test")
    
    try:
        # Simulate an error
        result = 1 / 0
    except ZeroDivisionError as e:
        logger.error(
            "Division by zero occurred",
            extra={"operation": "division", "numerator": 1, "denominator": 0},
            exc_info=True
        )
    
    print("✅ Error logging test completed")

def test_log_request_helper():
    """Test the log_request helper function"""
    print("🧪 Testing log_request helper...")
    
    # Mock request data
    class MockRequest:
        def __init__(self):
            self.method = "POST"
            self.url = "http://localhost:8000/test"
            self.client = type('Client', (), {'host': '127.0.0.1'})()
    
    request = MockRequest()
    
    # Test log_request without response
    log_data = log_request(request)
    print(f"📋 Request log data: {log_data}")
    
    # Test log_request with response
    class MockResponse:
        def __init__(self):
            self.status_code = 200
    
    response = MockResponse()
    log_data_with_response = log_request(request, response, 0.123)
    print(f"📋 Response log data: {log_data_with_response}")
    
    print("✅ log_request helper test completed")

async def main():
    """Main test runner"""
    print("🚀 Starting logging system tests...\n")
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Run all tests
    test_basic_logging()
    print()
    
    test_structured_logging()
    print()
    
    test_file_output()
    print()
    
    await test_async_logging()
    print()
    
    test_error_logging()
    print()
    
    test_log_request_helper()
    print()
    
    print("🎉 All logging tests completed successfully!")
    print("📁 Check the logs/ directory for output files")

if __name__ == "__main__":
    asyncio.run(main())
