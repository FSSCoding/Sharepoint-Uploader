# Technical Specification: SharePoint Folder Uploader CLI

## 1. Introduction

This document provides the technical details for the SharePoint Folder Uploader CLI. It covers the technology stack, architecture, key components, and implementation details necessary to build the tool as defined in the Functional Specification.

## 2. Technology Stack

-   **Programming Language**: Python 3.8+
-   **Key Libraries**:
    -   **CLI Framework**: `Typer` or `Click` for argument parsing and command structure.
    -   **CLI User Interface**: `Rich` for progress bars, formatted tables, and styled text.
    -   **Microsoft Graph API**: `MSAL (Microsoft Authentication Library) for Python` (`msal`) or `azure-identity` for authentication, and `httpx` or `requests` for API calls.
    -   **SSH/SCP/rsync**: `paramiko` for direct SSH implementation or the `subprocess` module to call system-level `rsync`/`scp` commands.
    -   **Configuration**: `python-dotenv` for loading `.env` files.
-   **Development Tools**:
    -   **Testing Framework**: `pytest`
    -   **Linter/Formatter**: `ruff`, `black`
    -   **Dependency Management**: `pip` with `requirements.txt`.

## 3. System Architecture

The application will be a monolithic CLI tool with a modular internal structure. The core logic will be separated into distinct components to handle authentication, remote file fetching, and the upload process.

### 3.1. Core Components

-   **`main.py`**: The entry point of the application. It will handle CLI argument parsing and orchestrate the overall workflow by calling the appropriate modules.
-   **`auth.py`**: Manages authentication with the Microsoft Graph API. It will acquire and refresh OAuth2 tokens using app-only (client credentials) flow.
-   **`config.py`**: Handles loading and validation of configuration from `.env` and `config.json` files.
-   **`ssh_copy.py`**: Manages the process of fetching remote directories using SSH (rsync/scp). It will handle connection, transfer, and error handling for the remote copy process.
-   **`uploader.py`**: The core component responsible for the upload logic. It will:
    -   Scan the source directory (local or temporary).
    -   Create corresponding folders in SharePoint.
    -   Handle both small file uploads and large, resumable file uploads.
    -   Manage the state of resumable uploads.
    -   Implement the retry logic for failed uploads.
-   **`state.py`**: Manages the persistence of the application's state, primarily for resumable uploads. It will read and write state information (e.g., upload session URLs, file offsets) to a file within the temporary directory.
-   **`progress.py`**: A dedicated module to encapsulate all `Rich` library interactions, providing a clean interface for displaying progress bars, tables, and status messages.
-   **`logger.py`**: Configures and provides a centralized logging instance for the application.

### 3.2. Data Flow

1.  **Initialization**: The `main.py` script parses CLI arguments and initializes the configuration from `config.py`.
2.  **Authentication**: The `auth.py` module is called to get a valid access token from Microsoft Graph.
3.  **Remote Fetch (if applicable)**: If `--use-ssh` is specified, `ssh_copy.py` is invoked to rsync the remote directory to the local temporary path.
4.  **Upload Orchestration**: The `uploader.py` module is called with the source path (local or temp) and target SharePoint path.
5.  **State Check**: The uploader checks the temporary directory for an existing state file to determine if it's a new or resumed session.
6.  **File Processing**: The uploader iterates through the source directory:
    -   For each sub-directory, it makes a Graph API call to create it in SharePoint if it doesn't exist.
    -   For each file, it determines whether to use a simple upload (small files) or a resumable upload session (large files).
    -   The `progress.py` module is updated continuously to reflect the current status.
7.  **Resumable Upload**:
    -   A `createUploadSession` request is sent to the Graph API.
    -   The file is read in chunks and sent via `PUT` requests to the `uploadUrl` returned by the session.
    -   The `state.py` module is updated after each successful chunk upload.
    -   In case of failure, the retry logic is triggered. If the session expires, a new one is created, and the upload is resumed from the last known offset.
8.  **Completion**: Once all files are processed, the temporary directory is cleaned up (unless `--keep-temp` is specified). A final status report is displayed to the user.

## 4. Configuration

-   **`.env` file**:
    -   `CLIENT_ID`: The Application (client) ID for the Azure AD App Registration.
    -   `TENANT_ID`: The Directory (tenant) ID.
    -   `CLIENT_SECRET`: The client secret for the App Registration.
    -   `SITE_ID`: The Microsoft Graph ID for the target SharePoint site.
    -   `DRIVE_ID`: The Microsoft Graph ID for the target Document Library (drive).
-   **`config.json` (optional)**:
    -   `chunk_size_mb`: The size of chunks for resumable uploads (in megabytes). Default: 10.
    -   `max_retries`: The maximum number of retries for a failed chunk upload. Default: 5.
    -   `post_delay_seconds`: The delay after each file upload. Default: 0.
    -   `temp_path`: The path to the temporary directory. Default: `./.upload_temp`.
    -   `log_file`: The path to the log file. Default: `upload.log`.

## 5. API Interaction (Microsoft Graph)

-   **Authentication**: `POST https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token`
-   **Create Folder**: `PATCH https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drives/{DRIVE_ID}/root:/{parent_path}:/children` with a `folder` object in the body.
-   **Small File Upload**: `PUT https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drives/{DRIVE_ID}/root:/{item_path}:/content`
-   **Create Resumable Session**: `POST https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drives/{DRIVE_ID}/root:/{item_path}:/createUploadSession`
-   **Upload Chunk**: `PUT {uploadUrl}` (from the session response) with `Content-Range` header.
-   **Check Upload Status**: `GET {uploadUrl}`
-   **Cancel Upload**: `DELETE {uploadUrl}`

## 6. Error Handling and Resilience

-   **Network Errors**: Use `httpx` or `requests` with built-in retry mechanisms for transient network errors.
-   **API Throttling**: Respect `Retry-After` headers from the Graph API. Implement exponential back-off for `429` and `5xx` status codes.
-   **Session Expiry**: If a chunk upload fails with a `401` or `404` on the `uploadUrl`, the `uploader` should attempt to create a new session and resume from the last successful offset.
-   **Graceful Shutdown**: Use the `signal` module to catch `SIGINT` and `SIGTERM`. The signal handler will set a flag that stops new operations and ensures the current state is flushed to disk before exiting.