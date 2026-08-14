import os
import logging
from flask import Flask, Blueprint, render_template
from config import config
from app.extensions import db


def create_app(config_name='development'):
    """Application factory for SupplyShield."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['WORKSPACE_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
    
    logs_dir = os.path.join(app.root_path, '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Set up logging
    log_file = os.path.join(logs_dir, 'supplyshield.log')
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    
    # Create database tables
    with app.app_context():
        from app.models import scan as scan_models  # noqa: F401 — ensure models are registered
        db.create_all()
    
    # Register blueprints
    try:
        from app.core.scan_manager import scan_bp
        app.register_blueprint(scan_bp, url_prefix='/scan')
    except ImportError as e:
        app.logger.warning(f"Failed to import scan_bp: {e}")
        
    try:
        from app.core.dashboard import dashboard_bp
        app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    except ImportError as e:
        app.logger.warning(f"Failed to import dashboard_bp: {e}")
        
    # Main index blueprint
    main_bp = Blueprint('main', __name__)
    
    @main_bp.route('/')
    def index():
        return render_template('index.html')
    
    app.register_blueprint(main_bp, url_prefix='/')
    
    return app
