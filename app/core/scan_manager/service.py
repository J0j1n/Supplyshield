"""
Module 1 — Secure Scan Manager: Scan Service

Orchestrates the complete scan upload pipeline:
Upload → Validate → Create Record → Create Workspace → Extract → Cleanup on Failure
"""
import os
import uuid
import logging
from werkzeug.utils import secure_filename

from app.core.scan_manager.validators import (
    allowed_file, validate_file_size, validate_zip_contents, detect_path_traversal, MAX_FILE_SIZE
)
from app.core.workspace.manager import WorkspaceManager
from app.core.cleanup.engine import CleanupEngine
from app.core.metadata_repo.repository import MetadataRepository

logger = logging.getLogger(__name__)

class ScanService:
    def __init__(self, upload_folder: str, workspace_folder: str):
        self.upload_folder = upload_folder
        self.workspace_folder = workspace_folder
        self.workspace_manager = WorkspaceManager(workspace_folder)
        self.cleanup_engine = CleanupEngine(upload_folder, workspace_folder)
        self.metadata_repo = MetadataRepository()

    def validate_upload(self, file) -> tuple[bool, str]:
        if file is None:
            return False, 'No file part'
        if file.filename == '':
            return False, 'No selected file'
        if not allowed_file(file.filename):
            return False, 'File type not allowed'
        
        valid_size, msg = validate_file_size(file, MAX_FILE_SIZE)
        if not valid_size:
            return False, msg
            
        return True, ''

    def initiate_scan(self, file, project_name: str) -> dict:
        try:
            valid, msg = self.validate_upload(file)
            if not valid:
                return {'success': False, 'error': msg}

            sec_filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{sec_filename}"
            saved_path = os.path.join(self.upload_folder, unique_filename)
            
            file.save(saved_path)

            zip_val = validate_zip_contents(saved_path)
            if not zip_val.get('valid', False):
                os.remove(saved_path)
                return {'success': False, 'error': f"Invalid ZIP: {zip_val.get('errors')}"}

            if detect_path_traversal(saved_path):
                os.remove(saved_path)
                return {'success': False, 'error': 'Path traversal detected in ZIP'}

            scan = self.metadata_repo.create_scan(project_name, 'zip')
            self.metadata_repo.update_scan_status(str(scan.id), 'scanning')

            workspace_path = self.workspace_manager.create(str(scan.id))
            
            extracted = self.workspace_manager.extract_zip(saved_path, workspace_path)
            if not extracted:
                self.cleanup_engine.cleanup_scan(str(scan.id), unique_filename)
                self.metadata_repo.update_scan_status(str(scan.id), 'failed')
                return {'success': False, 'error': 'Failed to extract ZIP'}

            self.metadata_repo.update_scan_status(str(scan.id), 'completed')

            return {
                'success': True, 
                'scan_id': str(scan.id), 
                'project_name': project_name, 
                'workspace_path': workspace_path
            }

        except Exception as e:
            logger.exception("Error during scan initiation")
            return {'success': False, 'error': str(e)}

    def get_scan_status(self, scan_id: str) -> dict:
        scan = self.metadata_repo.get_scan(scan_id)
        if not scan:
            return {'found': False}
        return {
            'found': True,
            'scan_id': str(scan.id),
            'project_name': scan.project_name,
            'status': scan.scan_status,
            'created_at': scan.created_at.isoformat() if scan.created_at else None,
            'completed_at': scan.completed_at.isoformat() if scan.completed_at else None
        }

    def get_scan_results(self, scan_id: str) -> dict:
        scan = self.metadata_repo.get_scan(scan_id)
        if not scan:
            return {'found': False}
            
        workspace_exists = self.workspace_manager.exists(scan_id)
        file_list = []
        if workspace_exists:
            file_list = self.workspace_manager.list_files(scan_id)
            
        return {
            'found': True,
            'scan': {
                'id': str(scan.id),
                'project_name': scan.project_name,
                'status': scan.scan_status
            },
            'files': file_list,
            'workspace_exists': workspace_exists
        }

    def cleanup_scan(self, scan_id: str) -> dict:
        self.metadata_repo.update_scan_status(scan_id, 'cleanup')
        result = self.cleanup_engine.cleanup_scan(scan_id)
        self.metadata_repo.update_scan_status(scan_id, 'cleanup_completed', cleanup_completed=True)
        return result
