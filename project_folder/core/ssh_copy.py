import os
import stat
import socket
from pathlib import Path

import paramiko

from .progress import ProgressTracker


class SSHConnectionError(Exception):
    """Custom exception for SSH connection-related errors."""
    pass


class RemoteFetcher:
    """
    Handles connecting to a remote server via SSH and fetching directories.
    """

    def __init__(
        self,
        progress_tracker: ProgressTracker,
        hostname: str,
        username: str,
        port: int = 22,
        password: str = None,
        private_key_path: str = None,
        timeout: int = 15,
    ):
        self.progress_tracker = progress_tracker
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.private_key_path = private_key_path
        self.timeout = timeout
        self.ssh_client = None
        self.sftp_client = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        """Establishes the SSH connection."""
        if self.ssh_client:
            return

        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            private_key = None
            if self.private_key_path:
                private_key = paramiko.RSAKey.from_private_key_file(self.private_key_path)

            self.ssh_client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                pkey=private_key,
                timeout=self.timeout,
            )
            self.sftp_client = self.ssh_client.open_sftp()

        except paramiko.AuthenticationException as e:
            raise SSHConnectionError(f"Authentication failed: {e}") from e
        except paramiko.SSHException as e:
            raise SSHConnectionError(f"SSH error: {e}") from e
        except socket.timeout:
            raise SSHConnectionError(f"SSH connection timed out after {self.timeout} seconds.")
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            raise SSHConnectionError(f"SSH connection timed out after {self.timeout} seconds.") from e
        except Exception as e:
            raise SSHConnectionError(f"An unexpected error occurred during connection: {e}") from e

    def close(self):
        """Closes the SFTP and SSH clients."""
        if self.sftp_client:
            self.sftp_client.close()
            self.sftp_client = None
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

    def fetch_directory(self, remote_path: str, local_path: Path):
        """
        Recursively fetches a directory from the remote server to a local path.
        """
        if not self.sftp_client:
            raise SSHConnectionError("SFTP client is not connected.")

        try:
            # Check if remote path exists and is a directory
            remote_stat = self.sftp_client.stat(remote_path)
            if not stat.S_ISDIR(remote_stat.st_mode):
                raise FileNotFoundError(f"Remote path '{remote_path}' is not a directory.")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Remote path '{remote_path}' not found.") from e

        # Create a subdirectory in the local path to house the fetched contents
        local_dest_path = local_path / Path(remote_path).name
        local_dest_path.mkdir(exist_ok=True)

        # Count total files for ETA calculation
        print("📊 Analyzing remote directory structure for ETA calculation...")
        total_files = self._count_remote_files(remote_path)
        self.progress_tracker.set_total_files(total_files)
        self.progress_tracker.update_status(f"Downloading {total_files} files...")
        
        print(f"📁 Found {total_files} files to download")

        self._recursive_fetch(remote_path, local_dest_path)

    def _count_remote_files(self, remote_dir: str) -> int:
        """Count total number of files in remote directory for ETA calculation."""
        total_files = 0
        try:
            for item_attr in self.sftp_client.listdir_attr(remote_dir):
                remote_item_path = f"{remote_dir}/{item_attr.filename}"
                
                if stat.S_ISDIR(item_attr.st_mode):
                    # Recursively count files in subdirectory
                    total_files += self._count_remote_files(remote_item_path)
                elif stat.S_ISREG(item_attr.st_mode):
                    # Count regular files
                    total_files += 1
        except Exception as e:
            # If we can't count files, just continue without ETA
            print(f"⚠️  Warning: Could not count files in {remote_dir}: {e}")
            
        return total_files

    def _recursive_fetch(self, remote_dir: str, local_dir: Path):
        """Helper for recursively fetching directory contents."""
        for item_attr in self.sftp_client.listdir_attr(remote_dir):
            remote_item_path = f"{remote_dir}/{item_attr.filename}"
            local_item_path = local_dir / item_attr.filename

            if stat.S_ISDIR(item_attr.st_mode):
                local_item_path.mkdir(exist_ok=True)
                self._recursive_fetch(remote_item_path, local_item_path)
            elif stat.S_ISREG(item_attr.st_mode):
                self._download_file(remote_item_path, local_item_path, item_attr.st_size)

    def _download_file(self, remote_file: str, local_file: Path, file_size: int):
        """Downloads a single file with progress tracking."""
        # Sanitize local filename for Windows compatibility
        sanitized_name = local_file.name.replace('|', '_').replace('<', '_').replace('>', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_')
        sanitized_local_file = local_file.parent / sanitized_name
        
        task_id = self.progress_tracker.add_task(
            sanitized_name, total_size=file_size
        )

        # Simple callback to update progress
        def progress_callback(bytes_transferred, total_bytes):
            # This callback gives total bytes, not delta. We need to calculate the advance.
            current_completed = self.progress_tracker.file_progress.tasks[task_id].completed
            advance = bytes_transferred - current_completed
            if advance > 0:
                self.progress_tracker.update(sanitized_name, advance)

        try:
            self.sftp_client.get(remote_file, str(sanitized_local_file), callback=progress_callback)
            # Mark file as completed for ETA tracking
            self.progress_tracker.complete_file(sanitized_name)
        except Exception as e:
            # Clean up partially downloaded file on error
            if sanitized_local_file.exists():
                sanitized_local_file.unlink()
            raise e