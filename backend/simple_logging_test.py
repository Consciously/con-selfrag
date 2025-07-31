#!/usr/bin/env python3
"""
Very simple logging test - just test the logging_utils directly
"""
import os
import sys
from pathlib import Path

# Ensure we're in the right directory
os.chdir(Path(__file__).parent)

# Import logging_utils directly
from app.logging_utils import get_logger

def main():
    print("🚀 Starting simple logging test...")
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Get a logger
    logger = get_logger("simple_test")
    
    # Test basic logging
    logger.info("🎯 This is a test info message")
    logger.warning("⚠️  This is a test warning")
    logger.error("❌ This is a test error")
    
    # Test structured logging
    logger.info(
        "📊 Structured log example",
        extra={
            "test": True,
            "user_id": 123,
            "endpoint": "/test",
            "duration_ms": 42.5
        }
    )
    
    print("✅ Simple logging test completed!")
    print("📁 Check logs/app.log for output")

if __name__ == "__main__":
    main()
