"""Routes package"""
from .auth import auth_bp
from .dashboard import dashboard_bp
from .metadata import metadata_bp
from .analysis import analysis_bp
from .test import test_bp

__all__ = ['auth_bp', 'dashboard_bp', 'metadata_bp', 'analysis_bp', 'test_bp']