"""
Module 8 — Metadata Repository

Handles all database operations for scan metadata.
Never stores source code — only analysis results and metadata.
"""
import logging
from datetime import datetime
from app.extensions import db
from app.models.scan import Scan, Dependency, Vulnerability, ScanResult

logger = logging.getLogger(__name__)

class MetadataRepository:
    
    def create_scan(self, project_name: str, source_type: str = 'zip') -> Scan:
        try:
            scan = Scan(
                project_name=project_name,
                source_type=source_type,
                scan_status='pending'
            )
            db.session.add(scan)
            db.session.commit()
            logger.info(f"Created new scan with id {scan.id}")
            return scan
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create scan: {e}")
            raise

    def update_scan_status(self, scan_id: str, status: str, **kwargs) -> bool:
        try:
            scan = db.session.get(Scan, scan_id)
            if not scan:
                logger.error(f"Scan {scan_id} not found.")
                return False
                
            scan.scan_status = status
            if status == 'completed':
                scan.completed_at = datetime.utcnow()
                
            for key, value in kwargs.items():
                if hasattr(scan, key):
                    setattr(scan, key, value)
                    
            db.session.commit()
            logger.info(f"Updated scan {scan_id} status to {status}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update scan status for {scan_id}: {e}")
            return False

    def save_dependencies(self, scan_id: str, dependencies: list[dict]) -> int:
        try:
            count = 0
            for dep_data in dependencies:
                dep = Dependency(
                    scan_id=scan_id,
                    name=dep_data.get('name'),
                    version=dep_data.get('version'),
                    ecosystem=dep_data.get('ecosystem'),
                    is_direct=dep_data.get('is_direct', True),
                    license=dep_data.get('license')
                )
                db.session.add(dep)
                count += 1
            db.session.commit()
            logger.info(f"Saved {count} dependencies for scan {scan_id}")
            return count
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save dependencies for scan {scan_id}: {e}")
            return 0

    def save_vulnerabilities(self, dependency_id: int, vulnerabilities: list[dict]) -> int:
        try:
            count = 0
            for vuln_data in vulnerabilities:
                vuln = Vulnerability(
                    dependency_id=dependency_id,
                    cve_id=vuln_data.get('cve_id'),
                    severity=vuln_data.get('severity'),
                    cvss_score=vuln_data.get('cvss_score'),
                    description=vuln_data.get('description'),
                    affected_versions=vuln_data.get('affected_versions'),
                    fixed_version=vuln_data.get('fixed_version'),
                    source=vuln_data.get('source')
                )
                db.session.add(vuln)
                count += 1
            db.session.commit()
            logger.info(f"Saved {count} vulnerabilities for dependency {dependency_id}")
            return count
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save vulnerabilities for dependency {dependency_id}: {e}")
            return 0

    def save_result(self, scan_id: str, result_type: str, format: str, file_path: str) -> ScanResult:
        try:
            result = ScanResult(
                scan_id=scan_id,
                result_type=result_type,
                format=format,
                file_path=file_path
            )
            db.session.add(result)
            db.session.commit()
            logger.info(f"Saved result {result_type} for scan {scan_id}")
            return result
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save result for scan {scan_id}: {e}")
            raise

    def get_scan(self, scan_id: str) -> Scan:
        try:
            return db.session.get(Scan, scan_id)
        except Exception as e:
            logger.error(f"Failed to get scan {scan_id}: {e}")
            return None

    def get_scan_history(self, limit: int = 50) -> list:
        try:
            return Scan.query.order_by(Scan.created_at.desc()).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get scan history: {e}")
            return []

    def get_dependencies(self, scan_id: str) -> list:
        try:
            return Dependency.query.filter_by(scan_id=scan_id).all()
        except Exception as e:
            logger.error(f"Failed to get dependencies for scan {scan_id}: {e}")
            return []

    def get_vulnerabilities(self, scan_id: str) -> list:
        try:
            return Vulnerability.query.join(Dependency).filter(Dependency.scan_id == scan_id).all()
        except Exception as e:
            logger.error(f"Failed to get vulnerabilities for scan {scan_id}: {e}")
            return []

    def delete_scan(self, scan_id: str) -> bool:
        try:
            scan = db.session.get(Scan, scan_id)
            if scan:
                db.session.delete(scan)
                db.session.commit()
                logger.info(f"Deleted scan {scan_id}")
                return True
            return False
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete scan {scan_id}: {e}")
            return False
