import pytest

class TestScanManager:
    def test_upload_valid_zip(self, client, sample_zip):
        # TODO: POST /scan/upload with valid zip, assert 200 or redirect
        pass

    def test_upload_invalid_file(self, client):
        # TODO: POST with .exe, assert 400
        pass

    def test_upload_no_file(self, client):
        # TODO: POST with no file, assert 400
        pass

    def test_scan_status(self, client):
        # TODO: GET /scan/status/<id>, assert response
        pass
