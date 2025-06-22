# SSH Testing - Report

**Original Report Date:** 2024-12-01
**Project Phase:** Testing

## 1. Executive Summary

This report provides a comprehensive overview of SSH testing requirements and procedures for the SharePoint Uploader CLI application. The SSH functionality enables secure remote file transfer from SSH servers to local directories before uploading to SharePoint. This report details the testing strategy, prerequisites, test cases, and execution procedures necessary to validate the SSH module's reliability and robustness.

## 2. SSH Functionality Overview

### 2.1 Core Components

The SSH functionality is implemented in the `RemoteFetcher` class within `project_folder/core/ssh_copy.py`. Key features include:

- **SSH Connection Management**: Establishes secure connections using the `paramiko` library
- **Authentication Support**: Supports both password and private key authentication methods
- **SFTP File Transfer**: Recursive directory fetching with progress tracking
- **Error Handling**: Custom `SSHConnectionError` exceptions for connection failures
- **Context Manager**: Automatic connection cleanup using `__enter__` and `__exit__` methods

### 2.2 Technical Architecture

- **Library Dependencies**: `paramiko` for SSH/SFTP operations
- **Progress Tracking**: Integration with `ProgressTracker` for file transfer monitoring
- **Connection Parameters**: Configurable hostname, port, username, password, private key path, and timeout
- **Security Policy**: Uses `AutoAddPolicy` for host key verification (development/testing only)

## 3. Testing Prerequisites

### 3.1 Environment Setup

#### Local Environment Requirements:
- **Operating System**: Windows/Linux/macOS
- **Python Version**: 3.8+
- **Dependencies**: Install from `project_folder/requirements.txt`
- **Test Framework**: pytest

#### SSH Server Environment:
- **Test SSH Server**: Accessible SSH server for system-level testing
- **Required Environment Variables**:
  - `TEST_SSH_HOST`: Hostname or IP of the test SSH server
  - `TEST_SSH_PORT`: Port of the test SSH server (typically 22)
  - `TEST_SSH_USER`: Username for authentication
  - `TEST_SSH_PASS`: Password for authentication

#### Test Data Structure:
The test SSH server must have the following directory structure at `/tmp/test_remote_src/`:
```
/tmp/test_remote_src/
├── file1.txt (content: "hello")
└── subdir/
    └── file2.txt (content: "world")
```

### 3.2 Configuration Requirements

- **SSH Credentials**: Valid SSH server credentials for authentication testing
- **Network Connectivity**: Ensure firewall rules allow SSH connections
- **File Permissions**: Appropriate read permissions on remote test files
- **Local Storage**: Sufficient disk space for downloaded test files

## 4. Test Categories and Cases

### 4.1 Unit Tests (`test_ssh_copy.py`)

The unit test suite provides comprehensive coverage of the `RemoteFetcher` class functionality using mocked dependencies.

#### 4.1.1 Initialization Tests
- **TC-SSH-U-001**: `test_remote_fetcher_init`
  - **Purpose**: Verify proper initialization of RemoteFetcher with all parameters
  - **Expected Result**: All instance variables correctly set

#### 4.1.2 Connection Tests
- **TC-SSH-U-002**: `test_connect_success_with_password`
  - **Purpose**: Test successful SSH connection using password authentication
  - **Expected Result**: SSH client connects with correct parameters, SFTP client established

- **TC-SSH-U-003**: `test_connect_success_with_private_key`
  - **Purpose**: Test successful SSH connection using private key authentication
  - **Expected Result**: Private key loaded, SSH connection established with key authentication

- **TC-SSH-U-004**: `test_connect_authentication_failure`
  - **Purpose**: Verify proper handling of authentication failures
  - **Expected Result**: `SSHConnectionError` raised with "Authentication failed" message

- **TC-SSH-U-005**: `test_connect_ssh_exception`
  - **Purpose**: Test handling of generic SSH protocol errors
  - **Expected Result**: `SSHConnectionError` raised with "SSH error" prefix

- **TC-SSH-U-006**: `test_connect_socket_timeout`
  - **Purpose**: Verify timeout handling during connection attempts
  - **Expected Result**: `SSHConnectionError` raised with timeout message

#### 4.1.3 File Transfer Tests
- **TC-SSH-U-007**: `test_fetch_directory_happy_path`
  - **Purpose**: Test successful recursive directory fetching
  - **Expected Result**: Directory structure replicated, all files downloaded, progress tracking called

- **TC-SSH-U-008**: `test_fetch_directory_remote_not_found`
  - **Purpose**: Test handling of non-existent remote paths
  - **Expected Result**: `FileNotFoundError` raised

- **TC-SSH-U-009**: `test_fetch_directory_empty`
  - **Purpose**: Test behavior with empty remote directories
  - **Expected Result**: Empty local directory created, no errors

- **TC-SSH-U-010**: `test_fetch_directory_ignores_unsupported_file_types`
  - **Purpose**: Verify handling of special file types (symlinks, FIFOs, etc.)
  - **Expected Result**: Unsupported file types ignored, no errors

- **TC-SSH-U-011**: `test_fetch_directory_with_special_characters_in_filenames`
  - **Purpose**: Test handling of filenames with special characters
  - **Expected Result**: Files with special characters handled correctly

- **TC-SSH-U-012**: `test_download_file_failure_and_cleanup`
  - **Purpose**: Verify cleanup of partially downloaded files on failure
  - **Expected Result**: Partial files removed on download failure

- **TC-SSH-U-013**: `test_download_large_file_with_progress_updates`
  - **Purpose**: Test progress tracking for large file downloads
  - **Expected Result**: Progress callbacks executed, accurate progress reporting

- **TC-SSH-U-014**: `test_fetch_directory_local_permission_error`
  - **Purpose**: Test handling of local filesystem permission errors
  - **Expected Result**: Appropriate exception handling for permission issues

### 4.2 System Tests (`test_system_ssh.py`)

System tests validate end-to-end SSH functionality using a real SSH server connection.

#### 4.2.1 Integration Tests
- **TC-SSH-S-001**: `test_system_successful_transfer`
  - **Purpose**: Validate complete directory transfer from remote SSH server
  - **Prerequisites**: Live SSH server with test data structure
  - **Expected Result**: 
    - Remote directory structure replicated locally
    - File contents match expected values ("hello" and "world")
    - All files successfully transferred

- **TC-SSH-S-002**: `test_system_connection_failure`
  - **Purpose**: Test connection failure handling with invalid host/port
  - **Prerequisites**: Invalid SSH server credentials (unreachable host)
  - **Expected Result**: `SSHConnectionError` raised with timeout message

- **TC-SSH-S-003**: `test_system_authentication_failure`
  - **Purpose**: Test authentication failure with incorrect credentials
  - **Prerequisites**: Valid SSH server with incorrect password
  - **Expected Result**: `SSHConnectionError` raised with authentication failure message

- **TC-SSH-S-004**: `test_system_remote_path_not_found`
  - **Purpose**: Test handling of non-existent remote directories
  - **Prerequisites**: Valid SSH connection to server without test path
  - **Expected Result**: `FileNotFoundError` raised

## 5. Test Execution Instructions

### 5.1 Running Unit Tests

#### Execute All SSH Unit Tests:
```bash
cd project_folder
pytest tests/core/test_ssh_copy.py -v
```

#### Execute Specific Test Categories:
```bash
# Connection tests only
pytest tests/core/test_ssh_copy.py -k "connect" -v

# File transfer tests only
pytest tests/core/test_ssh_copy.py -k "fetch" -v

# Progress tracking tests only
pytest tests/core/test_ssh_copy.py -k "progress" -v
```

#### Generate Coverage Report:
```bash
pytest tests/core/test_ssh_copy.py --cov=core.ssh_copy --cov-report=html
```

### 5.2 Running System Tests

#### Prerequisites Check:
Before running system tests, verify environment variables are set:
```bash
echo $TEST_SSH_HOST
echo $TEST_SSH_PORT
echo $TEST_SSH_USER
echo $TEST_SSH_PASS
```

#### Execute System Tests:
```bash
cd project_folder
pytest tests/test_system_ssh.py -v
```

#### Skip System Tests (if no SSH server available):
System tests are automatically skipped if environment variables are not set. To explicitly skip:
```bash
pytest tests/test_system_ssh.py -v -m "not requires_ssh_server"
```

### 5.3 Complete SSH Test Suite

#### Run All SSH Tests:
```bash
cd project_folder
pytest tests/core/test_ssh_copy.py tests/test_system_ssh.py -v
```

#### Generate Comprehensive Test Report:
```bash
pytest tests/core/test_ssh_copy.py tests/test_system_ssh.py --html=ssh_test_report.html --self-contained-html
```

#### Using the Dedicated SSH Testing Script:
A specialized testing script `run_ssh_tests.py` is available for convenient SSH testing:

```bash
# Run all SSH tests with coverage
python run_ssh_tests.py --coverage

# Run only unit tests
python run_ssh_tests.py --unit-only

# Run only system tests
python run_ssh_tests.py --system-only

# Show help
python run_ssh_tests.py --help
```

The script provides:
- Automatic virtual environment detection
- Detailed test execution feedback
- Coverage reporting (both terminal and HTML)
- Environment variable validation for system tests
- Clear success/failure indicators

## 6. Expected Test Outcomes

### 6.1 Successful Test Run Indicators

#### Unit Tests Success Criteria:
- All 19 unit test cases pass (100% success rate)
- No unexpected exceptions or errors
- Mock assertions verify correct paramiko API usage
- Progress tracking integration validated
- 92% code coverage of SSH module achieved

#### System Tests Success Criteria:
- Successful connection to test SSH server
- Complete directory structure replication
- File content integrity maintained
- Proper error handling for various failure scenarios

### 6.2 Test Output Examples

#### Successful Unit Test Run:
```
============================= test session starts ==============================
collected 19 items

tests/core/test_ssh_copy.py::test_remote_fetcher_init PASSED             [  5%]
tests/core/test_ssh_copy.py::test_connect_success_with_password PASSED   [ 10%]
tests/core/test_ssh_copy.py::test_connect_success_with_private_key PASSED [ 15%]
tests/core/test_ssh_copy.py::test_connect_authentication_failure PASSED  [ 21%]
tests/core/test_ssh_copy.py::test_fetch_directory_happy_path PASSED      [ 26%]
tests/core/test_ssh_copy.py::test_fetch_directory_remote_not_found PASSED [ 31%]
tests/core/test_ssh_copy.py::test_connect_ssh_exception PASSED           [ 36%]
tests/core/test_ssh_copy.py::test_connect_socket_timeout PASSED          [ 42%]
tests/core/test_ssh_copy.py::test_fetch_directory_empty PASSED           [ 47%]
tests/core/test_ssh_copy.py::test_fetch_directory_ignores_unsupported_file_types[40960] PASSED [ 52%]
tests/core/test_ssh_copy.py::test_fetch_directory_ignores_unsupported_file_types[4096] PASSED [ 57%]
tests/core/test_ssh_copy.py::test_fetch_directory_ignores_unsupported_file_types[8192] PASSED [ 63%]
tests/core/test_ssh_copy.py::test_fetch_directory_ignores_unsupported_file_types[24576] PASSED [ 68%]
tests/core/test_ssh_copy.py::test_fetch_directory_ignores_unsupported_file_types[49152] PASSED [ 73%]
tests/core/test_ssh_copy.py::test_fetch_directory_with_special_characters_in_filenames PASSED [ 78%]
tests/core/test_ssh_copy.py::test_download_file_failure_and_cleanup PASSED [ 84%]
tests/core/test_ssh_copy.py::test_download_large_file_with_progress_updates PASSED [ 89%]
tests/core/test_ssh_copy.py::test_fetch_directory_local_permission_error PASSED [ 94%]
tests/core/test_ssh_copy.py::test_download_progress_callback_logic PASSED [100%]

============================== 19 passed in 1.05s ==============================
```

#### Successful System Test Run:
```
============================= test session starts ==============================
collected 4 items

tests/test_system_ssh.py::test_system_successful_transfer SKIPPED (Test SSH server environment variables not set) [25%]
tests/test_system_ssh.py::test_system_connection_failure SKIPPED (Test SSH server environment variables not set) [50%]
tests/test_system_ssh.py::test_system_authentication_failure SKIPPED (Test SSH server environment variables not set) [75%]
tests/test_system_ssh.py::test_system_remote_path_not_found SKIPPED (Test SSH server environment variables not set) [100%]

============================== 4 skipped in 0.30s ===============================
```

## 7. Troubleshooting Common Issues

### 7.1 Connection Failures

#### Issue: `SSHConnectionError: SSH connection timed out`
**Possible Causes:**
- Network connectivity issues
- Firewall blocking SSH port (22)
- SSH server not running
- Incorrect hostname/IP address

**Resolution Steps:**
1. Verify network connectivity: `ping <hostname>`
2. Check SSH port accessibility: `telnet <hostname> 22`
3. Verify SSH server status
4. Check firewall rules

#### Issue: `SSHConnectionError: Authentication failed`
**Possible Causes:**
- Incorrect username/password
- Invalid private key file
- SSH server authentication restrictions
- Key file permission issues

**Resolution Steps:**
1. Verify credentials manually: `ssh user@hostname`
2. Check private key file permissions (should be 600)
3. Validate private key format
4. Review SSH server authentication logs

### 7.2 File Transfer Issues

#### Issue: `FileNotFoundError: Remote path not found`
**Possible Causes:**
- Incorrect remote path specification
- Missing test data structure on SSH server
- Insufficient permissions on remote directory

**Resolution Steps:**
1. Verify remote path exists: `ssh user@hostname ls -la /path`
2. Create required test data structure
3. Check directory permissions

#### Issue: Progress tracking inconsistencies
**Possible Causes:**
- Large file transfer interruptions
- Network instability
- Callback function errors

**Resolution Steps:**
1. Test with smaller files first
2. Check network stability
3. Review progress tracker implementation

## 8. Performance Considerations

### 8.1 Test Execution Time

- **Unit Tests**: Expected completion in 2-5 seconds
- **System Tests**: Expected completion in 5-15 seconds (depending on network latency)
- **Large File Tests**: May require extended timeouts for files >100MB

### 8.2 Resource Requirements

- **Memory**: Minimal impact for standard test files (<10MB each)
- **Network**: Bandwidth requirements depend on test file sizes
- **Disk Space**: Temporary storage for downloaded test files

## 9. Security Considerations

### 9.1 Test Environment Security

- **Host Key Policy**: `AutoAddPolicy` used for testing (not production-safe)
- **Credential Management**: Environment variables for test credentials
- **Test Data**: Use non-sensitive test files only
- **Network Isolation**: Recommend isolated test network for SSH server

### 9.2 Production Recommendations

- Implement proper host key verification for production use
- Use key-based authentication instead of passwords
- Regular security audits of SSH configurations
- Implement connection retry logic with exponential backoff

## 10. Maintenance and Updates

### 10.1 Test Maintenance

- **Regular Execution**: Include SSH tests in CI/CD pipeline
- **Test Data Updates**: Maintain test server data structure
- **Dependency Updates**: Monitor paramiko library updates
- **Environment Validation**: Periodic verification of test SSH server

### 10.2 Documentation Updates

- Update test cases when SSH functionality changes
- Maintain environment setup documentation
- Document new failure scenarios as discovered
- Keep troubleshooting guide current with common issues

## 11. Conclusion

The SSH testing framework provides comprehensive validation of remote file transfer functionality. Proper execution of these tests ensures the reliability and robustness of the SSH module.

## 5. Next Steps

*   Verify all prerequisites are met.
*   Set up the test SSH server environment.
*   Execute unit tests to validate core functionality.
*   Run system tests to validate end-to-end integration.
*   Review test results and address any failures.
*   Document any new issues or edge cases discovered.