"""
Selfrag LLM API - Backend Application

Clean template for LLM applications with LocalAI backend.
"""

__version__ = "1.0.0"
__title__ = "Selfrag LLM API"
__description__ = "Clean template for LLM applications with LocalAI backend"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .main import app
from .config import config
from .localai_client import localai_client

__all__ = ["app", "config", "localai_client"]
