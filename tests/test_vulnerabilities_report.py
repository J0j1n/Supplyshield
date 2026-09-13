import os
import zipfile
import json
import sys

sys.path.insert(0, '.')

from app import create_app
from app.core.scan_manager.service import ScanService
from app.extensions import db
from app.models.scan import Scan, Dependency, Vulnerability
from werkzeug.datastructures import FileStorage
from io import BytesIO

def create_zip(path, files):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, 'w') as z:
        for filename, content in files.items():
            z.writestr(filename, content)

def run_tests():
    app = create_app('testing')
    app.config['TESTING'] = True
    
    with app.app_context():
        # Ensure clean db for testing
        db.create_all()
        
        svc = ScanService(
            upload_folder=app.config['UPLOAD_FOLDER'],
            workspace_folder=app.config['WORKSPACE_FOLDER'],
            results_folder=app.config['RESULTS_FOLDER']
        )
        
        test_cases = [
            {
                'name': 'No Dependencies Project',
                'files': {
                    'main.py': 'print("Hello World!")\n'
                }
            },
            {
                'name': 'Up-to-date Project',
                'files': {
                    'requirements.txt': 'flask==3.0.0\nrequests==2.31.0\npydantic==2.8.2\n',
                    'main.py': 'import flask\n'
                }
            },
            {
                'name': 'Highly Vulnerable Project',
                'files': {
                    'requirements.txt': 'django==1.11\nrequests==2.0.0\nurllib3==1.24\nflask==0.12\n',
                    'main.py': 'import django\n'
                }
            }
        ]
        
        results_summary = []
        
        for case in test_cases:
            print(f"Testing: {case['name']}")
            zip_path = f"tests/fixtures/{case['name'].replace(' ', '_').lower()}.zip"
            create_zip(zip_path, case['files'])
            
            with open(zip_path, 'rb') as f:
                data = f.read()
                
            file_storage = FileStorage(
                stream=BytesIO(data),
                filename=os.path.basename(zip_path),
                content_type='application/zip'
            )
            
            result = svc.initiate_scan(file_storage, case['name'])
            scan_id = result.get('scan_id')
            
            if not scan_id:
                print(f"Failed to scan {case['name']}: {result}")
                continue
                
            scan_record = Scan.query.get(scan_id)
            deps = Dependency.query.filter_by(scan_id=scan_id).all()
            
            dep_info = []
            for d in deps:
                vulns = Vulnerability.query.filter_by(dependency_id=d.id).all()
                dep_info.append({
                    'name': d.name,
                    'version': d.version,
                    'vulnerability_count': len(vulns),
                    'vulnerabilities': [{'cve': v.cve_id, 'severity': v.severity} for v in vulns]
                })
                
            results_summary.append({
                'project_name': case['name'],
                'dependencies_found': scan_record.total_dependencies,
                'critical_vulns': scan_record.critical_count,
                'high_vulns': scan_record.high_count,
                'medium_vulns': scan_record.medium_count,
                'low_vulns': scan_record.low_count,
                'dependency_details': dep_info
            })
            
            # Clean up the scan
            svc.cleanup_scan(scan_id)
            
        with open('test_report.json', 'w') as f:
            json.dump(results_summary, f, indent=2)
            
        print("\nTesting complete. Report generated at test_report.json")

if __name__ == '__main__':
    run_tests()
