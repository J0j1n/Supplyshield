"""
Module 1 — Secure Scan Manager: Upload & ZIP Validators

Provides security-focused validation for uploaded files and ZIP archives.
Prevents zip bombs, path traversal attacks, and invalid uploads.
"""
import os
import zipfile
import logging

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'zip'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_ZIP_ENTRIES = 10000
MAX_UNCOMPRESSED_SIZE = 500 * 1024 * 1024  # 500 MB (zip bomb protection)
MAX_COMPRESSION_RATIO = 100  # If ratio > 100x, likely a zip bomb

def allowed_file(filename: str) -> bool:
    if not filename:
        return False
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def validate_file_size(file, max_size: int = MAX_FILE_SIZE) -> tuple[bool, str]:
    try:
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size > max_size:
            return False, f"File size exceeds maximum allowed size of {max_size} bytes."
        return True, ""
    except Exception as e:
        logger.error(f"Error validating file size: {e}")
        return False, "Could not validate file size."

def validate_zip_contents(zip_path: str) -> dict:
    result = {
        'valid': True,
        'errors': [],
        'entry_count': 0,
        'total_size': 0
    }
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            infolist = z.infolist()
            result['entry_count'] = len(infolist)
            
            if result['entry_count'] > MAX_ZIP_ENTRIES:
                result['valid'] = False
                result['errors'].append(f"Too many entries in ZIP file: {result['entry_count']} > {MAX_ZIP_ENTRIES}")
            
            for info in infolist:
                result['total_size'] += info.file_size
                
                # Path traversal check
                if '..' in info.filename or info.filename.startswith('/') or info.filename.startswith('\\'):
                    result['valid'] = False
                    result['errors'].append(f"Path traversal detected in entry: {info.filename}")
            
            if result['total_size'] > MAX_UNCOMPRESSED_SIZE:
                result['valid'] = False
                result['errors'].append(f"Uncompressed size exceeds maximum: {result['total_size']} > {MAX_UNCOMPRESSED_SIZE}")
                
            compressed_size = os.path.getsize(zip_path)
            if compressed_size > 0:
                ratio = result['total_size'] / compressed_size
                if ratio > MAX_COMPRESSION_RATIO:
                    result['valid'] = False
                    result['errors'].append(f"Compression ratio too high (possible zip bomb): {ratio:.2f} > {MAX_COMPRESSION_RATIO}")
                    
    except zipfile.BadZipFile:
        result['valid'] = False
        result['errors'].append("Invalid ZIP file format.")
    except Exception as e:
        logger.error(f"Error validating ZIP contents: {e}")
        result['valid'] = False
        result['errors'].append("Error reading ZIP file.")
        
    return result

def detect_path_traversal(zip_path: str) -> bool:
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            for name in z.namelist():
                if '..' in name or name.startswith('/') or name.startswith('\\'):
                    return True
    except Exception as e:
        logger.error(f"Error checking for path traversal: {e}")
        return True # Fail secure
    return False
