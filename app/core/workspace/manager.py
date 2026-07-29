"""
Module 2 — Temporary Workspace Manager

Manages ephemeral workspaces for secure dependency analysis.
Each scan gets an isolated workspace that is destroyed after analysis.
"""
import os
import shutil
import zipfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class WorkspaceManager:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path).resolve()

    def create(self, scan_id: str) -> str:
        workspace_path = self.base_path / scan_id
        try:
            os.makedirs(workspace_path, exist_ok=False)
            logger.info(f"Created workspace for scan {scan_id} at {workspace_path}")
            return str(workspace_path)
        except Exception as e:
            logger.error(f"Failed to create workspace for scan {scan_id}: {e}")
            raise

    def extract_zip(self, zip_path: str, workspace_path: str) -> bool:
        try:
            extracted_count = 0
            with zipfile.ZipFile(zip_path, 'r') as z:
                for info in z.infolist():
                    # Skip potentially malicious paths
                    if '..' in info.filename or info.filename.startswith('/') or info.filename.startswith('\\'):
                        logger.warning(f"Skipping path traversal entry: {info.filename}")
                        continue
                    
                    z.extract(info, workspace_path)
                    extracted_count += 1
            logger.info(f"Extracted {extracted_count} files to {workspace_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to extract zip to {workspace_path}: {e}")
            return False

    def get_path(self, scan_id: str) -> str:
        return str(self.base_path / scan_id)

    def exists(self, scan_id: str) -> bool:
        return os.path.isdir(self.get_path(scan_id))

    def destroy(self, scan_id: str) -> bool:
        workspace_path = Path(self.get_path(scan_id)).resolve()
        
        # Security check: verify path is under base_path
        if not str(workspace_path).startswith(str(self.base_path)):
            logger.error(f"Security check failed: {workspace_path} is not under {self.base_path}")
            return False
            
        try:
            if workspace_path.exists() and workspace_path.is_dir():
                shutil.rmtree(workspace_path)
                logger.info(f"Destroyed workspace for scan {scan_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to destroy workspace for scan {scan_id}: {e}")
            return False

    def list_files(self, scan_id: str) -> list[dict]:
        workspace_path = self.get_path(scan_id)
        files = []
        try:
            for root, dirs, filenames in os.walk(workspace_path):
                for d in dirs:
                    full_path = os.path.join(root, d)
                    rel_path = os.path.relpath(full_path, workspace_path)
                    files.append({
                        'path': rel_path,
                        'size': 0,
                        'is_dir': True
                    })
                for f in filenames:
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, workspace_path)
                    size = os.path.getsize(full_path)
                    files.append({
                        'path': rel_path,
                        'size': size,
                        'is_dir': False
                    })
            files.sort(key=lambda x: x['path'])
            return files
        except Exception as e:
            logger.error(f"Failed to list files for scan {scan_id}: {e}")
            return []

    def get_size(self, scan_id: str) -> int:
        workspace_path = self.get_path(scan_id)
        total_size = 0
        try:
            for root, _, filenames in os.walk(workspace_path):
                for f in filenames:
                    total_size += os.path.getsize(os.path.join(root, f))
            return total_size
        except Exception as e:
            logger.error(f"Failed to get size for scan {scan_id}: {e}")
            return 0
