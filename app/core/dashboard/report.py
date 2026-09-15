"""
Security Report Generator

Generates structured JSON security reports from actual scan data.
All data comes from the database — nothing is fabricated.
"""
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_security_report(scan, dependencies, vulnerabilities, sbom_data=None):
    """
    Generate a complete security report dictionary from real scan data.
    
    Args:
        scan: Scan model object
        dependencies: list of Dependency model objects
        vulnerabilities: list of Vulnerability model objects
        sbom_data: optional parsed SBOM dict
    
    Returns:
        dict with the full report structure
    """
    total_vulns = (scan.critical_count or 0) + (scan.high_count or 0) + \
                  (scan.medium_count or 0) + (scan.low_count or 0)

    # Determine risk level
    if (scan.critical_count or 0) > 0:
        risk_level = 'CRITICAL'
    elif (scan.high_count or 0) > 0:
        risk_level = 'HIGH'
    elif (scan.medium_count or 0) > 0:
        risk_level = 'MODERATE'
    elif (scan.low_count or 0) > 0:
        risk_level = 'LOW'
    else:
        risk_level = 'NONE'

    # Scan duration
    duration = None
    if scan.created_at and scan.completed_at:
        delta = scan.completed_at - scan.created_at
        duration = round(delta.total_seconds(), 1)

    # Build dependency findings
    dep_findings = []
    for dep in dependencies:
        dep_vulns = [v for v in vulnerabilities if v.dependency_id == dep.id]
        finding = {
            'name': dep.name,
            'version': dep.version,
            'ecosystem': dep.ecosystem,
            'type': 'Direct' if dep.is_direct else 'Transitive',
            'license': dep.license,
            'vulnerability_count': len(dep_vulns),
            'security_status': 'Vulnerable' if dep_vulns else 'Clean',
            'vulnerabilities': []
        }
        for v in dep_vulns:
            vuln_entry = {
                'id': v.cve_id,
                'severity': v.severity,
                'cvss_score': v.cvss_score,
                'description': v.description,
                'affected_versions': v.affected_versions,
                'fixed_version': v.fixed_version if v.fixed_version else 'Not available',
                'source': v.source or 'osv',
                'recommendation': _get_recommendation(dep, v)
            }
            finding['vulnerabilities'].append(vuln_entry)
        dep_findings.append(finding)

    # SBOM summary
    sbom_summary = {
        'generated': scan.sbom_generated or False,
        'format': 'CycloneDX' if scan.sbom_generated else None,
        'component_count': len(sbom_data.get('components', [])) if sbom_data else scan.total_dependencies or 0
    }

    report = {
        'report_metadata': {
            'title': 'SupplyShield Security Report',
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'generator': 'SupplyShield v0.1.0',
            'report_version': '1.0'
        },
        'project_information': {
            'name': scan.project_name,
            'source_type': scan.source_type
        },
        'scan_information': {
            'scan_id': scan.id,
            'status': scan.scan_status,
            'started_at': scan.created_at.isoformat() if scan.created_at else None,
            'completed_at': scan.completed_at.isoformat() if scan.completed_at else None,
            'duration_seconds': duration
        },
        'security_risk_overview': {
            'risk_level': risk_level,
            'total_vulnerabilities': total_vulns,
            'severity_breakdown': {
                'critical': scan.critical_count or 0,
                'high': scan.high_count or 0,
                'medium': scan.medium_count or 0,
                'low': scan.low_count or 0
            }
        },
        'dependency_summary': {
            'total_dependencies': scan.total_dependencies or 0,
            'vulnerable_count': sum(1 for f in dep_findings if f['security_status'] == 'Vulnerable'),
            'clean_count': sum(1 for f in dep_findings if f['security_status'] == 'Clean')
        },
        'sbom_summary': sbom_summary,
        'dependency_findings': dep_findings,
        'privacy_status': {
            'source_code_deleted': scan.cleanup_completed or False,
            'metadata_retained': True,
            'workspace_type': 'Temporary'
        }
    }

    return report


def _get_recommendation(dep, vuln):
    """Generate a factual recommendation based on available data."""
    if vuln.fixed_version:
        return f"Upgrade {dep.name} from {dep.version} to {vuln.fixed_version} or later."
    else:
        return f"Upgrade {dep.name} to a non-affected version when a fixed release is available."
