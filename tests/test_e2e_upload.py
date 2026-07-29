"""End-to-end test for Module 1 (Secure Scan Manager) + Module 2 (Workspace) pipeline."""
import zipfile
import os
import json
import sys

def run_tests():
    # Create a test ZIP with a requirements.txt
    test_dir = os.path.join('tests', 'fixtures')
    os.makedirs(test_dir, exist_ok=True)
    zip_path = os.path.join(test_dir, 'test_project.zip')

    with zipfile.ZipFile(zip_path, 'w') as z:
        z.writestr('requirements.txt', 'flask==3.0.0\nrequests==2.31.0\nnumpy==1.24.0\n')
        z.writestr('setup.py', 'from setuptools import setup\nsetup(name="testproject")\n')
        z.writestr('src/main.py', 'print("hello")\n')

    print(f'Test ZIP created at {zip_path}')
    print(f'Size: {os.path.getsize(zip_path)} bytes')

    # Test the full pipeline using Flask test client
    from app import create_app
    app = create_app('testing')

    with app.test_client() as client:
        # Test 1: GET upload page
        resp = client.get('/scan/upload')
        print(f'\n[TEST 1] GET /scan/upload -> {resp.status_code}')
        assert resp.status_code == 200, f'Expected 200, got {resp.status_code}'
        print('  PASSED: Upload page renders')

        # Test 2: POST upload with valid ZIP
        with open(zip_path, 'rb') as f:
            resp = client.post('/scan/upload', data={
                'file': (f, 'test_project.zip'),
                'project_name': 'TestProject'
            }, content_type='multipart/form-data', follow_redirects=False)
        print(f'\n[TEST 2] POST /scan/upload -> {resp.status_code}')
        assert resp.status_code == 302, f'Expected 302 redirect, got {resp.status_code}'
        redirect_url = resp.headers.get('Location', '')
        print(f'  Redirects to: {redirect_url}')
        scan_id = redirect_url.split('/')[-1]
        print(f'  Scan ID: {scan_id}')
        print('  PASSED: Upload + redirect works')

        # Test 3: GET scan status page
        resp = client.get(f'/scan/status/{scan_id}')
        print(f'\n[TEST 3] GET /scan/status/{scan_id} -> {resp.status_code}')
        assert resp.status_code == 200
        print('  PASSED: Status page renders')

        # Test 4: GET scan status as JSON
        resp = client.get(f'/scan/status/{scan_id}', headers={'Accept': 'application/json'})
        data = json.loads(resp.data)
        print(f'\n[TEST 4] GET /scan/status (JSON) -> {resp.status_code}')
        print(f'  Status: {data["status"]}')
        print(f'  Project: {data["project_name"]}')
        assert data['found'] == True
        assert data['status'] == 'completed'
        assert data['project_name'] == 'TestProject'
        print('  PASSED: Status JSON correct')

        # Test 5: GET scan results
        resp = client.get(f'/scan/results/{scan_id}')
        data = json.loads(resp.data)
        print(f'\n[TEST 5] GET /scan/results/{scan_id} -> {resp.status_code}')
        print(f'  Found: {data["found"]}')
        print(f'  Workspace exists: {data["workspace_exists"]}')
        print(f'  Files: {len(data["files"])} items')
        for item in data['files']:
            kind = "DIR " if item["is_dir"] else "FILE"
            print(f'    {kind}: {item["path"]} ({item["size"]} bytes)')
        assert data['found'] == True
        assert data['workspace_exists'] == True
        assert len(data['files']) > 0
        print('  PASSED: Results show extracted files')

        # Test 6: POST cleanup
        resp = client.post(f'/scan/cleanup/{scan_id}', follow_redirects=False)
        print(f'\n[TEST 6] POST /scan/cleanup/{scan_id} -> {resp.status_code}')
        assert resp.status_code == 302
        print('  PASSED: Cleanup triggered')

        # Test 7: Verify workspace deleted after cleanup
        resp = client.get(f'/scan/results/{scan_id}')
        data = json.loads(resp.data)
        print(f'\n[TEST 7] Verify cleanup -> workspace_exists: {data["workspace_exists"]}')
        assert data['workspace_exists'] == False
        print('  PASSED: Workspace deleted (zero source code retention confirmed)')

    # Test 8: Validator edge cases
    from app.core.scan_manager.validators import allowed_file, detect_path_traversal
    print(f'\n[TEST 8] Validator edge cases')
    assert allowed_file('test.zip') == True
    assert allowed_file('test.exe') == False
    assert allowed_file('') == False
    assert allowed_file(None) == False
    assert allowed_file('noextension') == False
    print('  PASSED: Validators handle edge cases')

    print('\n' + '=' * 55)
    print('  ALL 8 TESTS PASSED')
    print('  M1 (Scan Manager) + M2 (Workspace) +')
    print('  M8 (Metadata Repo) + M9 (Cleanup) WORKING')
    print('=' * 55)

if __name__ == '__main__':
    run_tests()
