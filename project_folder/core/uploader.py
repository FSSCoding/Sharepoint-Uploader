import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from core.utils import StatePersister, load_config

class SharePointUploader:
    """
    SharePoint uploader with resumable upload support.
    
    This class handles large file uploads to SharePoint using Microsoft Graph API's
    resumable upload sessions. It supports chunked uploads, state persistence for
    resuming interrupted uploads, and retry logic for transient failures.
    """
    
    CHUNK_SIZE = 4 * 1024 * 1024  # 4MB chunks
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # Base delay in seconds for exponential backoff
    
    def __init__(self, token, config_path="config.json"):
        """
        Initialize the SharePoint uploader.
        
        Args:
            token (str): Bearer token for Microsoft Graph API authentication
            config_path (str): Path to the configuration file
        """
        self.token = token
        
        # Load configuration using the same logic as auth.py
        env_file = Path('.env')
        if env_file.exists():
            load_dotenv(env_file)
            # Use environment variables if available
            self.config = {
                'TENANT_ID': os.getenv('TENANT_ID'),
                'CLIENT_ID': os.getenv('CLIENT_ID'), 
                'CLIENT_SECRET': os.getenv('CLIENT_SECRET'),
                'SITE_ID': os.getenv('SITE_ID'),
                'DRIVE_ID': os.getenv('DRIVE_ID'),
                'SHAREPOINT_HOST': os.getenv('SHAREPOINT_HOST', 'graph.microsoft.com'),
                'SCOPES': os.getenv('SCOPES', 'https://graph.microsoft.com/.default')
            }
            # Check if all required env vars are present
            required_vars = ['TENANT_ID', 'CLIENT_ID', 'CLIENT_SECRET', 'SITE_ID', 'DRIVE_ID']
            if not all(self.config.get(var) for var in required_vars):
                self.config = load_config(config_path)
        else:
            self.config = load_config(config_path)
            
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        })
        self.state_persister = StatePersister()

    def create_upload_session(self, file_path, folder_path=""):
        """
        Create a resumable upload session for a file.
        
        Args:
            file_path (str): Path to the file to upload
            folder_path (str): Optional folder path in SharePoint (e.g., "Documents/SubFolder")
            
        Returns:
            str: Upload session URL
            
        Raises:
            Exception: If session creation fails
        """
        filename = os.path.basename(file_path)
        
        # Construct the API URL using specific site and drive IDs
        site_id = self.config.get("SITE_ID")
        drive_id = self.config.get("DRIVE_ID")
        
        if site_id and drive_id:
            # Use specific site and drive IDs for better targeting
            if folder_path:
                # Upload to specific folder
                item_path = f"{folder_path}/{filename}".replace("\\", "/")
                api_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{item_path}:/createUploadSession"
            else:
                # Upload to root of the drive
                api_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{filename}:/createUploadSession"
        else:
            # Fallback to default site/drive
            if folder_path:
                item_path = f"{folder_path}/{filename}".replace("\\", "/")
                api_url = f"https://graph.microsoft.com/v1.0/sites/root/drive/root:/{item_path}:/createUploadSession"
            else:
                api_url = f"https://graph.microsoft.com/v1.0/sites/root/drive/root:/{filename}:/createUploadSession"
        
        response = self.session.post(api_url, headers=self.session.headers)
        response.raise_for_status()
        
        result = response.json()
        return result["uploadUrl"]

    def upload_file(self, file_path, folder_path=""):
        """
        Upload a file using resumable upload with chunking and state persistence.
        
        Args:
            file_path (str): Path to the file to upload
            folder_path (str): Optional folder path in SharePoint
            
        Returns:
            dict: Upload result containing file metadata
            
        Raises:
            Exception: If upload fails after all retries
        """
        file_size = os.stat(file_path).st_size
        state_file = f"{file_path}.state.json"
        
        # Check if we can resume from a previous upload
        if os.path.exists(state_file):
            saved_state = load_upload_state(state_file)
            if saved_state:
                upload_url = saved_state["upload_url"]
                offset = saved_state["offset"]
            else:
                upload_url = self.create_upload_session(file_path, folder_path)
                offset = 0
        else:
            upload_url = self.create_upload_session(file_path, folder_path)
            offset = 0
        
        with open(file_path, 'rb') as file:
            file.seek(offset)
            
            while offset < file_size:
                chunk_size = min(self.CHUNK_SIZE, file_size - offset)
                chunk_data = file.read(chunk_size)
                
                # Upload chunk with retry logic
                result = self._upload_chunk_with_retry(
                    upload_url, chunk_data, offset, chunk_size, file_size
                )
                
                if result.status_code == 201:
                    # Upload complete
                    if os.path.exists(state_file):
                        os.remove(state_file)
                    return result.json()
                elif result.status_code == 202:
                    # Chunk uploaded successfully, continue
                    offset += chunk_size
                    # Save progress state
                    save_upload_state(state_file, {
                        "upload_url": upload_url,
                        "offset": offset
                    })
                else:
                    raise Exception(f"Unexpected response status: {result.status_code}")
        
        # Should not reach here in normal flow
        raise Exception("Upload completed but no final response received")

    def _upload_chunk_with_retry(self, upload_url, chunk_data, offset, chunk_size, total_size):
        """
        Upload a single chunk with retry logic for transient failures.
        
        Args:
            upload_url (str): Upload session URL
            chunk_data (bytes): Chunk data to upload
            offset (int): Byte offset in the file
            chunk_size (int): Size of the chunk
            total_size (int): Total file size
            
        Returns:
            requests.Response: Response from the upload request
            
        Raises:
            Exception: If all retries are exhausted
        """
        headers = {
            "Content-Range": f"bytes {offset}-{offset + chunk_size - 1}/{total_size}",
            "Content-Length": str(chunk_size)
        }
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.put(upload_url, data=chunk_data, headers=headers)
                
                if response.status_code in [200, 201, 202]:
                    return response
                elif response.status_code >= 500:
                    # Server error, retry
                    if attempt < self.MAX_RETRIES - 1:
                        delay = self.RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                        time.sleep(delay)
                        continue
                    else:
                        response.raise_for_status()
                else:
                    # Client error, don't retry
                    response.raise_for_status()
                    
            except requests.exceptions.RequestException as e:
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                    time.sleep(delay)
                    continue
                else:
                    raise e
        
        raise Exception(f"Failed to upload chunk after {self.MAX_RETRIES} attempts")


def save_upload_state(state_file, state_data):
    """
    Save upload state to a JSON file.
    
    Args:
        state_file (str): Path to the state file
        state_data (dict): State data to save
    """
    import json
    with open(state_file, 'w') as f:
        json.dump(state_data, f)


def load_upload_state(state_file):
    """
    Load upload state from a JSON file.
    
    Args:
        state_file (str): Path to the state file
        
    Returns:
        dict or None: Loaded state data or None if file doesn't exist/is invalid
    """
    import json
    try:
        with open(state_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None