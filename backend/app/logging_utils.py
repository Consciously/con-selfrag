from loguru import logger
import sys
import os
from pathlib import Path

# Remove default handler to configure custom ones
logger.remove()

# Console handler with structured format (always works)
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
    backtrace=True,
    diagnose=True
)

# Try to set up file logging, but gracefully handle permission errors
def setup_file_logging():
    """Set up file logging with graceful error handling."""
    try:
        # Try different log directory locations
        possible_log_dirs = [
            Path(__file__).parent.parent / "logs",  # Original location
            Path("/tmp/app_logs"),  # Fallback to /tmp
            Path.cwd() / "logs",  # Current working directory
        ]
        
        log_dir = None
        for potential_dir in possible_log_dirs:
            try:
                potential_dir.mkdir(parents=True, exist_ok=True)
                # Test write permissions
                test_file = potential_dir / "test_write.tmp"
                test_file.write_text("test")
                test_file.unlink()  # Clean up test file
                log_dir = potential_dir
                break
            except (PermissionError, OSError):
                continue
        
        if log_dir:
            # File handler with rotation and retention
            logger.add(
                log_dir / "app.log",
                rotation="10 MB",
                retention="30 days",
                level="DEBUG",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                backtrace=True,
                diagnose=True,
                serialize=False
            )

            # Error log file for critical issues
            logger.add(
                log_dir / "error.log",
                rotation="5 MB",
                retention="30 days",
                level="ERROR",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                backtrace=True,
                diagnose=True,
                serialize=True
            )
            
            logger.info(f"File logging enabled in: {log_dir}")
        else:
            logger.warning("File logging disabled due to permission issues - using console logging only")
            
    except Exception as e:
        logger.warning(f"Failed to set up file logging: {e} - using console logging only")

# Set up file logging
setup_file_logging()

def get_logger(name: str = None):
    """Get a configured logger instance."""
    if name:
        return logger.bind(name=name)
    return logger

def log_request(request, response=None, duration=None, **kwargs):
    """Structured logging for HTTP requests."""
    log_data = {
        "method": request.method,
        "url": str(request.url),
        "client": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
        **kwargs
    }
    
    if response:
        log_data["status_code"] = response.status_code
    
    if duration:
        log_data["duration_ms"] = round(duration * 1000, 2)
    
    return log_data
