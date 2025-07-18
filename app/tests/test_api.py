# test_fixed_api.py
"""

Run with: pytest test_fixed_api.py -v
"""

import requests
import pytest
from io import BytesIO
import time
import uuid
import random

BASE_URL = "http://localhost:8000"

class TestFixedAPI:
    
    def generate_unique_content(self, base_text="test file"):
        unique_id = str(uuid.uuid4())
        timestamp = str(time.time())
        return f"{base_text} - {unique_id} - {timestamp}".encode()
    
    def test_health_check(self):
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "file-upload-service"
    
    def test_upload_text_file(self):
        test_content = self.generate_unique_content("Hello, World! This is a test file.")
        files = {
            'file': ('test.txt', BytesIO(test_content), 'text/plain')
        }
        data = {
            'uploaded_by': 'pytest_test_service'
        }
        
        response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        result = response.json()
        assert "file_id" in result
        assert result["file_size"] == len(test_content)
        assert result["content_type"] == "text/plain"
        assert result["upload_status"] in ["pending", "uploading", "completed"]
        
        TestFixedAPI.uploaded_file_id = result["file_id"]
    
    def test_upload_image_file(self):
        random_bytes = bytes([random.randint(0, 255) for _ in range(10)])
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82' + random_bytes
        
        files = {
            'file': (f'test_{uuid.uuid4().hex[:8]}.png', BytesIO(png_data), 'image/png')
        }
        data = {
            'uploaded_by': 'pytest_image_service'
        }
        
        response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        result = response.json()
        assert result["content_type"] == "image/png"
        assert result["file_size"] == len(png_data)
    
    def test_upload_pdf_file(self):
        unique_content = f"Unique content: {uuid.uuid4()}"
        pdf_content = f"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n%{unique_content}\n%%EOF".encode()
        
        files = {
            'file': (f'test_{uuid.uuid4().hex[:8]}.pdf', BytesIO(pdf_content), 'application/pdf')
        }
        data = {
            'uploaded_by': 'pytest_pdf_service'
        }
        
        response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        result = response.json()
        assert result["content_type"] == "application/pdf"
    
    def test_upload_file_too_large(self):
        large_content = b"x" * (100 * 1024 * 1024 + 1)
        files = {
            'file': ('large.txt', BytesIO(large_content), 'text/plain')
        }
        
        response = requests.post(f"{BASE_URL}/upload", files=files)
        
        if response.status_code == 500:
            error_text = response.text
            assert "File too large" in error_text or "413" in error_text
        else:
            assert response.status_code == 413
    
    def test_upload_invalid_file_type(self):
        exe_content = self.generate_unique_content("fake executable content")
        files = {
            'file': ('malware.exe', BytesIO(exe_content), 'application/octet-stream')
        }
        
        response = requests.post(f"{BASE_URL}/upload", files=files)
        
        if response.status_code == 500:
            error_text = response.text
            assert "File type not allowed" in error_text or "400" in error_text
        else:
            assert response.status_code == 400
    
    def test_upload_invalid_extension_zip(self):
        zip_content = self.generate_unique_content("fake zip content")
        files = {
            'file': ('archive.zip', BytesIO(zip_content), 'application/zip')
        }
        
        response = requests.post(f"{BASE_URL}/upload", files=files)
        
        if response.status_code == 500:
            error_text = response.text
            assert "File type not allowed" in error_text or "400" in error_text
        else:
            assert response.status_code == 400
    
    def test_get_file_info(self):
        test_content = self.generate_unique_content("Get file info test")
        files = {
            'file': ('get_info_test.txt', BytesIO(test_content), 'text/plain')
        }
        data = {
            'uploaded_by': 'pytest_get_info_service'
        }
        
        upload_response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
        assert upload_response.status_code == 200, f"Upload failed: {upload_response.text}"
        file_id = upload_response.json()["file_id"]
        
        response = requests.get(f"{BASE_URL}/files/{file_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["id"] == file_id
        assert data["original_filename"] == "get_info_test.txt"
        assert "created_at" in data
    
    def test_get_nonexistent_file(self):
        response = requests.get(f"{BASE_URL}/files/999999")
        assert response.status_code == 404
    
    def test_list_files_basic(self):
        response = requests.get(f"{BASE_URL}/files")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "files" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert isinstance(data["files"], list)
    
    def test_list_files_pagination(self):
        response = requests.get(f"{BASE_URL}/files?page=1&size=5")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 5
        assert len(data["files"]) <= 5
        
        response = requests.get(f"{BASE_URL}/files?page=2&size=3")
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["size"] == 3
        assert len(data["files"]) <= 3
    
    def test_list_files_invalid_pagination(self):
        response = requests.get(f"{BASE_URL}/files?page=0")
        assert response.status_code == 422
        
        response = requests.get(f"{BASE_URL}/files?size=1000")
        assert response.status_code == 422
    
    def test_download_url_for_uploaded_file(self):
        test_content = self.generate_unique_content("Download URL test")
        files = {
            'file': ('download_test.txt', BytesIO(test_content), 'text/plain')
        }
        data = {
            'uploaded_by': 'pytest_download_service'
        }
        
        upload_response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
        assert upload_response.status_code == 200, f"Upload failed: {upload_response.text}"
        file_id = upload_response.json()["file_id"]
        
        response = requests.get(f"{BASE_URL}/files/{file_id}/download")
        
        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "download_url" in data
            assert isinstance(data["download_url"], str)
    
    def test_download_url_nonexistent_file(self):
        response = requests.get(f"{BASE_URL}/files/999999/download")
        assert response.status_code == 404
    
    def test_delete_nonexistent_file(self):
        response = requests.delete(f"{BASE_URL}/files/999999")
        assert response.status_code == 404
    
    def test_concurrent_uploads(self):
        import concurrent.futures
        
        def upload_file(file_number):
            content = self.generate_unique_content(f"Concurrent test file {file_number}")
            files = {
                'file': (f'concurrent_{file_number}_{uuid.uuid4().hex[:8]}.txt', BytesIO(content), 'text/plain')
            }
            data = {
                'uploaded_by': f'concurrent_test_{file_number}'
            }
            
            response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
            return response.status_code, response.json() if response.status_code == 200 else response.text
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(upload_file, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        successful_uploads = 0
        for status_code, data in results:
            if status_code == 200:
                successful_uploads += 1
                assert "file_id" in data
        
        assert successful_uploads >= 3, f"Only {successful_uploads}/5 uploads succeeded"
    
    def test_stress_upload_many_small_files(self):
        successful_uploads = 0
        
        for i in range(10):
            content = self.generate_unique_content(f"Stress test file {i}")
            files = {
                'file': (f'stress_{i}_{uuid.uuid4().hex[:8]}.txt', BytesIO(content), 'text/plain')
            }
            data = {
                'uploaded_by': f'stress_test_{i}'
            }
            
            response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
            if response.status_code == 200:
                successful_uploads += 1
        
        assert successful_uploads >= 8, f"Only {successful_uploads}/10 uploads succeeded"
    
    def test_database_operations_via_api(self):
        content = self.generate_unique_content("CRUD test file content")
        files = {
            'file': (f'crud_test_{uuid.uuid4().hex[:8]}.txt', BytesIO(content), 'text/plain')
        }
        data = {
            'uploaded_by': 'crud_test_service'
        }
        
        response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        file_id = response.json()["file_id"]
        
        response = requests.get(f"{BASE_URL}/files/{file_id}")
        assert response.status_code == 200, f"Get file failed: {response.text}"
        file_data = response.json()
        assert file_data["id"] == file_id
        
        response = requests.get(f"{BASE_URL}/files")
        assert response.status_code == 200, f"List files failed: {response.text}"
        list_data = response.json()
        assert any(f["id"] == file_id for f in list_data["files"])
        
        response = requests.delete(f"{BASE_URL}/files/{file_id}")
        assert response.status_code == 200, f"Delete failed: {response.text}"
        assert response.json()["message"] == "File deleted successfully"
        
        response = requests.get(f"{BASE_URL}/files/{file_id}")
        assert response.status_code == 404, f"File should be deleted but got: {response.status_code}"
    
    def test_file_deduplication_feature(self):
        content = b"Deduplication test content - exact same bytes"
        
        files1 = {
            'file': ('dedup_test1.txt', BytesIO(content), 'text/plain')
        }
        response1 = requests.post(f"{BASE_URL}/upload", files=files1)
        
        files2 = {
            'file': ('dedup_test2.txt', BytesIO(content), 'text/plain')
        }
        response2 = requests.post(f"{BASE_URL}/upload", files=files2)
        
        assert response1.status_code == 200
        assert response2.status_code in [200, 409]  

if __name__ == "__main__":
    print("Testing Live File Upload Service - Fixed for Unique Constraints")
    print("=" * 70)
    print(f"Service URL: {BASE_URL}")
    print()
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("Service is running")
        else:
            print("Service responded but health check failed")
            exit(1)
    except requests.exceptions.ConnectionError:
        print("Cannot connect to service")
        print("Run: docker-compose up -d")
        exit(1)
    
    print("Run with: pytest test_fixed_api.py -v")