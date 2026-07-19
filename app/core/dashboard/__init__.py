"""
Module 7 — Risk Dashboard

This module provides the user interface and APIs for viewing scan results.
"""

from flask import Blueprint

dashboard_bp = Blueprint('dashboard', __name__)

# Import routes at bottom to avoid circular imports
from app.core.dashboard import routes
