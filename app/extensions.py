"""
Flask extensions are initialized here to avoid circular dependencies.
Future extensions (e.g., Flask-Migrate, Flask-Login) can be added here.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
