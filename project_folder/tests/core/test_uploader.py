"""Tests for the uploader module."""

import pytest
import os
from unittest.mock import patch, MagicMock, mock_open
from core.uploader import SharePointUploader

# Constants for testing
DUMMY_TOKEN = "DUMMY_ACCESS_TOKEN"
TEST_FILE_PATH = "/path/to/fake/large_file.bin"
TEST_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
UPLOAD_URL = "https://graph.microsoft.com/v1.0/sites/root/drive/items/root:/large_file.bin:/createUploadSession"
SESSION_URL = "https://graph.microsoft.com/v1.0/some/upload/session"

@pytest.fixture
def mock_uploader():
    """Fixture to create a SharePointUploader instance with a dummy token."""
    return SharePointUploader(DUMMY_TOKEN)

@pytest.fixture
def mock_requests_session():
    """Fixture to mock requests.Session."""
    with patch('requests.Session') as mock_session_constructor:
        mock_session = MagicMock()
        mock_session_constructor.return_value = mock_session
        yield mock_session

@pytest.fixture
def mock_os_stat():
    """Fixture to mock os.stat to return a fake file size."""
    with patch('os.stat') as mock_stat:
        mock_stat.return_value.st_size = TEST_FILE_SIZE
        yield mock_stat

@pytest.fixture
def mock_file_open():
    """Fixture to mock open for file reading."""
    # Mock a file that returns chunks of data
    mock_file = mock_open(read_data=b'a' * (4 * 1024 * 1024))
    with patch('builtins.open', mock_file):
        yield mock_file

# --- Test Placeholder and Basic Initialization ---

def test_uploader_placeholder():
    """Ensure the original placeholder test still behaves as expected if needed."""
    assert True

def test_uploader_initialization(mock_uploader):
    """Test that the SharePointUploader initializes correctly."""
    assert mock_uploader.token == DUMMY_TOKEN
    assert mock_uploader.session is not None

# --- Test Resumable Upload Session Creation ---

def test_create_upload_session_success(mock_uploader):
    """Test successful creation of a resumable upload session."""
    # Mock the config to return test values
    mock_uploader.config = {
        "SITE_ID": "test-site-id",
        "DRIVE_ID": "test-drive-id"
    }
    
    with patch.object(mock_uploader.session, 'post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"uploadUrl": SESSION_URL}
        mock_post.return_value = mock_response

        session_url = mock_uploader.create_upload_session(TEST_FILE_PATH)

        # Verify the correct API endpoint was called with specific site and drive IDs
        site_id = mock_uploader.config.get("SITE_ID")
        drive_id = mock_uploader.config.get("DRIVE_ID")
        filename = os.path.basename(TEST_FILE_PATH)
        expected_api_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{filename}:/createUploadSession"
        mock_post.assert_called_once_with(expected_api_url, headers=mock_uploader.session.headers)
        
        assert session_url == SESSION_URL

def test_create_upload_session_failure(mock_uploader):
    """Test handling of a failed upload session creation."""
    with patch.object(mock_uploader.session, 'post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_post.return_value = mock_response

        with pytest.raises(Exception, match="API Error"):
            mock_uploader.create_upload_session(TEST_FILE_PATH)

# --- Test Chunked File Upload Process ---

def test_upload_file_full_success(mock_uploader, mock_os_stat, mock_file_open):
    """Test the successful upload of a file in chunks from start to finish."""
    # Mock the config
    mock_uploader.config = {
        "SITE_ID": "test-site-id",
        "DRIVE_ID": "test-drive-id"
    }
    
    # Mock session creation
    with patch.object(mock_uploader, 'create_upload_session', return_value=SESSION_URL) as mock_create_session, \
         patch.object(mock_uploader.session, 'put') as mock_put, \
         patch('core.uploader.save_upload_state') as mock_save_state, \
         patch('core.uploader.load_upload_state', return_value=None), \
         patch('os.path.exists', return_value=False), \
         patch('os.remove') as mock_remove:

        # Mock responses for each chunk upload
        mock_response_chunk1 = MagicMock(status_code=202, json=lambda: {"nextExpectedRanges": ["4194304-8388607"]})
        mock_response_chunk2 = MagicMock(status_code=202, json=lambda: {"nextExpectedRanges": ["8388608-10485759"]})
        mock_response_final = MagicMock(status_code=201, json=lambda: {"id": "file_id", "name": "large_file.bin"})
        mock_put.side_effect = [mock_response_chunk1, mock_response_chunk2, mock_response_final]

        result = mock_uploader.upload_file(TEST_FILE_PATH)

        # Verify session was created
        mock_create_session.assert_called_once_with(TEST_FILE_PATH, "")
        
        # Verify all chunks were uploaded
        assert mock_put.call_count == 3
        
        # Verify state was saved for each chunk
        assert mock_save_state.call_count == 2 # First two chunks

        # Verify final result
        assert result['id'] == "file_id"

def test_upload_file_resume_from_state(mock_uploader, mock_os_stat, mock_file_open):
    """Test resuming an upload from a saved state."""
    # Simulate a state where the first chunk was already uploaded
    saved_state = {"upload_url": SESSION_URL, "offset": 4194304}
    
    with patch('core.uploader.load_upload_state', return_value=saved_state), \
         patch('os.path.exists', return_value=True), \
         patch('core.uploader.save_upload_state') as mock_save_state, \
         patch('os.remove') as mock_remove, \
         patch.object(mock_uploader.session, 'put') as mock_put:

        # Mock responses for the remaining chunks
        mock_response_chunk2 = MagicMock(status_code=202, json=lambda: {"nextExpectedRanges": ["8388608-10485759"]})
        mock_response_final = MagicMock(status_code=201, json=lambda: {"id": "file_id"})
        mock_put.side_effect = [mock_response_chunk2, mock_response_final]

        result = mock_uploader.upload_file(TEST_FILE_PATH)

        # Verify file handle was seeked to the correct offset
        mock_file_open().seek.assert_called_once_with(saved_state['offset'])

        # Verify only the remaining chunks were uploaded
        assert mock_put.call_count == 2
        assert result['id'] == "file_id"
        
        # Verify state file was removed after successful upload
        mock_remove.assert_called_once()

def test_upload_chunk_retry_on_failure(mock_uploader, mock_os_stat, mock_file_open):
    """Test that the uploader retries a chunk upload on transient failure."""
    with patch.object(mock_uploader, 'create_upload_session', return_value=SESSION_URL), \
         patch.object(mock_uploader.session, 'put') as mock_put, \
         patch('core.uploader.load_upload_state', return_value=None), \
         patch('os.path.exists', return_value=False), \
         patch('time.sleep') as mock_sleep: # Mock sleep to speed up test

        # Simulate a network error followed by a success
        mock_failure = MagicMock(status_code=503)
        mock_failure.raise_for_status.side_effect = Exception("Service Unavailable")
        mock_success = MagicMock(status_code=202, json=lambda: {"nextExpectedRanges": ["4194304-8388607"]})
        
        # The final successful upload
        mock_final_success = MagicMock(status_code=201, json=lambda: {"id": "file_id"})

        mock_put.side_effect = [mock_failure, mock_success, mock_success, mock_final_success]

        result = mock_uploader.upload_file(TEST_FILE_PATH)

        # Expecting more than the usual number of PUTs due to retry
        assert mock_put.call_count > 3
        assert mock_sleep.called  # Exponential backoff should trigger sleep
        assert result['id'] == "file_id"