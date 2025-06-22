import os
import pytest
import shutil
import tempfile
from pathlib import Path
import hashlib

# Assuming the core logic is in RemoteFetcher as hinted by unit tests
from core.ssh_copy import RemoteFetcher, SSHConnectionError
from core.progress import ProgressTracker

# --- Test Configuration ---
# These tests require a live SSH server. The connection details are expected
# to be provided via environment variables.
#
# Required Environment Variables:
#   - TEST_SSH_HOST: Hostname or IP of the test SSH server.
#   - TEST_SSH_PORT: Port of the test SSH server.
#   - TEST_SSH_USER: Username for authentication.
#   - TEST_SSH_PASS: Password for authentication.
#
# The test server must have a specific directory structure for the successful
# transfer test to pass. It should have a directory '/tmp/test_remote_src'
# with the following structure:
# /tmp/test_remote_src/
# |-- file1.txt (content: "hello")
# |-- subdir/
# |   |-- file2.txt (content: "world")

# Helper to skip tests if the required environment variables are not set.
requires_ssh_server = pytest.mark.skipif(
    not all(
        os.getenv(var)
        for var in ["TEST_SSH_HOST", "TEST_SSH_PORT", "TEST_SSH_USER", "TEST_SSH_PASS"]
    ),
    reason="Test SSH server environment variables not set",
)


def calculate_sha256(filepath):
    """Calculates the SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256.update(byte_block)
    return sha256.hexdigest()


@pytest.fixture
def ssh_credentials():
    """Provides SSH credentials from environment variables."""
    return {
        "hostname": os.getenv("TEST_SSH_HOST"),
        "port": int(os.getenv("TEST_SSH_PORT")),
        "username": os.getenv("TEST_SSH_USER"),
        "password": os.getenv("TEST_SSH_PASS"),
    }


@pytest.fixture
def local_temp_dir():
    """Creates a temporary local directory for downloads and cleans it up afterward."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@requires_ssh_server
def test_system_successful_transfer(ssh_credentials, local_temp_dir):
    """
    Tests a successful directory transfer from the remote SSH server.
    Verifies that the directory structure and file contents are correct.
    """
    remote_path = "/tmp/test_remote_src"
    tracker = ProgressTracker()
    fetcher = RemoteFetcher(progress_tracker=tracker, **ssh_credentials)

    with fetcher:
        fetcher.fetch_directory(remote_path, local_temp_dir)

    # Verify local directory structure
    local_base_path = local_temp_dir / "test_remote_src"
    assert local_base_path.is_dir()
    assert (local_base_path / "file1.txt").is_file()
    assert (local_base_path / "subdir").is_dir()
    assert (local_base_path / "subdir" / "file2.txt").is_file()

    # Verify file content by checking their content (strip newlines from echo command)
    with open(local_base_path / "file1.txt", "r") as f:
        assert f.read().strip() == "hello"
    with open(local_base_path / "subdir" / "file2.txt", "r") as f:
        assert f.read().strip() == "world"


@requires_ssh_server
def test_system_connection_failure(ssh_credentials):
    """
    Tests that connecting to an invalid host/port raises SSHConnectionError.
    """
    invalid_credentials = ssh_credentials.copy()
    invalid_credentials["hostname"] = "127.0.0.1"
    invalid_credentials["port"] = 2222  # An unlikely port to be open

    tracker = ProgressTracker()
    fetcher = RemoteFetcher(progress_tracker=tracker, **invalid_credentials)

    with pytest.raises(SSHConnectionError, match="SSH connection timed out"):
        fetcher.connect()


@requires_ssh_server
def test_system_authentication_failure(ssh_credentials):
    """
    Tests that using incorrect credentials raises an authentication-related error.
    """
    auth_fail_credentials = ssh_credentials.copy()
    auth_fail_credentials["password"] = "wrongpassword"

    tracker = ProgressTracker()
    fetcher = RemoteFetcher(progress_tracker=tracker, **auth_fail_credentials)

    with pytest.raises(SSHConnectionError, match="Authentication failed"):
        fetcher.connect()


@requires_ssh_server
def test_system_remote_path_not_found(ssh_credentials, local_temp_dir):
    """
    Tests that fetching a non-existent remote directory raises FileNotFoundError.
    """
    remote_path = "/tmp/this_path_should_not_exist_12345"
    tracker = ProgressTracker()
    fetcher = RemoteFetcher(progress_tracker=tracker, **ssh_credentials)

    with fetcher:
        with pytest.raises(FileNotFoundError):
            fetcher.fetch_directory(remote_path, local_temp_dir)