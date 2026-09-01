"""
Module 7 — Risk Dashboard: Routes

Serves the dashboard views for scan history, scan details,
dependency graphs, and JSON APIs.
"""
import json
import logging
from flask import render_template, jsonify, request
from app.core.dashboard import dashboard_bp
from app.core.metadata_repo.repository import MetadataRepository
from app.core.graph_engine import GraphBuilder

logger = logging.getLogger(__name__)
repo = MetadataRepository()
graph_builder = GraphBuilder()

@dashboard_bp.route('/')
def index():
    scans = repo.get_scan_history(limit=50)
    return render_template('dashboard/index.html', scans=scans)

@dashboard_bp.route('/scan/<scan_id>')
def scan_details(scan_id):
    scan = repo.get_scan(scan_id)
    if not scan:
        return "Scan not found", 404
        
    dependencies = repo.get_dependencies(scan_id)
    vulnerabilities = repo.get_vulnerabilities(scan_id)
    
    # Group vulnerabilities by dependency ID
    vulns_by_dep = {}
    for v in vulnerabilities:
        if v.dependency_id not in vulns_by_dep:
            vulns_by_dep[v.dependency_id] = []
        vulns_by_dep[v.dependency_id].append(v)
        
    # Group dependencies by ecosystem
    ecosystem_counts = {}
    
    # Attach vulnerabilities to dependencies
    for dep in dependencies:
        dep.vulnerabilities = vulns_by_dep.get(dep.id, [])
        dep.vuln_count = len(dep.vulnerabilities)
        
        # Calculate max severity for color coding
        severity_rank = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        max_sev = 0
        max_sev_name = 'none'
        for v in dep.vulnerabilities:
            rank = severity_rank.get(v.severity.lower(), 0)
            if rank > max_sev:
                max_sev = rank
                max_sev_name = v.severity.lower()
        dep.max_severity = max_sev_name
        
        if dep.ecosystem:
            eco = dep.ecosystem.lower()
            ecosystem_counts[eco] = ecosystem_counts.get(eco, 0) + 1
            
    # Sort dependencies by vulnerability count descending
    dependencies.sort(key=lambda d: d.vuln_count, reverse=True)
            
    return render_template('dashboard/scan_details.html', 
                           scan=scan, 
                           dependencies=dependencies,
                           vulnerabilities=vulnerabilities,
                           ecosystem_counts=ecosystem_counts)

@dashboard_bp.route('/scan/<scan_id>/graph')
def scan_graph(scan_id):
    scan = repo.get_scan(scan_id)
    if not scan:
        return "Scan not found", 404
        
    dependencies = repo.get_dependencies(scan_id)
    vulnerabilities = repo.get_vulnerabilities(scan_id)
    
    # Build vulnerability map: dep_name -> {count, max_severity}
    vuln_map = {}
    vulns_by_dep_id = {}
    for v in vulnerabilities:
        if v.dependency_id not in vulns_by_dep_id:
            vulns_by_dep_id[v.dependency_id] = []
        vulns_by_dep_id[v.dependency_id].append(v)
        
    severity_rank = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
    
    deps_list = []
    for dep in dependencies:
        dep_vulns = vulns_by_dep_id.get(dep.id, [])
        if dep_vulns:
            max_sev = 0
            max_sev_name = 'low'
            for v in dep_vulns:
                rank = severity_rank.get(v.severity.lower(), 0)
                if rank > max_sev:
                    max_sev = rank
                    max_sev_name = v.severity.lower()
            vuln_map[dep.name] = {
                'count': len(dep_vulns),
                'max_severity': max_sev_name
            }
            
        deps_list.append({
            'name': dep.name,
            'version': dep.version,
            'ecosystem': dep.ecosystem,
            'is_direct': dep.is_direct
        })
        
    graph_data = graph_builder.build_graph(deps_list, scan.project_name)
    d3_json = graph_builder.to_d3_json(graph_data, vuln_map)
    
    return render_template('dashboard/graph.html', 
                           scan=scan, 
                           graph_json=json.dumps(d3_json))

@dashboard_bp.route('/api/scan/<scan_id>/summary')
def scan_summary_api(scan_id):
    scan = repo.get_scan(scan_id)
    if not scan:
        return jsonify({"error": "Scan not found"}), 404
        
    return jsonify({
        "id": scan.id,
        "project_name": scan.project_name,
        "status": scan.scan_status,
        "total_dependencies": scan.total_dependencies,
        "vulnerabilities": {
            "critical": scan.critical_count or 0,
            "high": scan.high_count or 0,
            "medium": scan.medium_count or 0,
            "low": scan.low_count or 0
        },
        "trust_score": scan.trust_score,
        "trust_level": scan.trust_level
    })
