"""
Module 9 — Automatic Cleanup Engine

Ensures zero source code retention by securely deleting all temporary
files after scan completion. This is a core privacy guarantee.
"""
import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class CleanupEngine:
    def __init__(self, upload_folder: str, workspace_folder: str):
        self.upload_folder = Path(upload_folder).resolve()
        self.workspace_folder = Path(workspace_folder).resolve()

    def _is_safe_path(self, path: str, base_dir: str) -> bool:
        try:
            resolved_path = Path(path).resolve()
            resolved_base = Path(base_dir).resolve()
            return str(resolved_path).startswith(str(resolved_base))
        except Exception as e:
            logger.error(f"Error checking safe path: {e}")
            return False

    def cleanup_scan(self, scan_id: str, upload_filename: str = None) -> dict:
        result = {
            'workspace_cleaned': self.cleanup_workspace(scan_id),
            'upload_cleaned': False,
            'verified': False,
            'errors': []
        }
        
        if upload_filename:
            result['upload_cleaned'] = self.cleanup_upload(upload_filename)
            
        verification = self.verify_cleanup(scan_id, upload_filename)
        result['verified'] = verification.get('clean', False)
        if not result['verified']:
            result['errors'] = verification.get('remaining', [])
            
        return result

    def cleanup_workspace(self, scan_id: str) -> bool:
        workspace_path = self.workspace_folder / scan_id
        
        if not self._is_safe_path(workspace_path, self.workspace_folder):
            logger.error(f"Security error: path {workspace_path} not under {self.workspace_folder}")
            return False
            
        try:
            if workspace_path.exists():
                def onerror(func, path, exc_info):
                    logger.warning(f"Error removing {path}: {exc_info}")
                shutil.rmtree(workspace_path, onerror=onerror)
                logger.info(f"Cleaned up workspace {workspace_path}")
                return True
            return True # Already clean
        except Exception as e:
            logger.error(f"Failed to cleanup workspace {workspace_path}: {e}")
            return False

    def cleanup_upload(self, filename: str) -> bool:
        upload_path = self.upload_folder / filename
        
        if not self._is_safe_path(upload_path, self.upload_folder):
            logger.error(f"Security error: path {upload_path} not under {self.upload_folder}")
            return False
            
        if upload_path.exists():
            return self.secure_delete(str(upload_path))
        return True # Already clean

    def verify_cleanup(self, scan_id: str, upload_filename: str = None) -> dict:
        remaining = []
        workspace_path = self.workspace_folder / scan_id
        
        if workspace_path.exists():
            remaining.append(str(workspace_path))
            
        if upload_filename:
            upload_path = self.upload_folder / upload_filename
            if upload_path.exists():
                remaining.append(str(upload_path))
                
        return {
            'clean': len(remaining) == 0,
            'remaining': remaining
        }

    def secure_delete(self, file_path: str) -> bool:
        try:
            if not os.path.exists(file_path):
                return True
                
            size = os.path.getsize(file_path)
            with open(file_path, 'rb+') as f:
                # Write zeros
                f.write(b'\x00' * size)
                f.flush()
                os.fsync(f.fileno())
                
            os.remove(file_path)
            logger.info(f"Securely deleted {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to securely delete {file_path}: {e}")
            return False
