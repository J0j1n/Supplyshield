"""
Module 1 — Secure Scan Manager: Routes

Handles HTTP endpoints for project upload and scan management.
"""
import logging
from flask import request, jsonify, render_template, redirect, url_for, flash, current_app
from app.core.scan_manager import scan_bp
from app.core.scan_manager.service import ScanService

logger = logging.getLogger(__name__)

def _get_service() -> ScanService:
    return ScanService(
        upload_folder=current_app.config['UPLOAD_FOLDER'],
        workspace_folder=current_app.config['WORKSPACE_FOLDER']
    )

@scan_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('scan/upload.html')
        
    try:
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
            
        file = request.files['file']
        project_name = request.form.get('project_name', '').strip()
        if not project_name:
            project_name = file.filename
            
        service = _get_service()
        result = service.initiate_scan(file, project_name)
        
        if result['success']:
            flash('Scan initiated successfully.', 'success')
            return redirect(url_for('scan.status', scan_id=result['scan_id']))
        else:
            flash(f"Upload failed: {result['error']}", 'error')
            return redirect(request.url)
            
    except Exception as e:
        logger.exception("Exception during file upload")
        flash(f"An unexpected error occurred: {str(e)}", 'error')
        return redirect(request.url)

@scan_bp.route('/status/<scan_id>', methods=['GET'])
def status(scan_id):
    service = _get_service()
    status_data = service.get_scan_status(scan_id)
    
    if not status_data.get('found'):
        flash('Scan not found.', 'error')
        return redirect(url_for('scan.upload'))
        
    if request.headers.get('Accept') == 'application/json':
        return jsonify(status_data)
        
    return render_template('scan/status.html', scan=status_data)

@scan_bp.route('/results/<scan_id>', methods=['GET'])
def results(scan_id):
    service = _get_service()
    results_data = service.get_scan_results(scan_id)
    return jsonify(results_data)

@scan_bp.route('/cleanup/<scan_id>', methods=['POST'])
def cleanup(scan_id):
    service = _get_service()
    result = service.cleanup_scan(scan_id)
    if result.get('success', True):
        flash('Cleanup completed successfully.', 'success')
    else:
        flash('Cleanup encountered errors.', 'warning')
    # Use dashboard if it exists, otherwise back to root index
    try:
        return redirect(url_for('dashboard.index'))
    except:
        return redirect(url_for('main.index'))
