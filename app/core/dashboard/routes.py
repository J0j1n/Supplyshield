"""
Module 7 — Risk Dashboard: Routes

Handles HTTP endpoints for the security dashboard, scan details,
SBOM viewer, dependency graph, security report, and scan history.
"""
import os
import json
import logging
from flask import render_template, jsonify, current_app, send_file, abort
from app.core.dashboard import dashboard_bp
from app.core.metadata_repo.repository import MetadataRepository
from app.core.graph_engine.builder import GraphBuilder
from app.core.vulnerability import VulnerabilityAnalyzer
from app.core.dashboard.report import generate_security_report

logger = logging.getLogger(__name__)


def _get_repo():
    return MetadataRepository()


@dashboard_bp.route('/')
def index():
    """Dashboard home — shows recent scans overview."""
    repo = _get_repo()
    scans = repo.get_scan_history(limit=50)

    # Compute risk level for each scan
    for scan in scans:
        severity = {
            'critical': scan.critical_count or 0,
            'high': scan.high_count or 0,
            'medium': scan.medium_count or 0,
            'low': scan.low_count or 0
        }
        scan.risk_level = VulnerabilityAnalyzer.get_risk_level(severity)
        total = severity['critical'] + severity['high'] + severity['medium'] + severity['low']
        scan.total_vulnerabilities = total

    return render_template('dashboard/index.html', scans=scans)


@dashboard_bp.route('/history')
def history():
    """Dedicated Scan History page."""
    repo = _get_repo()
    scans = repo.get_scan_history(limit=100)

    for scan in scans:
        severity = {
            'critical': scan.critical_count or 0,
            'high': scan.high_count or 0,
            'medium': scan.medium_count or 0,
            'low': scan.low_count or 0
        }
        scan.risk_level = VulnerabilityAnalyzer.get_risk_level(severity)
        total = severity['critical'] + severity['high'] + severity['medium'] + severity['low']
        scan.total_vulnerabilities = total

    return render_template('dashboard/scan_history.html', scans=scans)


@dashboard_bp.route('/scan/<scan_id>')
def scan_details(scan_id):
    """Detailed scan results page."""
    repo = _get_repo()
    scan = repo.get_scan(scan_id)

    if not scan:
        abort(404)

    dependencies = repo.get_dependencies(scan_id)
    vulnerabilities = repo.get_vulnerabilities(scan_id)

    # Compute risk level
    severity = {
        'critical': scan.critical_count or 0,
        'high': scan.high_count or 0,
        'medium': scan.medium_count or 0,
        'low': scan.low_count or 0
    }
    risk_level = VulnerabilityAnalyzer.get_risk_level(severity)
    total_vulns = severity['critical'] + severity['high'] + severity['medium'] + severity['low']

    # Scan duration
    scan_duration = None
    if scan.created_at and scan.completed_at:
        delta = scan.completed_at - scan.created_at
        scan_duration = round(delta.total_seconds(), 1)

    # Determine ecosystem from dependencies
    ecosystem_counts = {}
    for dep in dependencies:
        eco = dep.ecosystem or 'unknown'
        ecosystem_counts[eco] = ecosystem_counts.get(eco, 0) + 1
    primary_ecosystem = max(ecosystem_counts, key=ecosystem_counts.get) if ecosystem_counts else None

    # Enrich dependencies with vuln data for template
    vuln_by_dep = {}
    for v in vulnerabilities:
        vuln_by_dep.setdefault(v.dependency_id, []).append(v)

    for dep in dependencies:
        dep_vulns = vuln_by_dep.get(dep.id, [])
        dep.vuln_count = len(dep_vulns)
        dep.vulnerabilities = dep_vulns
        if dep_vulns:
            severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            dep.max_severity = min(
                (v.severity for v in dep_vulns if v.severity),
                key=lambda s: severity_order.get(s, 4),
                default='none'
            )
        else:
            dep.max_severity = 'none'

    # Sort: vulnerable deps first, then by severity
    severity_rank = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'none': 4}
    dependencies.sort(key=lambda d: (severity_rank.get(d.max_severity, 4), -d.vuln_count))

    # SBOM component count from actual SBOM file
    sbom_component_count = 0
    sbom_results = [r for r in scan.results if r.result_type == 'sbom' and r.format == 'cyclonedx']
    if sbom_results and os.path.exists(sbom_results[0].file_path):
        try:
            with open(sbom_results[0].file_path, 'r') as f:
                sbom_data = json.load(f)
            sbom_component_count = len(sbom_data.get('components', []))
        except Exception:
            sbom_component_count = scan.total_dependencies or 0

    return render_template(
        'dashboard/scan_details.html',
        scan=scan,
        dependencies=dependencies,
        vulnerabilities=vulnerabilities,
        risk_level=risk_level,
        total_vulns=total_vulns,
        scan_duration=scan_duration,
        primary_ecosystem=primary_ecosystem,
        ecosystem_counts=ecosystem_counts,
        sbom_component_count=sbom_component_count
    )


@dashboard_bp.route('/scan/<scan_id>/graph')
def scan_graph(scan_id):
    """Dependency graph visualization page."""
    repo = _get_repo()
    scan = repo.get_scan(scan_id)

    if not scan:
        abort(404)

    dependencies = repo.get_dependencies(scan_id)
    vulnerabilities = repo.get_vulnerabilities(scan_id)

    # Build vulnerability map
    vuln_by_dep = {}
    for v in vulnerabilities:
        vuln_by_dep.setdefault(v.dependency_id, []).append(v)

    vuln_map = {}
    for dep in dependencies:
        dep_vulns = vuln_by_dep.get(dep.id, [])
        if dep_vulns:
            severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            max_sev = min(
                (v.severity for v in dep_vulns if v.severity),
                key=lambda s: severity_order.get(s, 4),
                default='none'
            )
            vuln_map[dep.name] = {
                'count': len(dep_vulns),
                'max_severity': max_sev
            }

    dep_dicts = [
        {
            'name': d.name,
            'version': d.version or '',
            'ecosystem': d.ecosystem or 'unknown',
            'is_direct': d.is_direct
        }
        for d in dependencies
    ]

    builder = GraphBuilder()
    graph = builder.build_graph(dep_dicts, scan.project_name)
    graph_json = json.dumps(builder.to_d3_json(graph, vuln_map))

    return render_template(
        'dashboard/graph.html',
        scan=scan,
        graph_json=graph_json
    )


@dashboard_bp.route('/scan/<scan_id>/sbom')
def sbom_viewer(scan_id):
    """SBOM detail viewer page."""
    repo = _get_repo()
    scan = repo.get_scan(scan_id)

    if not scan:
        abort(404)

    sbom_data = None
    sbom_format = None
    sbom_results = [r for r in scan.results if r.result_type == 'sbom']

    # Prefer CycloneDX
    cdx_results = [r for r in sbom_results if r.format == 'cyclonedx']
    if cdx_results and os.path.exists(cdx_results[0].file_path):
        try:
            with open(cdx_results[0].file_path, 'r') as f:
                sbom_data = json.load(f)
            sbom_format = 'CycloneDX'
        except Exception as e:
            logger.error(f"Failed to load SBOM: {e}")

    return render_template(
        'dashboard/sbom_viewer.html',
        scan=scan,
        sbom_data=sbom_data,
        sbom_format=sbom_format
    )


@dashboard_bp.route('/scan/<scan_id>/report')
def download_report(scan_id):
    """Download security report as JSON."""
    repo = _get_repo()
    scan = repo.get_scan(scan_id)

    if not scan:
        abort(404)

    dependencies = repo.get_dependencies(scan_id)
    vulnerabilities = repo.get_vulnerabilities(scan_id)

    # Load SBOM data if available
    sbom_data = None
    sbom_results = [r for r in scan.results if r.result_type == 'sbom' and r.format == 'cyclonedx']
    if sbom_results and os.path.exists(sbom_results[0].file_path):
        try:
            with open(sbom_results[0].file_path, 'r') as f:
                sbom_data = json.load(f)
        except Exception:
            pass

    report = generate_security_report(scan, dependencies, vulnerabilities, sbom_data)

    response = jsonify(report)
    response.headers['Content-Disposition'] = \
        f'attachment; filename=supplyshield_report_{scan_id[:8]}.json'
    return response


@dashboard_bp.route('/api/sbom/<scan_id>')
def download_sbom(scan_id):
    """Download raw SBOM JSON file."""
    repo = _get_repo()
    scan = repo.get_scan(scan_id)

    if not scan:
        abort(404)

    sbom_results = [r for r in scan.results if r.result_type == 'sbom' and r.format == 'cyclonedx']
    if not sbom_results or not os.path.exists(sbom_results[0].file_path):
        abort(404)

    return send_file(
        sbom_results[0].file_path,
        as_attachment=True,
        download_name=f'sbom_{scan.project_name}_{scan_id[:8]}.json',
        mimetype='application/json'
    )


@dashboard_bp.route('/api/scan/<scan_id>/summary')
def scan_summary_api(scan_id):
    """JSON API for scan summary data."""
    repo = _get_repo()
    scan = repo.get_scan(scan_id)

    if not scan:
        return jsonify({'error': 'Scan not found'}), 404

    severity = {
        'critical': scan.critical_count or 0,
        'high': scan.high_count or 0,
        'medium': scan.medium_count or 0,
        'low': scan.low_count or 0
    }

    return jsonify({
        'scan_id': scan.id,
        'project_name': scan.project_name,
        'status': scan.scan_status,
        'risk_level': VulnerabilityAnalyzer.get_risk_level(severity),
        'total_dependencies': scan.total_dependencies,
        'severity_summary': severity,
        'sbom_generated': scan.sbom_generated,
        'cleanup_completed': scan.cleanup_completed
    })
