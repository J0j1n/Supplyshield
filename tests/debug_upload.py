"""Debug script for upload pipeline."""
import zipfile
import os
import sys

sys.path.insert(0, '.')

# Create test ZIP
test_dir = os.path.join('tests', 'fixtures')
os.makedirs(test_dir, exist_ok=True)
zip_path = os.path.join(test_dir, 'test_project.zip')
with zipfile.ZipFile(zip_path, 'w') as z:
    z.writestr('requirements.txt', 'flask==3.0.0\nrequests==2.31.0\n')

from app import create_app
app = create_app('testing')
app.config['TESTING'] = True

with app.test_client() as client:
    # Attempt upload
    with open(zip_path, 'rb') as f:
        resp = client.post('/scan/upload', data={
            'file': (f, 'test_project.zip'),
            'project_name': 'TestProject'
        }, content_type='multipart/form-data', follow_redirects=False)

    print(f'Response status: {resp.status_code}')
    print(f'Location header: {resp.headers.get("Location", "N/A")}')

    # Now test the service directly
    print('\n--- Direct Service Test ---')
    from app.core.scan_manager.service import ScanService

    with app.app_context():
        svc = ScanService(
            upload_folder=app.config['UPLOAD_FOLDER'],
            workspace_folder=app.config['WORKSPACE_FOLDER']
        )

        # Open file manually
        from io import BytesIO
        with open(zip_path, 'rb') as f:
            data = f.read()

        from werkzeug.datastructures import FileStorage
        file_storage = FileStorage(
            stream=BytesIO(data),
            filename='test_project.zip',
            content_type='application/zip'
        )

        result = svc.initiate_scan(file_storage, 'TestProject')
        print(f'Result: {result}')
