# User Guide - Report

**Original Report Date:** 2025-06-18
**Project Phase:** Documentation

## 1. Executive Summary

The SharePoint Uploader is a command-line interface (CLI) tool designed to facilitate the upload of files and directories from a local or remote (via SSH) source to a specified SharePoint document library. It supports large file uploads, resumable transfers, and flexible configuration options.

## 2. Key Accomplishments

*   **Installation**: Provided clear, step-by-step instructions for installing the tool and its dependencies.
*   **Configuration**: Detailed the three methods of configuration: JSON file, environment variables, and command-line arguments, including their order of precedence.
*   **Usage**: Offered comprehensive usage examples for basic local uploads and more advanced SSH-based remote uploads.
*   **Command-Line Options**: Included a complete reference table for all available command-line arguments.
*   **Features**: Highlighted key features such as resumable uploads, SSH integration, rich progress display, and graceful shutdown.
*   **Troubleshooting**: Provided a troubleshooting guide for common issues like authentication errors and SSH connection failures.

## 3. Challenges and Resolutions

No challenges were identified.

## 4. Final Status

The user guide is complete and provides all necessary information for users to install, configure, and use the SharePoint Uploader CLI tool effectively.

## 5. Next Steps

No next steps were identified.
The CLI can be configured via a JSON file, environment variables, or command-line arguments. The order of precedence is:

1.  Command-line arguments
2.  JSON configuration file
3.  Environment variables

### 3.1. JSON Configuration File

Create a `config.json` file with the following structure:

```json
{
  "SP_DRIVE_ID": "your_sharepoint_drive_id",
  "SP_CLIENT_ID": "your_azure_ad_client_id",
  "SP_TENANT_ID": "your_azure_ad_tenant_id",
  "SP_CLIENT_SECRET": "your_azure_ad_client_secret",
  "SSH_HOST": "your_ssh_host",
  "SSH_USER": "your_ssh_username",
  "SSH_KEY_PATH": "/path/to/your/ssh/private/key"
}
```

### 3.2. Environment Variables

Alternatively, set the following environment variables:

-   `DRIVE_ID`
-   `CLIENT_ID`
-   `TENANT_ID`
-   `CLIENT_SECRET`
-   `SSH_HOST`
-   `SSH_USER`
-   `SSH_KEY_PATH`

## 4. Usage

The main command is `main.py`.

### Basic Usage

**Upload a local directory:**

```bash
python main.py --source /path/to/local/directory --target "Shared Documents/My Target Folder"
```

**Upload a single local file:**

```bash
python main.py --source /path/to/local/file.txt --target "Shared Documents/My Target Folder"
```

### SSH Usage

To upload from a remote server, use the `--use-ssh` flag and provide SSH credentials.

```bash
python main.py \
  --source /path/to/remote/directory \
  --target "Shared Documents/Destination" \
  --use-ssh \
  --ssh-host your_ssh_host \
  --ssh-user your_ssh_user \
  --ssh-key /path/to/your/ssh/key
```

### All Command-Line Options

| Option            | Description                                                               |
| ----------------- | ------------------------------------------------------------------------- |
| `--source`        | Local source directory or remote path (`user@host:/path`). (Required)     |
| `--target`        | Target SharePoint folder path. (Required)                                 |
| `--config-file`   | Path to a JSON config file.                                               |
| `--use-ssh`       | Flag to indicate the source is a remote path.                             |
| `--ssh-host`      | SSH host.                                                                 |
| `--ssh-port`      | SSH port (default: 22).                                                   |
| `--ssh-user`      | SSH username.                                                             |
| `--ssh-pass`      | SSH password (not recommended).                                           |
| `--ssh-key`       | Path to SSH private key.                                                  |
| `--drive-id`      | SharePoint Drive ID.                                                      |
| `--client-id`     | Azure AD App Client ID.                                                   |
| `--tenant-id`     | Azure AD Tenant ID.                                                       |
| `--client-secret` | Azure AD App Client Secret.                                               |
| `--verbose`       | Enable verbose logging.                                                   |
| `--keep-temp`     | Do not delete temporary files after completion.                           |
| `--temp-path`     | Custom temporary directory path.                                          |
| `--chunk-size`    | Upload chunk size in MB.                                                  |
| `--max-retries`   | Maximum number of retries for a failed chunk.                             |
| `--post-delay`    | Delay in seconds after each file upload.                                  |

## 5. Features

-   **Resumable Uploads**: If an upload is interrupted, the CLI will automatically resume from where it left off the next time it's run for the same file. State is stored in a `.state.json` file next to the source file.
-   **SSH Integration**: Fetch files and directories from a remote server securely via SSH.
-   **Rich Progress Display**: A detailed progress bar shows the status of individual files and the overall upload process.
-   **Graceful Shutdown**: Press `Ctrl+C` to safely interrupt the process. The current state will be saved for resumption.

## 6. Troubleshooting

-   **Authentication Errors**: Ensure your `client_id`, `tenant_id`, and `client_secret` are correct and that the Azure AD application has the necessary `Files.ReadWrite.All` permissions for SharePoint.
-   **SSH Connection Failed**: Verify your SSH host, user, and key path. Ensure the remote server is accessible.
-   **File Not Found**: Double-check the source path.