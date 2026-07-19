"""
Module 1 — Secure Scan Manager

This module handles the initiation of scans, processing of uploaded ZIP files,
and routing for scan-related endpoints.
"""

from flask import Blueprint

scan_bp = Blueprint('scan', __name__)

# Import routes at bottom to avoid circular imports
from app.core.scan_manager import routes
