#!/usr/bin/env python3
"""
Completely isolated logging test - no app imports
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Configure logging directly without app imports
from loguru import logger

def setup_isolated_logging():
    """Set up logging configuration directly"""
    
    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Remove default handler
    logger.remove()
    
    # Console handler with colors
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # File handler with rotation
    logger.add(
        "logs/app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )
    
    # Error file with JSON format
    logger.add(
        "logs/error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="5 MB",
        retention="30 days",
        compression="zip",
        serialize=True,
    )
    
    return logger

def test_basic_logging(test_logger):
    """Test basic logging"""
    print("🧪 Testing basic logging...")
    
    test_logger.debug("Debug message - should appear in file but not console")
    test_logger.info("Info message - should appear in both console and file")
    test_logger.warning("Warning message - should appear in both")
    test_logger.error("Error message - should appear in console, file, and error log")
    
    print("✅ Basic logging test completed")

def test_structured_logging(test_logger):
    """Test structured logging"""
    print("🧪 Testing structured logging...")
    
    test_logger.info(
        "Processing request",
        endpoint="/test",
        method="POST",
        user_id=12345,
        request_size=1024,
        processing_time_ms=45.67
    )
    
    test_logger.error(
        "Database connection failed",
        operation="connect",
        database="test_db",
        retry_count=3,
        exc_info=True
    )
    
    print("✅ Structured logging test completed")

def test_file_output():
    """Test file output"""
    print("🧪 Testing file output...")
    
    log_dir = Path("logs")
    app_log = log_dir / "app.log"
    error_log = log_dir / "error.log"
    
    print(f"📁 Log directory: {log_dir.absolute()}")
    print(f"📄 app.log exists: {app_log.exists()}")
    print(f"📄 error.log exists: {error_log.exists()}")
    
    if app_log.exists():
        with open(app_log, 'r') as f:
            content = f.read()
            lines = content.strip().split('\n')
            print(f"📊 Lines in app.log: {len(lines)}")
            if lines:
                print(f"📝 Last 3 lines:")
                for line in lines[-3:]:
                    print(f"   {line}")
    
    if error_log.exists():
        with open(error_log, 'r') as f:
            content = f.read()
            lines = content.strip().split('\n')
            print(f"📊 Lines in error.log: {len(lines)}")
    
    print("✅ File output test completed")

def simulate_api_calls(test_logger):
    """Simulate API request/response logging"""
    print("🧪 Simulating API calls...")
    
    # Simulate request
    start_time = time.time()
    test_logger.info(
        "Incoming request",
        method="POST",
        url="/api/v1/ingest",
        client_ip="127.0.0.1",
        user_agent="curl/7.68.0"
    )
    
    # Simulate processing
    time.sleep(0.1)
    
    # Simulate response
    duration = time.time() - start_time
    test_logger.info(
        "Request completed",
        method="POST",
        url="/api/v1/ingest",
        status_code=200,
        duration_ms=round(duration * 1000, 2),
        content_length=256
    )
    
    print("✅ API simulation completed")

def main():
    """Main test runner"""
    print("🚀 Starting isolated logging test...")
    print(f"📍 Working directory: {Path.cwd()}")
    
    # Set up logging
    test_logger = setup_isolated_logging()
    
    # Run tests
    test_basic_logging(test_logger)
    print()
    
    test_structured_logging(test_logger)
    print()
    
    simulate_api_calls(test_logger)
    print()
    
    test_file_output()
    print()
    
    print("🎉 All isolated logging tests completed!")
    print("📁 Check the logs/ directory for output files")
    print("📝 You can view logs with: tail -f logs/app.log")

if __name__ == "__main__":
    main()
