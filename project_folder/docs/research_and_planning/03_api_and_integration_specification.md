# API and Integration Specification: SharePoint Folder Uploader CLI

## 1. Introduction

This document details the integration points between the SharePoint Folder Uploader CLI and external services. It specifies the APIs to be used, data formats, and protocols for communication.

## 2. Microsoft Graph API Integration

The primary external integration is with the Microsoft Graph API, which facilitates all interactions with SharePoint Online.

### 2.1. Authentication

-   **Method**: OAuth 2.0 Client Credentials Grant Flow (App-Only Authentication).
-   **Endpoint**: `https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token`
-   **Request Body**:
    -   `client_id`: The application's client ID.
    -   `client_secret`: The application's client secret.
    -   `scope`: `https://graph.microsoft.com/.default`
    -   `grant_type`: `client_credentials`
-   **Permissions**: The associated Azure AD App Registration must be granted the following application permissions:
    -   `Sites.ReadWrite.All`
    -   `Files.ReadWrite.All`

### 2.2. API Endpoints

All endpoints are relative to the base URL: `https://graph.microsoft.com/v1.0`

-   **Create Folder**:
    -   **Endpoint**: `PATCH /sites/{SITE_ID}/drives/{DRIVE_ID}/root:/{parent_path}:/children`
    -   **Method**: `PATCH`
    -   **Body**: `{ "name": "{folder_name}", "folder": {} }`
    -   **Notes**: This will create the folder if it doesn't exist.

-   **Small File Upload (< 4MB)**:
    -   **Endpoint**: `PUT /sites/{SITE_ID}/drives/{DRIVE_ID}/root:/{parent_path}/{file_name}:/content`
    -   **Method**: `PUT`
    -   **Headers**: `Content-Type: application/octet-stream`
    -   **Body**: Raw file content.

-   **Create Resumable Upload Session (>= 4MB)**:
    -   **Endpoint**: `POST /sites/{SITE_ID}/drives/{DRIVE_ID}/root:/{parent_path}/{file_name}:/createUploadSession`
    -   **Method**: `POST`
    -   **Body**: `{ "item": { "@microsoft.graph.conflictBehavior": "replace" } }`
    -   **Success Response**: A JSON object containing the `uploadUrl` and `expirationDateTime`.

-   **Upload File Chunk**:
    -   **Endpoint**: The `uploadUrl` obtained from the `createUploadSession` response.
    -   **Method**: `PUT`
    -   **Headers**:
        -   `Content-Length`: The size of the chunk in bytes.
        -   `Content-Range`: `bytes {start_byte}-{end_byte}/{total_bytes}`
    -   **Body**: The raw bytes of the file chunk.

-   **Check Upload Status**:
    -   **Endpoint**: The `uploadUrl`.
    -   **Method**: `GET`
    -   **Success Response**: A JSON object containing `expirationDateTime` and `nextExpectedRanges`.

-   **Delete Upload Session**:
    -   **Endpoint**: The `uploadUrl`.
    -   **Method**: `DELETE`
    -   **Notes**: Used to cancel an in-progress resumable upload.

### 2.3. Error Handling

The application must handle the following HTTP status codes from the Graph API:
-   `401 Unauthorized`: The access token is invalid or expired. The tool should attempt to refresh the token.
-   `404 Not Found`: Can occur on a chunk upload if the session has expired. The tool should create a new session and resume.
-   `429 Too Many Requests`: The application is being throttled. The tool must respect the `Retry-After` header and wait the specified duration before retrying.
-   `500 Internal Server Error`, `503 Service Unavailable`: Transient server-side errors. The tool should use an exponential back-off strategy for retries.

## 3. SSH Integration (Remote Directory Fetch)

When the `--use-ssh` flag is active, the tool must integrate with a remote server to fetch the source directory.

-   **Protocol**: Secure Shell (SSH).
-   **Method**: The tool will use the `rsync` utility over SSH for efficient and resumable file transfers. If `rsync` is not available, it will fall back to `scp`.
-   **Implementation**: The `subprocess` module in Python will be used to execute the command-line utilities.
    -   **Example `rsync` command**:
        ```bash
        rsync -avz --partial --progress -e "ssh -i /path/to/key" user@host:/remote/source/folder/ /local/temp/path/
        ```
-   **Authentication**:
    -   The primary method should be SSH key-based authentication. The user is responsible for ensuring their SSH agent or key configuration is set up correctly.
    -   Password-based authentication is not recommended and will not be directly supported by the tool's logic.
-   **Data Flow**:
    1.  The tool constructs the appropriate `rsync` or `scp` command.
    2.  It executes the command using `subprocess.run()`.
    3.  It monitors the standard output/error streams to check for transfer progress and errors.
    4.  The remote files are copied into the local temporary directory, which then becomes the source for the SharePoint upload process.

## 4. Local File System Integration

The tool interacts with the local file system for several purposes:

-   **Source Files**: Reading the source directory and files when not using the SSH fetch feature.
-   **Temporary Directory**:
    -   **Location**: Defaults to a sub-directory (e.g., `.upload_temp`) in the current working directory. Can be overridden by the user.
    -   **Contents**:
        -   Staging area for files fetched via SSH.
        -   A state file (e.g., `upload_state.json`) that persists the status of resumable uploads.
-   **Configuration Files**:
    -   Reading the `.env` file for credentials.
    -   Reading the `config.json` file for optional settings.
-   **Log File**: Writing logs to a file (e.g., `upload.log`).