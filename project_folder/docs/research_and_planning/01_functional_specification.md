# Functional Specification: SharePoint Folder Uploader CLI

## 1. Introduction

This document outlines the functional requirements for the SharePoint Folder Uploader CLI, a Python-based tool designed to upload local or remote folder structures to a SharePoint document library. The tool is intended to be robust, resumable, and provide rich user feedback, handling large data transfers and unstable network conditions gracefully.

## 2. Target Audience

The primary users of this tool are:
- System administrators
- IT professionals
- Developers
- Any user needing to automate folder uploads to SharePoint, especially from remote servers.

## 3. Core Features (Must-Have)

The CLI tool must provide the following core functionalities:

- **Authentication**: Securely authenticate with the Microsoft Graph API using app-only credentials.
- **Remote Data Fetching**: Fetch remote directories via SSH (using SCP/rsync) to a local temporary staging area.
- **Folder Upload**: Upload local folder structures (including those fetched remotely) to a specified path within a SharePoint document library.
- **File Handling**:
    - Upload small files directly.
    - Utilize chunked, resumable upload sessions for large files.
- **Resumability and State Management**:
    - Persist upload state (e.g., session URL, offset) to allow for resuming interrupted uploads.
    - Automatically re-create and resume upload sessions upon expiry.
- **Error Handling and Retries**:
    - Implement an automatic retry mechanism with exponential back-off for failed chunk uploads.
- **Folder Structure Replication**: Automatically create folders in SharePoint as needed to mirror the source directory structure.
- **User Feedback and Logging**:
    - Provide rich, real-time CLI feedback using the "Rich" library, including overall progress, per-file progress, ETA, and transfer rates.
    - Maintain robust logs of all operations, errors, and retries for diagnostic purposes.
- **Configuration**:
    - Load primary configuration (CLIENT_ID, TENANT_ID, CLIENT_SECRET, SITE_ID, DRIVE_ID) from a `.env` file.
    - Allow for optional configuration overrides via a `config.json` file.
- **Workspace Management**:
    - Automatically clean up the temporary folder upon successful completion of an upload, unless specified otherwise by the user.
- **Reporting and Manual Intervention**:
    - Report all upload successes and failures clearly to the user.
    - Allow for the manual retry of failed items.
- **Graceful Shutdown**: Ensure a graceful shutdown on receiving SIGINT/SIGTERM signals, flushing any in-flight session information to disk.
- **CLI Arguments**: Support a comprehensive set of command-line flags for controlling the tool's behavior, including: `remote-path`, `target-path`, `use-ssh`, `temp-path`, `chunk-size`, `max-retries`, `post-delay`, `verbose`, and `keep-temp`.

## 4. Advanced Features (Nice-to-Have)

The following features are desirable but not essential for the initial launch:

- **Post-Upload Validation**: Optionally validate successful uploads by fetching file metadata (e.g., size, hash) from SharePoint and comparing it against the source.
- **Configurable Delays**: Allow for a configurable pause after each file or batch of files to accommodate SharePoint's indexing process.
- **Supervisor Process**: Implement a supervisor loop to catch major network or API errors and attempt to resume the entire process after a configurable delay.

## 5. User Workflows

### 5.1. Initial Setup
1.  The user configures a `.env` file with their Microsoft Graph API credentials and SharePoint site/drive identifiers.
2.  Optionally, the user creates a `config.json` file to override default settings.

### 5.2. Local Folder Upload
1.  The user executes the tool, providing the path to a local source folder and the target path in SharePoint.
    -   Example: `main.py --remote-path /local/source/folder --target-path /Documents/Destination`
2.  The tool authenticates, reads the local folder structure, and begins the upload process.
3.  For each file and folder, it creates the corresponding item in SharePoint and uploads the file, showing progress and handling retries as needed.
4.  Upon completion, it reports the final status.

### 5.3. Remote Folder Upload (via SSH)
1.  The user executes the tool with the `--use-ssh` flag, providing remote server details and the target SharePoint path.
    -   Example: `main.py --remote-path user@host:/remote/source/folder --target-path /Documents/Destination --use-ssh`
2.  The tool authenticates with Microsoft Graph.
3.  It fetches the remote folder to a local temporary directory using rsync or scp.
4.  It then proceeds with the upload from the temporary directory as described in the local upload workflow.
5.  Finally, it cleans up the temporary folder and reports the status.

### 5.4. Resuming an Interrupted Upload
1.  The user re-runs the exact same command that was previously interrupted.
2.  The tool detects the existing state in the temporary folder.
3.  The remote fetcher (if applicable) resumes or re-synchronizes the source data.
4.  The uploader checks SharePoint for partially uploaded files and resumes chunked uploads from the last known offset.
5.  The process continues until completion.

### 5.5. Debugging
1.  The user runs the tool with the `--keep-temp` and/or `--verbose` flags to inspect logs and temporary files after an issue occurs.

## 6. User Interface Requirements

- **Command-Line Interface**:
    - All interactions with the tool will be through CLI arguments.
    - The tool must provide clear and comprehensive help messages.
- **In-Operation Feedback**:
    - Display informative status updates throughout the upload process.
    - Use clear progress bars, ETAs, and transfer rate metrics.
    - Log periodic "still alive" messages during long-running operations to indicate that the process has not stalled.
- **Error Reporting**:
    - Present clear and actionable error messages upon failure.
    - Provide guidance to the user on how to resolve common issues.