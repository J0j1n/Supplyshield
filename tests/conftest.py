import pytest
import os
import tempfile
import zipfile
from app import create_app
from collections import namedtuple

# Dummy object for dependencies
DependencyInfo = namedtuple('DependencyInfo', ['name', 'version', 'ecosystem', 'type'])

@pytest.fixture
def app():
    app = create_app('TestingConfig')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db_session(app):
    # TODO: create tables, yield session, drop tables
    with app.app_context():
        yield None

@pytest.fixture
def sample_zip():
    # Create a temporary valid ZIP file with a requirements.txt inside
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('requirements.txt', 'flask==3.0.0\nrequests==2.31.0\n')
        
    yield path
    os.remove(path)

@pytest.fixture
def sample_dependencies():
    return [
        DependencyInfo(name='flask', version='3.0.0', ecosystem='pypi', type='direct'),
        DependencyInfo(name='requests', version='2.31.0', ecosystem='pypi', type='direct')
    ]
