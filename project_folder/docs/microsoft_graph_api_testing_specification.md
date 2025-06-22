# Microsoft Graph API Testing & Validation Specification

## 1. Executive Summary

This document provides comprehensive testing procedures and specifications for Microsoft Graph API endpoints used in the SharePoint Uploader application. It ensures all API interactions are validated to full specification and documented for reliability and maintainability.

## Table of Contents

1. [API Endpoint Specifications](#api-endpoint-specifications)
2. [Authentication & Authorization Testing](#authentication--authorization-testing)
3. [Drive & Site Operations](#drive--site-operations)
4. [Folder Management Operations](#folder-management-operations)
5. [File Upload Operations](#file-upload-operations)
6. [Error Handling & Edge Cases](#error-handling--edge-cases)
7. [Performance & Rate Limiting](#performance--rate-limiting)
8. [Test Automation Framework](#test-automation-framework)
9. [Validation Checklists](#validation-checklists)

---

## API Endpoint Specifications

### Base URLs and Versioning

```
Base URL: https://graph.microsoft.com/v1.0
Beta URL: https://graph.microsoft.com/beta (for preview features)
```

### Supported Endpoints

| Endpoint Category | Base Path | Description |
|------------------|-----------|-------------|
| Sites | `/sites/{site-id}` | Site collection operations |
| Drives | `/drives/{drive-id}` | Drive-specific operations |
| Site Drives | `/sites/{site-id}/drive` | Site's default document library |
| Drive Items | `/drives/{drive-id}/items/{item-id}` | Individual item operations |
| Drive Root | `/drives/{drive-id}/root` | Root folder operations |

---

## Authentication & Authorization Testing

### Test Case AUTH-01: Client Credentials Flow

**Objective**: Validate application-only authentication using client credentials

**Prerequisites**:
- Valid Azure AD application registration
- Client ID, Tenant ID, and Client Secret
- Required permissions granted and admin consent provided

**Test Steps**:

```python
def test_client_credentials_auth():
    """Test client credentials authentication flow"""
    
    # Test data
    auth_config = {
        "client_id": "your-client-id",
        "tenant_id": "your-tenant-id", 
        "client_secret": "your-client-secret",
        "scopes": ["https://graph.microsoft.com/.default"]
    }
    
    # Step 1: Initialize authentication
    auth = GraphAuthentication(**auth_config)
    
    # Step 2: Acquire token
    token = auth.get_token()
    
    # Validation
    assert isinstance(token, str), "Token should be a string"
    assert len(token) > 100, "Token should be substantial length"
    
    # Step 3: Validate token structure (JWT)
    decoded_token = jwt.decode(token, options={"verify_signature": False})
    
    # Required claims validation
    required_claims = ["aud", "iss", "iat", "exp", "app_displayname", "appid"]
    for claim in required_claims:
        assert claim in decoded_token, f"Missing required claim: {claim}"
    
    # Step 4: Validate token expiration
    exp_timestamp = decoded_token["exp"]
    current_timestamp = time.time()
    assert exp_timestamp > current_timestamp, "Token should not be expired"
    
    return token
```

**Expected Results**:
- ✅ Token acquired successfully
- ✅ Token contains required JWT claims
- ✅ Token is not expired
- ✅ Token audience matches Graph API

**Failure Scenarios**:
- ❌ Invalid client credentials → 401 Unauthorized
- ❌ Missing permissions → 403 Forbidden
- ❌ Network issues → Connection timeout

---

### Test Case AUTH-02: Permission Validation

**Objective**: Verify application has required permissions for all operations

**Required Permissions**:

| Permission | Type | Description | Required For |
|------------|------|-------------|--------------|
| `Files.ReadWrite.All` | Application | Read/write files in all site collections | File operations |
| `Sites.ReadWrite.All` | Application | Read/write items in all site collections | Site operations |
| `Sites.Manage.All` | Application | Create, edit, delete items/lists | Advanced operations |

**Test Implementation**:

```python
def test_permission_validation():
    """Validate all required permissions are granted"""
    
    token = get_valid_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    permission_tests = [
        {
            "name": "Files.ReadWrite.All",
            "test_url": f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/root/children",
            "method": "GET",
            "expected_status": [200]
        },
        {
            "name": "Sites.ReadWrite.All", 
            "test_url": f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drive",
            "method": "GET",
            "expected_status": [200]
        }
    ]
    
    for test in permission_tests:
        response = requests.request(test["method"], test["test_url"], headers=headers)
        assert response.status_code in test["expected_status"], \
            f"Permission {test['name']} test failed: {response.status_code}"
```

---

## Drive & Site Operations

### Test Case DRIVE-01: Drive Information Retrieval

**Objective**: Validate drive metadata retrieval and structure

**API Endpoint**: `GET /drives/{drive-id}`

**Test Implementation**:

```python
def test_drive_info_retrieval():
    """Test drive information retrieval"""
    
    token = get_valid_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with valid drive ID
    response = requests.get(
        f"https://graph.microsoft.com/v1.0/drives/{VALID_DRIVE_ID}",
        headers=headers
    )
    
    # Validate response
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    drive_data = response.json()
    
    # Validate required fields
    required_fields = ["id", "name", "driveType", "owner", "quota"]
    for field in required_fields:
        assert field in drive_data, f"Missing required field: {field}"
    
    # Validate drive ID format
    assert drive_data["id"] == VALID_DRIVE_ID, "Drive ID mismatch"
    
    # Validate drive type
    valid_drive_types = ["personal", "business", "documentLibrary"]
    assert drive_data["driveType"] in valid_drive_types, \
        f"Invalid drive type: {drive_data['driveType']}"
    
    return drive_data
```

**Expected Response Structure**:

```json
{
    "id": "b!ExampleDriveIdBase64EncodedStringHereForDocumentation123456",
    "name": "Documents",
    "driveType": "documentLibrary",
    "owner": {
        "user": {
            "displayName": "System Account"
        }
    },
    "quota": {
        "deleted": 0,
        "remaining": 27487790694400,
        "state": "normal",
        "total": 27487790694400,
        "used": 0
    }
}
```

---

### Test Case DRIVE-02: Site-to-Drive ID Resolution

**Objective**: Validate conversion from Site ID to Drive ID

**API Endpoint**: `GET /sites/{site-id}/drive`

**Test Implementation**:

```python
def test_site_to_drive_resolution():
    """Test site to drive ID resolution"""
    
    token = get_valid_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get drive from site
    response = requests.get(
        f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drive",
        headers=headers
    )
    
    assert response.status_code == 200, f"Site drive resolution failed: {response.status_code}"
    
    site_drive = response.json()
    resolved_drive_id = site_drive["id"]
    
    # Validate drive ID format (SharePoint drive IDs start with 'b!')
    assert resolved_drive_id.startswith("b!"), "SharePoint drive ID should start with 'b!'"
    
    # Cross-validate with direct drive access
    direct_response = requests.get(
        f"https://graph.microsoft.com/v1.0/drives/{resolved_drive_id}",
        headers=headers
    )
    
    assert direct_response.status_code == 200, "Resolved drive ID should be directly accessible"
    
    return resolved_drive_id
```

---

## Folder Management Operations

### Test Case FOLDER-01: Folder Creation

**Objective**: Validate folder creation with various scenarios

**API Endpoint**: `POST /drives/{drive-id}/root/children`

**Test Implementation**:

```python
def test_folder_creation():
    """Comprehensive folder creation testing"""
    
    token = get_valid_token()
    headers = {"Authorization": f"Bearer {token}"}
    base_url = f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}"
    
    test_scenarios = [
        {
            "name": "Basic folder creation",
            "folder_name": "Test_Folder_Basic",
            "conflict_behavior": "rename",
            "expected_status": [201]
        },
        {
            "name": "Folder with special characters",
            "folder_name": "Test Folder (2024) - Special!",
            "conflict_behavior": "rename", 
            "expected_status": [201]
        },
        {
            "name": "Duplicate folder with rename",
            "folder_name": "Test_Folder_Basic",  # Same as first
            "conflict_behavior": "rename",
            "expected_status": [201]
        },
        {
            "name": "Duplicate folder with fail",
            "folder_name": "Test_Folder_Basic",
            "conflict_behavior": "fail",
            "expected_status": [409]  # Conflict expected
        }
    ]
    
    created_folders = []
    
    for scenario in test_scenarios:
        payload = {
            "name": scenario["folder_name"],
            "folder": {},
            "@microsoft.graph.conflictBehavior": scenario["conflict_behavior"]
        }
        
        response = requests.post(
            f"{base_url}/root/children",
            headers=headers,
            json=payload
        )
        
        assert response.status_code in scenario["expected_status"], \
            f"Scenario '{scenario['name']}' failed: {response.status_code}"
        
        if response.status_code == 201:
            folder_data = response.json()
            created_folders.append(folder_data["id"])
            
            # Validate folder structure
            assert "id" in folder_data, "Folder should have ID"
            assert "name" in folder_data, "Folder should have name"
            assert "folder" in folder_data, "Should be folder type"
            assert folder_data["name"].startswith(scenario["folder_name"]), \
                "Folder name should match or be renamed version"
    
    # Cleanup
    for folder_id in created_folders:
        cleanup_response = requests.delete(f"{base_url}/items/{folder_id}", headers=headers)
        assert cleanup_response.status_code == 204, f"Cleanup failed for {folder_id}"
```

---

### Test Case FOLDER-02: Nested Folder Creation

**Objective**: Validate creation of nested folder structures

**Test Implementation**:

```python
def test_nested_folder_creation():
    """Test nested folder structure creation"""
    
    token = get_valid_token()
    headers = {"Authorization": f"Bearer {token}"}
    base_url = f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}"
    
    # Create nested structure: Parent/Child/Grandchild
    folder_structure = ["Parent_Folder", "Child_Folder", "Grandchild_Folder"]
    current_parent_id = "root"
    created_folder_ids = []
    
    for folder_name in folder_structure:
        # Determine the correct endpoint
        if current_parent_id == "root":
            endpoint = f"{base_url}/root/children"
        else:
            endpoint = f"{base_url}/items/{current_parent_id}/children"
        
        payload = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename"
        }
        
        response = requests.post(endpoint, headers=headers, json=payload)
        
        assert response.status_code == 201, \
            f"Failed to create folder '{folder_name}': {response.status_code}"
        
        folder_data = response.json()
        folder_id = folder_data["id"]
        created_folder_ids.append(folder_id)
        current_parent_id = folder_id
        
        # Validate parent-child relationship
        if len(created_folder_ids) > 1:
            parent_id = created_folder_ids[-2]
            children_response = requests.get(
                f"{base_url}/items/{parent_id}/children",
                headers=headers
            )
            assert children_response.status_code == 200
            children = children_response.json()["value"]
            child_ids = [child["id"] for child in children]
            assert folder_id in child_ids, "Child folder not found in parent"
    
    # Cleanup (reverse order to handle dependencies)
    for folder_id in reversed(created_folder_ids):
        cleanup_response = requests.delete(f"{base_url}/items/{folder_id}", headers=headers)
        assert cleanup_response.status_code == 204
```

---

## File Upload Operations

### Test Case UPLOAD-01: Small File Upload

**Objective**: Validate small file upload (< 4MB)

**API Endpoint**: `PUT /drives/{drive-id}/items/{parent-id}:/{filename}:/content`

**Test Implementation**:

```python
def test_small_file_upload():
    """Test small file upload operations"""
    
    token = get_valid_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream"
    }
    
    # Create test folder
    test_folder_id = create_test_folder("Upload_Test_Folder")
    
    test_files = [
        {
            "name": "small_text.txt",
            "content": b"This is a small text file for testing.",
            "size": 39
        },
        {
            "name": "small_binary.bin", 
            "content": bytes(range(256)),  # Binary content
            "size": 256
        },
        {
            "name": "unicode_test.txt",
            "content": "Unicode test: 你好世界 🌍 émojis".encode('utf-8'),
            "size": None  # Will be calculated
        }
    ]
    
    uploaded_file_ids = []
    
    for test_file in test_files:
        content = test_file["content"]
        expected_size = test_file["size"] or len(content)
        
        # Upload file
        response = requests.put(
            f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/items/{test_folder_id}:/{test_file['name']}:/content",
            headers=headers,
            data=content
        )
        
        assert response.status_code == 201, \
            f"File upload failed for '{test_file['name']}': {response.status_code}"
        
        file_data = response.json()
        uploaded_file_ids.append(file_data["id"])
        
        # Validate file metadata
        assert file_data["name"] == test_file["name"], "Filename mismatch"
        assert file_data["size"] == expected_size, f"Size mismatch: expected {expected_size}, got {file_data['size']}"
        assert "file" in file_data, "Should be file type"
        
        # Validate download
        download_response = requests.get(
            f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/items/{file_data['id']}/content",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert download_response.status_code == 200, "File download failed"
        assert download_response.content == content, "Downloaded content doesn't match uploaded content"
    
    # Cleanup
    cleanup_test_folder(test_folder_id)
```

---

### Test Case UPLOAD-02: Large File Upload (Resumable)

**Objective**: Validate large file upload using upload sessions

**API Endpoint**: `POST /drives/{drive-id}/items/{parent-id}:/{filename}:/createUploadSession`

**Test Implementation**:

```python
def test_large_file_upload():
    """Test large file upload with resumable sessions"""
    
    token = get_valid_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test folder
    test_folder_id = create_test_folder("Large_Upload_Test")
    
    # Generate large test file (10MB)
    large_file_size = 10 * 1024 * 1024  # 10MB
    chunk_size = 320 * 1024  # 320KB chunks (must be multiple of 320KB)
    
    # Step 1: Create upload session
    session_payload = {
        "item": {
            "@microsoft.graph.conflictBehavior": "rename"
        }
    }
    
    session_response = requests.post(
        f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/items/{test_folder_id}:/large_test_file.bin:/createUploadSession",
        headers=headers,
        json=session_payload
    )
    
    assert session_response.status_code == 200, \
        f"Upload session creation failed: {session_response.status_code}"
    
    session_data = session_response.json()
    upload_url = session_data["uploadUrl"]
    
    # Validate session response
    assert "uploadUrl" in session_data, "Upload URL missing from session"
    assert "expirationDateTime" in session_data, "Expiration time missing"
    
    # Step 2: Upload file in chunks
    uploaded_bytes = 0
    
    for chunk_start in range(0, large_file_size, chunk_size):
        chunk_end = min(chunk_start + chunk_size - 1, large_file_size - 1)
        chunk_data = bytes([(i % 256) for i in range(chunk_start, chunk_end + 1)])
        
        chunk_headers = {
            "Content-Length": str(len(chunk_data)),
            "Content-Range": f"bytes {chunk_start}-{chunk_end}/{large_file_size}"
        }
        
        chunk_response = requests.put(
            upload_url,
            headers=chunk_headers,
            data=chunk_data
        )
        
        # Validate chunk upload
        if chunk_end < large_file_size - 1:
            # Intermediate chunk
            assert chunk_response.status_code == 202, \
                f"Chunk upload failed: {chunk_response.status_code}"
            
            # Validate next expected ranges
            if chunk_response.content:
                range_data = chunk_response.json()
                assert "nextExpectedRanges" in range_data, "Next expected ranges missing"
        else:
            # Final chunk
            assert chunk_response.status_code in [200, 201], \
                f"Final chunk upload failed: {chunk_response.status_code}"
            
            file_data = chunk_response.json()
            assert file_data["size"] == large_file_size, "Final file size mismatch"
    
    # Cleanup
    cleanup_test_folder(test_folder_id)
```

---

## Error Handling & Edge Cases

### Test Case ERROR-01: Invalid Drive ID Handling

**Objective**: Validate proper error handling for invalid drive IDs

```python
def test_invalid_drive_id_handling():
    """Test error handling for invalid drive IDs"""
    
    token = get_valid_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    invalid_drive_ids = [
        "invalid-drive-id",
        "C2941A8C-2C52-4037-B56D-4C834D5DDC51",  # Old format
        "",
        "b!InvalidBase64Content",
        "not-a-drive-id-at-all"
    ]
    
    for invalid_id in invalid_drive_ids:
        response = requests.get(
            f"https://graph.microsoft.com/v1.0/drives/{invalid_id}",
            headers=headers
        )
        
        # Should return 400 Bad Request or 404 Not Found
        assert response.status_code in [400, 404], \
            f"Invalid drive ID '{invalid_id}' should return 400/404, got {response.status_code}"
        
        # Validate error response structure
        if response.content:
            error_data = response.json()
            assert "error" in error_data, "Error response should contain 'error' field"
            assert "code" in error_data["error"], "Error should contain code"
            assert "message" in error_data["error"], "Error should contain message"
```

---

### Test Case ERROR-02: Rate Limiting Handling

**Objective**: Validate rate limiting detection and retry logic

```python
def test_rate_limiting_handling():
    """Test rate limiting detection and handling"""
    
    token = get_valid_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Make rapid requests to trigger rate limiting
    request_count = 0
    rate_limited = False
    
    for i in range(100):  # Make many requests quickly
        response = requests.get(
            f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/root",
            headers=headers
        )
        
        request_count += 1
        
        if response.status_code == 429:  # Too Many Requests
            rate_limited = True
            
            # Validate rate limiting headers
            assert "Retry-After" in response.headers, "Retry-After header missing"
            retry_after = int(response.headers["Retry-After"])
            assert retry_after > 0, "Retry-After should be positive"
            
            # Test retry logic
            time.sleep(retry_after + 1)  # Wait longer than required
            
            retry_response = requests.get(
                f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/root",
                headers=headers
            )
            
            assert retry_response.status_code == 200, \
                "Request after rate limit should succeed"
            break
        
        elif response.status_code != 200:
            pytest.fail(f"Unexpected status code: {response.status_code}")
        
        time.sleep(0.1)  # Small delay between requests
    
    # Note: Rate limiting may not always be triggered in test environment
    print(f"Made {request_count} requests, rate limited: {rate_limited}")
```

---

## Performance & Rate Limiting

### Test Case PERF-01: Concurrent Upload Performance

**Objective**: Validate performance under concurrent upload scenarios

```python
import concurrent.futures
import threading

def test_concurrent_upload_performance():
    """Test concurrent upload performance and thread safety"""
    
    token = get_valid_token()
    test_folder_id = create_test_folder("Concurrent_Upload_Test")
    
    def upload_test_file(file_index):
        """Upload a single test file"""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream"
        }
        
        filename = f"concurrent_test_{file_index}.txt"
        content = f"Test file {file_index} content".encode('utf-8')
        
        start_time = time.time()
        
        response = requests.put(
            f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/items/{test_folder_id}:/{filename}:/content",
            headers=headers,
            data=content
        )
        
        end_time = time.time()
        
        return {
            "file_index": file_index,
            "status_code": response.status_code,
            "duration": end_time - start_time,
            "success": response.status_code == 201
        }
    
    # Test with multiple concurrent uploads
    num_concurrent_uploads = 5
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_uploads) as executor:
        futures = [executor.submit(upload_test_file, i) for i in range(num_concurrent_uploads)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # Validate results
    successful_uploads = [r for r in results if r["success"]]
    assert len(successful_uploads) == num_concurrent_uploads, \
        f"Expected {num_concurrent_uploads} successful uploads, got {len(successful_uploads)}"
    
    # Performance validation
    avg_duration = sum(r["duration"] for r in results) / len(results)
    max_duration = max(r["duration"] for r in results)
    
    print(f"Concurrent upload performance:")
    print(f"  Average duration: {avg_duration:.2f}s")
    print(f"  Maximum duration: {max_duration:.2f}s")
    
    # Cleanup
    cleanup_test_folder(test_folder_id)
```

---

## Test Automation Framework

### Test Configuration

```python
# test_config.py

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class TestConfig:
    """Test configuration settings"""
    
    # Authentication
    client_id: str
    tenant_id: str
    client_secret: str
    
    # SharePoint identifiers
    site_id: str
    drive_id: str
    
    # Test settings
    test_folder_prefix: str = "API_Test_"
    cleanup_after_tests: bool = True
    max_retry_attempts: int = 3
    request_timeout: int = 30
    
    # Performance thresholds
    max_upload_time_small_file: float = 5.0  # seconds
    max_upload_time_per_mb: float = 2.0      # seconds per MB
    
    @classmethod
    def from_environment(cls) -> 'TestConfig':
        """Load configuration from environment variables"""
        return cls(
            client_id=os.getenv("CLIENT_ID"),
            tenant_id=os.getenv("TENANT_ID"), 
            client_secret=os.getenv("CLIENT_SECRET"),
            site_id=os.getenv("SITE_ID"),
            drive_id=os.getenv("DRIVE_ID")
        )
    
    @classmethod
    def from_json_file(cls, filepath: str) -> 'TestConfig':
        """Load configuration from JSON file"""
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)

# Global test configuration
TEST_CONFIG = TestConfig.from_environment()
```

### Base Test Class

```python
# base_test.py

import pytest
import requests
import time
from typing import List, Dict, Any
from core.auth import GraphAuthentication

class BaseGraphAPITest:
    """Base class for Microsoft Graph API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.config = TEST_CONFIG
        self.auth = GraphAuthentication(
            client_id=self.config.client_id,
            tenant_id=self.config.tenant_id,
            client_secret=self.config.client_secret,
            scopes=["https://graph.microsoft.com/.default"]
        )
        self.token = self.auth.get_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.created_items = []  # Track created items for cleanup
        
        yield
        
        # Cleanup
        if self.config.cleanup_after_tests:
            self.cleanup_created_items()
    
    def make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with retry logic"""
        
        for attempt in range(self.config.max_retry_attempts):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    timeout=self.config.request_timeout,
                    **kwargs
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    time.sleep(retry_after)
                    continue
                
                return response
                
            except requests.RequestException as e:
                if attempt == self.config.max_retry_attempts - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception("Max retry attempts exceeded")
    
    def create_test_folder(self, folder_name: str, parent_id: str = "root") -> str:
        """Create a test folder and track for cleanup"""
        
        if parent_id == "root":
            url = f"https://graph.microsoft.com/v1.0/drives/{self.config.drive_id}/root/children"
        else:
            url = f"https://graph.microsoft.com/v1.0/drives/{self.config.drive_id}/items/{parent_id}/children"
        
        payload = {
            "name": f"{self.config.test_folder_prefix}{folder_name}",
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename"
        }
        
        response = self.make_request("POST", url, json=payload)
        assert response.status_code == 201, f"Failed to create test folder: {response.status_code}"
        
        folder_data = response.json()
        folder_id = folder_data["id"]
        self.created_items.append(folder_id)
        
        return folder_id
    
    def cleanup_created_items(self):
        """Clean up all created test items"""
        
        for item_id in reversed(self.created_items):  # Reverse order for nested items
            try:
                response = self.make_request(
                    "DELETE",
                    f"https://graph.microsoft.com/v1.0/drives/{self.config.drive_id}/items/{item_id}"
                )
                if response.status_code != 204:
                    print(f"Warning: Failed to cleanup item {item_id}: {response.status_code}")
            except Exception as e:
                print(f"Warning: Exception during cleanup of {item_id}: {e}")
```

---

## Validation Checklists

### Pre-Test Validation Checklist

- [ ] **Authentication Setup**
  - [ ] Valid Azure AD application registration
  - [ ] Client ID, Tenant ID, Client Secret configured
  - [ ] Required permissions granted and admin consent provided
  - [ ] Test environment variables/config file set up

- [ ] **SharePoint Environment**
  - [ ] Valid Site ID obtained
  - [ ] Valid Drive ID obtained (via site-based API)
  - [ ] Test user has appropriate access to SharePoint site
  - [ ] SharePoint site is accessible and operational

- [ ] **Network & Infrastructure**
  - [ ] Network connectivity to graph.microsoft.com
  - [ ] Firewall rules allow HTTPS traffic
  - [ ] DNS resolution working for Microsoft endpoints
  - [ ] SSL/TLS certificates valid

### API Endpoint Validation Checklist

#### Authentication Endpoints
- [ ] **Token Acquisition**
  - [ ] `POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token`
  - [ ] Valid token returned with correct claims
  - [ ] Token expiration time reasonable (typically 1 hour)
  - [ ] Token refresh working if applicable

#### Drive Operations
- [ ] **Drive Information**
  - [ ] `GET /drives/{drive-id}` returns 200 OK
  - [ ] Response contains required fields: id, name, driveType, owner, quota
  - [ ] Drive ID format validation (SharePoint drives start with 'b!')

- [ ] **Site Drive Resolution**
  - [ ] `GET /sites/{site-id}/drive` returns 200 OK
  - [ ] Resolved drive ID matches expected format
  - [ ] Cross-validation with direct drive access works

#### Folder Operations
- [ ] **Root Folder Access**
  - [ ] `GET /drives/{drive-id}/root` returns 200 OK
  - [ ] `GET /drives/{drive-id}/root/children` returns 200 OK
  - [ ] Folder listing contains expected structure

- [ ] **Folder Creation**
  - [ ] `POST /drives/{drive-id}/root/children` with folder payload returns 201 Created
  - [ ] Created folder has correct name and metadata
  - [ ] Conflict behavior (rename/fail) works as expected
  - [ ] Special characters in folder names handled correctly

- [ ] **Nested Folder Creation**
  - [ ] `POST /drives/{drive-id}/items/{parent-id}/children` returns 201 Created
  - [ ] Parent-child relationships maintained correctly
  - [ ] Deep nesting (3+ levels) works

#### File Operations
- [ ] **Small File Upload**
  - [ ] `PUT /drives/{drive-id}/items/{parent-id}:/{filename}:/content` returns 201 Created
  - [ ] File content uploaded correctly (validation via download)
  - [ ] File metadata (size, name, type) correct
  - [ ] Unicode filenames and content handled correctly

- [ ] **Large File Upload**
  - [ ] `POST /drives/{drive-id}/items/{parent-id}:/{filename}:/createUploadSession` returns 200 OK
  - [ ] Upload session URL provided and valid
  - [ ] Chunked upload with `PUT {uploadUrl}` works
  - [ ] Content-Range headers processed correctly
  - [ ] Final chunk returns file metadata

#### Error Handling
- [ ] **Invalid Requests**
  - [ ] Invalid drive IDs return 400 Bad Request
  - [ ] Malformed payloads return 400 Bad Request
  - [ ] Missing authentication returns 401 Unauthorized
  - [ ] Insufficient permissions return 403 Forbidden

- [ ] **Rate Limiting**
  - [ ] Excessive requests return 429 Too Many Requests
  - [ ] Retry-After header provided
  - [ ] Requests succeed after waiting

### Performance Validation Checklist

- [ ] **Response Times**
  - [ ] Authentication: < 2 seconds
  - [ ] Drive info retrieval: < 1 second
  - [ ] Folder creation: < 2 seconds
  - [ ] Small file upload (< 1MB): < 5 seconds
  - [ ] Large file upload: < 2 seconds per MB

- [ ] **Concurrent Operations**
  - [ ] Multiple simultaneous folder creations work
  - [ ] Multiple simultaneous file uploads work
  - [ ] No race conditions or data corruption
  - [ ] Thread safety maintained

- [ ] **Scalability**
  - [ ] Large folder structures (100+ items) handled
  - [ ] Large files (100MB+) uploaded successfully
  - [ ] Memory usage reasonable during operations

### Security Validation Checklist

- [ ] **Authentication Security**
  - [ ] Tokens properly secured (not logged or exposed)
  - [ ] Token expiration handled correctly
  - [ ] Invalid/expired tokens rejected

- [ ] **Data Security**
  - [ ] File content integrity maintained
  - [ ] No data leakage between operations
  - [ ] Proper cleanup of temporary data

- [ ] **Permission Validation**
  - [ ] Application permissions properly scoped
  - [ ] Unauthorized operations properly rejected
  - [ ] Admin consent requirements met

### Post-Test Validation Checklist

- [ ] **Cleanup Verification**
  - [ ] All test folders removed
  - [ ] All test files removed
  - [ ] No orphaned items remaining
  - [ ] SharePoint site in original state

- [ ] **Log Analysis**
  - [ ] No error messages in application logs
  - [ ] Performance metrics within acceptable ranges
  - [ ] No security warnings or issues

- [ ] **Documentation Updates**
  - [ ] Test results documented
  - [ ] Any issues or limitations noted
  - [ ] Configuration changes recorded
  - [ ] Known issues list updated

---

## Conclusion

This comprehensive testing specification ensures that all Microsoft Graph API interactions are validated to full specification. Regular execution of these tests will maintain reliability and catch any regressions or API changes that might affect the SharePoint Uploader application.

### Recommended Testing Schedule

- **Pre-deployment**: Full test suite execution
- **Weekly**: Core functionality tests (AUTH, DRIVE, FOLDER, UPLOAD basic scenarios)
- **Monthly**: Complete test suite including performance and edge cases
- **After API updates**: Full validation of affected endpoints

### Test Maintenance

- Keep test data and configurations up to date
- Monitor Microsoft Graph API changelog for breaking changes
- Update test cases when new features are added to the application
- Review and update performance thresholds based on production metrics 