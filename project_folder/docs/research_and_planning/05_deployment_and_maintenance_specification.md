# Deployment and Maintenance Specification: SharePoint Folder Uploader CLI

## 1. Introduction

This document outlines the procedures for deploying, configuring, and maintaining the SharePoint Folder Uploader CLI. It provides guidance for system administrators and users on how to get the tool running and how to handle future updates and troubleshooting.

## 2. Deployment

### 2.1. Prerequisites

-   Python 3.8 or higher.
-   Access to a command line/terminal.
-   `pip` for installing dependencies.
-   For remote uploads: A configured SSH client and network access to the remote server.
-   For all uploads: Network access to Microsoft 365 services.

### 2.2. Installation Steps

1.  **Clone the Repository**:
    ```bash
    git clone <repository_url>
    cd sharepoint-folder-uploader-cli
    ```
2.  **Install Dependencies**:
    It is highly recommended to use a Python virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

### 2.3. Configuration

1.  **Create `.env` file**:
    Create a file named `.env` in the root directory of the project and populate it with the necessary credentials and IDs:
    ```dotenv
    CLIENT_ID="your-application-client-id"
    TENANT_ID="your-directory-tenant-id"
    CLIENT_SECRET="your-client-secret"
    SITE_ID="your-sharepoint-site-id"
    DRIVE_ID="your-document-library-drive-id"
    ```
2.  **Optional `config.json`**:
    To override default behaviors, create a `config.json` file in the root directory. For example:
    ```json
    {
      "chunk_size_mb": 20,
      "max_retries": 10,
      "temp_path": "/path/to/custom/temp"
    }
    ```

## 3. Usage

The tool is run from the command line.

-   **Basic Local Upload**:
    ```bash
    python main.py --remote-path /path/to/local/source --target-path /Target/SharePoint/Folder
    ```
-   **Basic Remote Upload**:
    ```bash
    python main.py --remote-path user@host:/path/to/remote/source --target-path /Target/SharePoint/Folder --use-ssh
    ```
-   **Getting Help**:
    ```bash
    python main.py --help
    ```

## 4. Maintenance

### 4.1. Logging and Monitoring

-   **Log Files**: The application generates a log file (e.g., `upload.log`) in the root directory. This file should be the first point of reference for troubleshooting failed uploads.
-   **Verbose Mode**: For detailed, real-time diagnostics, run the tool with the `--verbose` flag. This will print debug-level information to the console.
-   **Monitoring**: For long-running automated jobs, system administrators should monitor the exit code of the script. A non-zero exit code indicates a failure.

### 4.2. Updating the Application

To update to a new version:
1.  Navigate to the project directory.
2.  Pull the latest changes from the repository:
    ```bash
    git pull origin main
    ```
3.  Update the dependencies in case they have changed:
    ```bash
    pip install -r requirements.txt
    ```

### 4.3. Common Issues and Troubleshooting

-   **Authentication Errors**:
    -   Verify that the `CLIENT_ID`, `TENANT_ID`, and `CLIENT_SECRET` in the `.env` file are correct.
    -   Ensure the Azure AD App Registration has the required API permissions (`Sites.ReadWrite.All`, `Files.ReadWrite.All`) and that admin consent has been granted.
-   **File/Folder Not Found Errors**:
    -   Double-check the `SITE_ID` and `DRIVE_ID` in the `.env` file.
    -   Ensure the source path (local or remote) is correct and accessible.
-   **SSH Connection Failures**:
    -   Verify that the remote host is reachable.
    -   Ensure your SSH key is correctly configured and loaded in your SSH agent.
    -   Test the connection manually with `ssh user@host`.
-   **Uploads Failing Repeatedly**:
    -   Check the log file for specific error messages from the Microsoft Graph API.
    -   Look for network connectivity issues (e.g., firewalls blocking access to `graph.microsoft.com`).
    -   If using the `--keep-temp` flag, inspect the `.upload_state.json` file to understand the state of the upload.

## 5. Backup and Recovery

-   **State File**: The primary mechanism for recovery from failed uploads is the state file (`.upload_state.json`) located in the temporary directory. As long as this file is intact, re-running the command will resume the upload.
-   **No Data Backup**: The tool itself does not perform backups of the source data. It is a transfer utility. Backups of the source and destination are the user's responsibility.