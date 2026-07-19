import uuid
from datetime import datetime
from app.extensions import db

class Scan(db.Model):
    """Model for a source code/dependency scan."""
    __tablename__ = 'scans'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_name = db.Column(db.String(255), nullable=False)
    scan_status = db.Column(db.String(20), default='pending') # 'pending', 'scanning', 'completed', 'failed', 'cleanup'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    source_type = db.Column(db.String(20), nullable=True) # 'zip', 'git'
    total_dependencies = db.Column(db.Integer, default=0)
    critical_count = db.Column(db.Integer, default=0)
    high_count = db.Column(db.Integer, default=0)
    medium_count = db.Column(db.Integer, default=0)
    low_count = db.Column(db.Integer, default=0)
    trust_score = db.Column(db.Float, nullable=True) # Phase 2
    trust_level = db.Column(db.String(20), nullable=True) # Phase 2
    sbom_generated = db.Column(db.Boolean, default=False)
    cleanup_completed = db.Column(db.Boolean, default=False)
    
    # Relationships
    results = db.relationship('ScanResult', backref='scan', lazy=True, cascade='all, delete-orphan')
    dependencies = db.relationship('Dependency', backref='scan', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Scan {self.id} - {self.project_name}>"


class Dependency(db.Model):
    """Model for a project dependency."""
    __tablename__ = 'dependencies'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scan_id = db.Column(db.String(36), db.ForeignKey('scans.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    version = db.Column(db.String(100), nullable=True)
    ecosystem = db.Column(db.String(50), nullable=True) # 'pypi', 'npm', 'maven', 'cargo', 'poetry'
    is_direct = db.Column(db.Boolean, default=True)
    license = db.Column(db.String(100), nullable=True)
    
    # Relationships
    vulnerabilities = db.relationship('Vulnerability', backref='dependency', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Dependency {self.name}=={self.version}>"


class Vulnerability(db.Model):
    """Model for a discovered vulnerability in a dependency."""
    __tablename__ = 'vulnerabilities'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dependency_id = db.Column(db.Integer, db.ForeignKey('dependencies.id'), nullable=False)
    cve_id = db.Column(db.String(50), nullable=True)
    severity = db.Column(db.String(20), nullable=True) # 'critical', 'high', 'medium', 'low'
    cvss_score = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=True)
    affected_versions = db.Column(db.String(255), nullable=True)
    fixed_version = db.Column(db.String(255), nullable=True)
    source = db.Column(db.String(50), nullable=True) # 'nvd', 'github_advisory', 'osv'
    published_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Vulnerability {self.cve_id} ({self.severity})>"


class ScanResult(db.Model):
    """Model for generated artifacts (SBOM, Reports, etc)."""
    __tablename__ = 'scan_results'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scan_id = db.Column(db.String(36), db.ForeignKey('scans.id'), nullable=False)
    result_type = db.Column(db.String(50), nullable=False) # 'sbom', 'report', 'certificate'
    format = db.Column(db.String(20), nullable=False) # 'cyclonedx', 'spdx', 'json', 'pdf'
    file_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ScanResult {self.result_type} ({self.format})>"
