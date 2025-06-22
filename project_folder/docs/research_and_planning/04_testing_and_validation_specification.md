# Testing and Validation Specification: SharePoint Folder Uploader CLI

## 1. Introduction

This document defines the testing strategy and validation criteria for the SharePoint Folder Uploader CLI. The goal is to ensure the tool is reliable, performs correctly under various conditions, and meets all specified requirements.

## 2. Testing Scope

Testing will cover the following areas:
-   **Unit Testing**: Individual components (modules, functions, classes) will be tested in isolation.
-   **Integration Testing**: Interactions between components (e.g., uploader and auth module) and with external services (Microsoft Graph API, SSH) will be tested.
-   **End-to-End (E2E) Testing**: The entire application workflow will be tested from the command line.
-   **Performance Testing**: The tool's ability to handle large files and folders will be assessed.
-   **Stress Testing**: The tool's resilience to network failures and API errors will be tested.

## 3. Unit Testing

Unit tests will be written using the `pytest` framework and will focus on the logic within each core module. Mocks will be used extensively to isolate the code under test from external dependencies.

-   **`auth.py`**:
    -   Test successful token acquisition.
    -   Test token caching and refresh logic.
    -   Test handling of authentication failures from the API.
-   **`config.py`**:
    -   Test loading of `.env` variables.
    -   Test overriding of defaults with `config.json`.
    -   Test validation of configuration values.
-   **`uploader.py`**:
    -   Test the logic for differentiating between small and large file uploads.
    -   Test the chunking mechanism for large files.
    -   Test the retry logic with mocked API failures.
    -   Test the state management for resumable uploads.
-   **`ssh_copy.py`**:
    -   Test the correct construction of `rsync`/`scp` commands.
    -   Test the parsing of output from the `subprocess`.
-   **`utils.py`**:
    -   Test any utility functions for path manipulation, file size calculation, etc.

## 4. Integration Testing

Integration tests will verify the interactions between modules and with live or simulated external services.

-   **Graph API Integration**:
    -   Test creating a folder in a live SharePoint site.
    -   Test uploading a small file.
    -   Test creating a resumable upload session.
    -   Test uploading a few chunks of a file to a resumable session.
    -   These tests will require a dedicated test SharePoint site and app registration.
-   **SSH Integration**:
    -   Test fetching a small directory from a test SSH server (e.g., a Docker container).
    -   Verify that `rsync` is used correctly and that files are transferred to the local temp directory.

## 5. End-to-End (E2E) Testing

E2E tests will simulate real user workflows by executing the main script from the command line with various arguments.

-   **Scenario 1: Local Upload (Small Files)**
    -   Upload a directory with a few small text files.
    -   **Validation**: Verify files and folders are created correctly in SharePoint. Verify the temp directory is cleaned up.
-   **Scenario 2: Local Upload (Large File)**
    -   Upload a directory containing a multi-gigabyte file (e.g., 1-2 GB for testing).
    -   **Validation**: Verify the file is uploaded successfully. Monitor progress indicators.
-   **Scenario 3: Remote Upload (SSH)**
    -   Fetch a directory from a test SSH server and upload it.
    -   **Validation**: Verify the end-to-end process completes successfully.
-   **Scenario 4: Resumable Upload**
    -   Start a large file upload and interrupt it (e.g., with Ctrl+C).
    -   Re-run the same command.
    -   **Validation**: Verify the upload resumes from the point of interruption and completes successfully.
-   **Scenario 5: Configuration Flags**
    -   Test the behavior of key CLI flags like `--keep-temp`, `--verbose`, and `--chunk-size`.
    -   **Validation**: Verify the application's behavior changes as expected.

## 6. Performance and Stress Testing

-   **Large Scale Test**:
    -   Upload a directory containing a very large file (10GB+).
    -   Upload a directory containing thousands of small files.
    -   **Validation**: Monitor memory usage, CPU load, and overall transfer time. Ensure the application remains stable.
-   **Failure Simulation**:
    -   Use tools like `toxiproxy` or custom mocks to simulate network dropouts, API timeouts, and `429`/`503` errors from the Graph API during a large upload.
    -   **Validation**: Verify that the retry and resume mechanisms handle these failures gracefully without data corruption.
-   **Graceful Shutdown Test**:
    -   Send a `SIGINT` (Ctrl+C) signal during a large upload.
    -   **Validation**: Verify that the application exits cleanly and that the state file is correctly written, allowing for a successful resume.

## 7. Success Criteria (Validation)

The project will be considered successfully tested and validated when:
-   All unit tests pass with a target code coverage of >80%.
-   All integration and E2E test scenarios pass consistently.
-   The tool can successfully upload a 10GB+ file without crashing.
-   The tool can successfully resume an interrupted 10GB+ upload.
-   The tool gracefully handles simulated network and API errors.
-   Post-upload validation (manual or scripted) confirms that the file count and total size in SharePoint match the source directory.
-   (Optional) Post-upload validation using file hashes confirms data integrity.