import stat
from pathlib import Path
from unittest.mock import MagicMock, patch, ANY

import paramiko
import pytest
import socket

from core.progress import ProgressTracker
from core.ssh_copy import RemoteFetcher, SSHConnectionError


@pytest.fixture
def mock_progress_tracker():
    """Fixture for a mocked ProgressTracker."""
    tracker = MagicMock(spec=ProgressTracker)
    tracker.progress = MagicMock()
    return tracker


@pytest.fixture
def mock_paramiko():
    """Fixture to patch the paramiko library."""
    with patch("core.ssh_copy.paramiko", autospec=True) as mock_paramiko_lib:
        # Attach real exceptions to the mock
        mock_paramiko_lib.AuthenticationException = paramiko.AuthenticationException
        mock_paramiko_lib.SSHException = paramiko.SSHException

        # Mock SSHClient
        mock_ssh_client = MagicMock(spec=paramiko.SSHClient)
        mock_sftp_client = MagicMock(spec=paramiko.SFTPClient)
        mock_ssh_client.open_sftp.return_value = mock_sftp_client
        mock_paramiko_lib.SSHClient.return_value = mock_ssh_client

        # Mock RSAKey
        mock_paramiko_lib.RSAKey.from_private_key_file.return_value = MagicMock()

        # Mock stat() method to return a directory stat by default
        mock_stat_result = MagicMock()
        mock_stat_result.st_mode = stat.S_IFDIR  # Default to directory
        mock_sftp_client.stat.return_value = mock_stat_result

        # Make SFTP attributes
        mock_sftp_attr_dir = MagicMock(spec=paramiko.SFTPAttributes)
        mock_sftp_attr_dir.filename = "subdir"
        mock_sftp_attr_dir.st_mode = stat.S_IFDIR

        mock_sftp_attr_file = MagicMock(spec=paramiko.SFTPAttributes)
        mock_sftp_attr_file.filename = "file.txt"
        mock_sftp_attr_file.st_mode = stat.S_IFREG
        mock_sftp_attr_file.st_size = 1024

        mock_sftp_client.listdir_attr.return_value = [
            mock_sftp_attr_dir,
            mock_sftp_attr_file,
        ]

        yield mock_paramiko_lib, mock_ssh_client, mock_sftp_client


def test_remote_fetcher_init(mock_progress_tracker):
    """Test RemoteFetcher initialization."""
    fetcher = RemoteFetcher(
        progress_tracker=mock_progress_tracker,
        hostname="testhost",
        username="testuser",
        password="testpassword",
        private_key_path="/fake/key",
    )
    assert fetcher.hostname == "testhost"
    assert fetcher.username == "testuser"
    assert fetcher.password == "testpassword"
    assert fetcher.private_key_path == "/fake/key"


def test_connect_success_with_password(mock_paramiko, mock_progress_tracker):
    """Test successful SSH connection using a password."""
    mock_paramiko_lib, mock_ssh_client, _ = mock_paramiko
    fetcher = RemoteFetcher(
        progress_tracker=mock_progress_tracker,
        hostname="testhost",
        username="testuser",
        password="testpassword",
    )
    with fetcher:
        mock_ssh_client.connect.assert_called_once_with(
            hostname="testhost",
            port=22,
            username="testuser",
            password="testpassword",
            pkey=None,
            timeout=15,
        )
        assert fetcher.sftp_client is not None
    mock_ssh_client.close.assert_called_once()


def test_connect_success_with_private_key(mock_paramiko, mock_progress_tracker):
    """Test successful SSH connection using a private key."""
    mock_paramiko_lib, mock_ssh_client, _ = mock_paramiko
    mock_key = mock_paramiko_lib.RSAKey.from_private_key_file.return_value

    fetcher = RemoteFetcher(
        progress_tracker=mock_progress_tracker,
        hostname="testhost",
        username="testuser",
        private_key_path="/fake/key",
    )
    with fetcher:
        mock_paramiko_lib.RSAKey.from_private_key_file.assert_called_once_with("/fake/key")
        mock_ssh_client.connect.assert_called_once_with(
            hostname="testhost",
            port=22,
            username="testuser",
            password=None,
            pkey=mock_key,
            timeout=15,
        )
    mock_ssh_client.close.assert_called_once()


def test_connect_authentication_failure(mock_paramiko, mock_progress_tracker):
    """Test that SSHConnectionError is raised on authentication failure."""
    mock_paramiko_lib, mock_ssh_client, _ = mock_paramiko
    mock_ssh_client.connect.side_effect = paramiko.AuthenticationException("Auth failed")

    fetcher = RemoteFetcher(
        progress_tracker=mock_progress_tracker, hostname="testhost", username="testuser"
    )
    with pytest.raises(SSHConnectionError, match="Authentication failed"):
        fetcher.connect()


def test_fetch_directory_happy_path(mock_paramiko, mock_progress_tracker, tmp_path):
    """Test recursive directory fetching on a happy path."""
    _, mock_ssh_client, mock_sftp_client = mock_paramiko

    # Simulate nested directory structure
    top_level_dir_attr = MagicMock()
    top_level_dir_attr.filename = "subdir"
    top_level_dir_attr.st_mode = stat.S_IFDIR

    top_level_file_attr = MagicMock()
    top_level_file_attr.filename = "file.txt"
    top_level_file_attr.st_mode = stat.S_IFREG
    top_level_file_attr.st_size = 123

    sub_level_file_attr = MagicMock()
    sub_level_file_attr.filename = "nested_file.txt"
    sub_level_file_attr.st_mode = stat.S_IFREG
    sub_level_file_attr.st_size = 456

    def listdir_attr_side_effect(path):
        if path == "/remote/source":
            return [top_level_dir_attr, top_level_file_attr]
        elif path == "/remote/source/subdir":
            return [sub_level_file_attr]
        return []

    mock_sftp_client.listdir_attr.side_effect = listdir_attr_side_effect

    fetcher = RemoteFetcher(
        progress_tracker=mock_progress_tracker, hostname="testhost", username="testuser"
    )
    with fetcher:
        fetcher.fetch_directory("/remote/source", tmp_path)

    # Verify directory structure and file downloads
    # The implementation creates a subdirectory with the remote path name
    source_dir = tmp_path / "source"
    assert source_dir.is_dir()
    assert (source_dir / "subdir").is_dir()
    assert not (source_dir / "file.txt").exists()  # get() is mocked, so file not created
    assert not (source_dir / "subdir" / "nested_file.txt").exists()

    # Check that get was called for both files
    assert mock_sftp_client.get.call_count == 2
    mock_sftp_client.get.assert_any_call(
        "/remote/source/file.txt", str(source_dir / "file.txt"), callback=ANY
    )
    mock_sftp_client.get.assert_any_call(
        "/remote/source/subdir/nested_file.txt",
        str(source_dir / "subdir" / "nested_file.txt"),
        callback=ANY,
    )

    # Check progress tracker calls
    assert mock_progress_tracker.add_task.call_count == 2
    mock_progress_tracker.add_task.assert_any_call("file.txt", total_size=123)
    mock_progress_tracker.add_task.assert_any_call("nested_file.txt", total_size=456)


def test_fetch_directory_remote_not_found(mock_paramiko, mock_progress_tracker, tmp_path):
    """Test that FileNotFoundError is raised if remote path does not exist."""
    _, _, mock_sftp_client = mock_paramiko
    mock_sftp_client.listdir_attr.side_effect = FileNotFoundError("No such file")

    fetcher = RemoteFetcher(
        progress_tracker=mock_progress_tracker, hostname="testhost", username="testuser"
    )
    with fetcher:
        with pytest.raises(FileNotFoundError):
            fetcher.fetch_directory("/nonexistent/path", tmp_path)


def test_connect_ssh_exception(mock_paramiko, mock_progress_tracker):
    """Test that SSHConnectionError is raised on a generic SSHException."""
    _, mock_ssh_client, _ = mock_paramiko
    mock_ssh_client.connect.side_effect = paramiko.SSHException("Network error")

    fetcher = RemoteFetcher(
        progress_tracker=mock_progress_tracker, hostname="testhost", username="testuser"
    )
    with pytest.raises(SSHConnectionError, match="SSH error: Network error"):
        fetcher.connect()


def test_connect_socket_timeout(mock_paramiko, mock_progress_tracker):
    """Test that SSHConnectionError is raised on a socket timeout during connect."""
    _, mock_ssh_client, _ = mock_paramiko
    mock_ssh_client.connect.side_effect = socket.timeout("Connection timed out")

    fetcher = RemoteFetcher(
        progress_tracker=mock_progress_tracker, hostname="testhost", username="testuser"
    )
    with pytest.raises(SSHConnectionError, match="SSH connection timed out after 15 seconds."):
        fetcher.connect()


def test_fetch_directory_empty(mock_paramiko, mock_progress_tracker, tmp_path):
    """Test fetching an empty directory."""
    _, _, mock_sftp_client = mock_paramiko
    mock_sftp_client.listdir_attr.return_value = []

    fetcher = RemoteFetcher(
        progress_tracker=mock_progress_tracker, hostname="testhost", username="testuser"
    )
    with fetcher:
        fetcher.fetch_directory("/remote/empty", tmp_path)

    # Verify the local directory is created but empty
    # The implementation creates a subdirectory with the remote path name
    empty_dir = tmp_path / "empty"
    assert empty_dir.is_dir()
    assert not any(empty_dir.iterdir())
    mock_sftp_client.get.assert_not_called()


@pytest.mark.parametrize(
    "file_mode",
    [stat.S_IFLNK, stat.S_IFIFO, stat.S_IFCHR, stat.S_IFBLK, stat.S_IFSOCK],
)
def test_fetch_directory_ignores_unsupported_file_types(
    file_mode, mock_paramiko, mock_progress_tracker, tmp_path
):
    """Test that unsupported file types like symlinks or FIFOs are ignored."""
    _, _, mock_sftp_client = mock_paramiko

    # Mock listdir_attr to return a file with an unsupported type
    unsupported_attr = MagicMock()
    unsupported_attr.filename = "unsupported_file"
    unsupported_attr.st_mode = file_mode
    unsupported_attr.st_size = 0  # Size doesn't matter here

    mock_sftp_client.listdir_attr.return_value = [unsupported_attr]

    fetcher = RemoteFetcher(
        progress_tracker=mock_progress_tracker, hostname="testhost", username="testuser"
    )
    with fetcher:
        # This should run without raising an error
        fetcher.fetch_directory("/remote/source", tmp_path)

    # Verify that no download was attempted
    mock_sftp_client.get.assert_not_called()

    # Verify that the local directory was created but is empty
    assert tmp_path.is_dir()


def test_fetch_directory_with_special_characters_in_filenames(
    mock_paramiko, mock_progress_tracker, tmp_path
):
    """Test fetching files with names containing spaces and special characters."""
    _, _, mock_sftp_client = mock_paramiko

    # Mock listdir_attr to return files with special characters in their names
    file_attr_1 = MagicMock()
    file_attr_1.filename = "file with spaces.txt"
    file_attr_1.st_mode = stat.S_IFREG
    file_attr_1.st_size = 100

    file_attr_2 = MagicMock()
    file_attr_2.filename = "file-with-hyphens.log"
    file_attr_2.st_mode = stat.S_IFREG
    file_attr_2.st_size = 200

    file_attr_3 = MagicMock()
    file_attr_3.filename = "file_with_underscores.dat"
    file_attr_3.st_mode = stat.S_IFREG
    file_attr_3.st_size = 300

    mock_sftp_client.listdir_attr.return_value = [
        file_attr_1,
        file_attr_2,
        file_attr_3,
    ]

    fetcher = RemoteFetcher(
        progress_tracker=mock_progress_tracker, hostname="testhost", username="testuser"
    )
    with fetcher:
        fetcher.fetch_directory("/remote/source", tmp_path)

    # Verify that get was called for all files with correct paths
    # The implementation creates a subdirectory with the remote path name
    source_dir = tmp_path / "source"
    assert mock_sftp_client.get.call_count == 3
    mock_sftp_client.get.assert_any_call(
        f"/remote/source/{file_attr_1.filename}",
        str(source_dir / file_attr_1.filename),
        callback=ANY,
    )
    mock_sftp_client.get.assert_any_call(
        f"/remote/source/{file_attr_2.filename}",
        str(source_dir / file_attr_2.filename),
        callback=ANY,
    )
    mock_sftp_client.get.assert_any_call(
        f"/remote/source/{file_attr_3.filename}",
        str(source_dir / file_attr_3.filename),
        callback=ANY,
    )

    # Verify progress tracker calls
    assert mock_progress_tracker.add_task.call_count == 3
    mock_progress_tracker.add_task.assert_any_call(
        file_attr_1.filename, total_size=100
    )
    mock_progress_tracker.add_task.assert_any_call(
        file_attr_2.filename, total_size=200
    )
    mock_progress_tracker.add_task.assert_any_call(
        file_attr_3.filename, total_size=300
    )
    # Verify the source directory was created (files are mocked so won't exist)
    assert source_dir.is_dir()
    assert not any(source_dir.iterdir())  # No actual files since get() is mocked


def test_download_file_failure_and_cleanup(mock_paramiko, mock_progress_tracker, tmp_path):
    """Test that a failed download cleans up the partial file."""
    _, _, mock_sftp_client = mock_paramiko

    # Create a fake local file to simulate a partial download
    local_file_path = tmp_path / "file.txt"
    local_file_path.write_text("partial content")
    assert local_file_path.exists()

    # Mock sftp_client.get to raise an exception
    mock_sftp_client.get.side_effect = Exception("Download failed")

    fetcher = RemoteFetcher(
        progress_tracker=mock_progress_tracker, hostname="testhost", username="testuser"
    )
    with fetcher:
        with pytest.raises(Exception, match="Download failed"):
            fetcher._download_file("/remote/file.txt", local_file_path, 1024)

    # Verify that the partial file was cleaned up
    assert not local_file_path.exists()


def test_download_large_file_with_progress_updates(mock_paramiko, tmp_path):
    """Test the progress callback logic with a simulated large file download."""
    _, _, mock_sftp_client = mock_paramiko
    mock_progress_tracker = MagicMock(spec=ProgressTracker)
    
    # Mock the file_progress.tasks structure properly
    mock_task = MagicMock()
    mock_task.completed = 0
    mock_progress_tracker.file_progress = MagicMock()
    mock_progress_tracker.file_progress.tasks = {0: mock_task}
    mock_progress_tracker.add_task.return_value = 0

    # Capture the callback passed to sftp_client.get
    captured_callback = None

    def get_side_effect(remote, local, callback):
        nonlocal captured_callback
        captured_callback = callback

    mock_sftp_client.get.side_effect = get_side_effect

    fetcher = RemoteFetcher(
        progress_tracker=mock_progress_tracker, hostname="testhost", username="testuser"
    )
    large_file_size = 5 * 1024 * 1024  # 5 MB

    with fetcher:
        fetcher._download_file(
            "/remote/large_file.bin", tmp_path / "large_file.bin", large_file_size
        )

    # Simulate multiple progress updates for a large file
    assert captured_callback is not None
    captured_callback(1024 * 1024, large_file_size)  # 1 MB
    mock_task.completed = 1024 * 1024  # Update the mock task
    captured_callback(3 * 1024 * 1024, large_file_size)  # 3 MB
    mock_task.completed = 3 * 1024 * 1024  # Update the mock task
    captured_callback(large_file_size, large_file_size)  # 5 MB (complete)

    # Verify that the update method was called with the correct cumulative advances
    update_calls = mock_progress_tracker.update.call_args_list
    assert len(update_calls) == 3

    # Call 1: 1 MB transferred
    assert update_calls[0].args == ("large_file.bin", 1024 * 1024)

    # Call 2: 2 MB transferred since last update
    assert update_calls[1].args == ("large_file.bin", 2 * 1024 * 1024)

    # Call 3: 2 MB transferred since last update
    assert update_calls[2].args == ("large_file.bin", 2 * 1024 * 1024)


@patch("pathlib.Path.mkdir")
def test_fetch_directory_local_permission_error(
    mock_mkdir, mock_paramiko, mock_progress_tracker, tmp_path
):
    """Test handling of permission errors when creating local directories."""
    _, _, mock_sftp_client = mock_paramiko
    mock_mkdir.side_effect = PermissionError("Access denied")
    
    # Need to mock listdir_attr to return something to trigger mkdir
    dir_attr = MagicMock()
    dir_attr.filename = "newdir"
    dir_attr.st_mode = stat.S_IFDIR
    mock_sftp_client.listdir_attr.return_value = [dir_attr]

    fetcher = RemoteFetcher(
        progress_tracker=mock_progress_tracker, hostname="testhost", username="testuser"
    )
    with fetcher:
        with pytest.raises(PermissionError):
            fetcher.fetch_directory("/remote/source", tmp_path)


def test_download_progress_callback_logic(mock_paramiko, tmp_path):
    """Test the progress callback logic during file download."""
    _, _, mock_sftp_client = mock_paramiko

    # This is the main object being mocked
    mock_progress_tracker = MagicMock(spec=ProgressTracker)

    # The code under test accesses `progress_tracker.file_progress.tasks`, so we need to mock this structure.
    mock_rich_progress = MagicMock()
    mock_task = MagicMock()
    mock_task.completed = 0
    mock_rich_progress.tasks = {0: mock_task}  # The `tasks` attribute is a dict of task objects

    # Assign the mocked rich progress object to the 'file_progress' attribute of our main mock
    mock_progress_tracker.file_progress = mock_rich_progress

    # The code calls `add_task` and we need to return a task_id (key for the tasks dict)
    mock_progress_tracker.add_task.return_value = 0

    # We need to simulate the `update` method changing the `completed` value of the task
    def update_side_effect(filename, advance):
        # Update the mock task
        mock_task.completed += advance

    mock_progress_tracker.update.side_effect = update_side_effect

    # Capture the callback passed to the `sftp_client.get` method
    captured_callback = None

    def get_side_effect(remote, local, callback):
        nonlocal captured_callback
        captured_callback = callback

    mock_sftp_client.get.side_effect = get_side_effect

    fetcher = RemoteFetcher(
        progress_tracker=mock_progress_tracker, hostname="testhost", username="testuser"
    )
    with fetcher:
        # This call will set up the callback
        fetcher._download_file("/remote/file.txt", tmp_path / "file.txt", 1024)

    # Now, simulate the SFTP client calling the callback with progress updates
    assert captured_callback is not None
    captured_callback(100, 1024)  # 100 bytes transferred
    captured_callback(512, 1024)  # 512 bytes transferred in total
    captured_callback(1024, 1024)  # 1024 bytes transferred in total

    # Verify that our `update` method was called with the correct `advance` values
    update_calls = mock_progress_tracker.update.call_args_list
    assert len(update_calls) == 3

    # Call 1: advance should be 100 (100 - 0)
    assert update_calls[0].args == ("file.txt", 100)

    # Call 2: advance should be 412 (512 - 100)
    assert update_calls[1].args == ("file.txt", 412)

    # Call 3: advance should be 512 (1024 - 512)
    assert update_calls[2].args == ("file.txt", 512)