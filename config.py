import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class BaseConfig:
    """Common configuration settings."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-change-in-prod')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    WORKSPACE_FOLDER = os.path.join(BASE_DIR, 'workspaces')
    ALLOWED_EXTENSIONS = {'zip'}
    SCAN_TIMEOUT = 300
    AUTO_CLEANUP = True

class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'supplyshield_dev.db')

class ProductionConfig(BaseConfig):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'supplyshield.db')

class TestingConfig(BaseConfig):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
