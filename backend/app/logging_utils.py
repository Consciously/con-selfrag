from loguru import logger
import sys
import os
from pathlib import Path
from typing import Optional, Any, Dict

# Remove default handler to configure custom ones
logger.remove()

def setup_logging(log_level: str = "INFO", debug_logging: bool = False, performance_logging: bool = False):
    """
    Configure logging with developer toggles.
    
    Args:
        log_level: Base logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        debug_logging: Enable verbose debug logging with request details
        performance_logging: Enable performance metric logging
    """
    # Determine console log level
    console_level = "DEBUG" if debug_logging else log_level
    
    # Enhanced console format for debug mode
    if debug_logging:
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
    else:
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
    
    # Console handler
    logger.add(
        sys.stdout,
        level=console_level,
        format=console_format,
        colorize=True,
        backtrace=debug_logging,
        diagnose=debug_logging,
        filter=lambda record: _should_log_record(record, performance_logging)
    )
    
    # Set up file logging
    setup_file_logging(log_level, debug_logging, performance_logging)


def _should_log_record(record: Any, performance_logging: bool) -> bool:
    """Filter log records based on performance logging setting."""
    if not performance_logging:
        # Filter out performance-related logs unless enabled
        performance_keywords = ["duration_ms", "response_time", "performance", "metric"]
        message = str(record["message"]).lower()
        extra = record.get("extra", {})
        
        # Check if this is a performance log
        is_performance_log = (
            any(keyword in message for keyword in performance_keywords) or
            any(keyword in str(extra).lower() for keyword in performance_keywords)
        )
        
        # Skip performance logs if performance logging is disabled
        if is_performance_log and record["level"].name in ["DEBUG", "INFO"]:
            return False
    
    return True


def setup_file_logging(log_level: str, debug_logging: bool, performance_logging: bool):
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
            # Main application log with enhanced format for debug mode
            if debug_logging:
                app_format = (
                    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
                    "{name}:{function}:{line} - {message}"
                )
            else:
                app_format = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
            
            logger.add(
                log_dir / "app.log",
                rotation="10 MB",
                retention="30 days",
                level="DEBUG" if debug_logging else log_level,
                format=app_format,
                backtrace=debug_logging,
                diagnose=debug_logging,
                serialize=False,
                filter=lambda record: _should_log_record(record, performance_logging)
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
            
            # Performance log file (only if performance logging is enabled)
            if performance_logging:
                logger.add(
                    log_dir / "performance.log",
                    rotation="5 MB", 
                    retention="7 days",
                    level="DEBUG",
                    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {message}",
                    filter=lambda record: any(
                        keyword in str(record["message"]).lower() or keyword in str(record.get("extra", {})).lower()
                        for keyword in ["duration_ms", "response_time", "performance", "metric"]
                    )
                )
            
            logger.info(f"File logging enabled in: {log_dir}")
            if debug_logging:
                logger.debug("Debug logging enabled - verbose output active")
            if performance_logging:
                logger.debug("Performance logging enabled - metrics will be logged")
        else:
            logger.warning("File logging disabled due to permission issues - using console logging only")
            
    except Exception as e:
        logger.warning(f"Failed to set up file logging: {e} - using console logging only")


# Initialize with default settings (will be reconfigured when config loads)
setup_logging()


def get_logger(name: str = None):
    """Get a configured logger instance."""
    if name:
        return logger.bind(name=name, request_id="")
    return logger.bind(request_id="")


def get_debug_logger(name: str = None, request_id: str = ""):
    """Get a logger configured for debug mode with request tracking."""
    if name:
        return logger.bind(name=name, request_id=request_id or "")
    return logger.bind(request_id=request_id or "")


def log_request(request, response=None, duration=None, **kwargs) -> Dict[str, Any]:
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


def log_performance(operation: str, duration: float, **kwargs):
    """Log performance metrics when performance logging is enabled."""
    perf_logger = logger.bind(performance=True)
    perf_logger.info(
        f"Performance: {operation}",
        extra={
            "operation": operation,
            "duration_ms": round(duration * 1000, 2),
            **kwargs
        }
    )


def reconfigure_logging(log_level: str = "INFO", debug_logging: bool = False, performance_logging: bool = False):
    """Reconfigure logging with new settings."""
    # Remove existing handlers
    logger.remove()
    # Set up with new configuration
    setup_logging(log_level, debug_logging, performance_logging)
