"""
Middleware package for FastAPI application
"""
from app.presentation.middleware.error_handler import setup_error_handlers

__all__ = ['setup_error_handlers']

