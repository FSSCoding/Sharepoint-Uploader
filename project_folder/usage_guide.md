# Usage Guide - Report

**Original Report Date:** 6/18/2025
**Project Phase:** Development

## 1. Executive Summary

This guide provides comprehensive instructions for using the SharePoint Uploader CLI to transfer files and directories to SharePoint document libraries.

## 2. Key Accomplishments

*   **Configuration Required**
    *   Your application needs to be configured with:
        *   **Tenant ID**: Your Azure AD tenant identifier
        *   **Client ID**: Your registered application's client ID
        *   **Site ID**: Your SharePoint site identifier
        *   **Drive ID**: Your SharePoint document library drive ID
        *   **Client Secret**: Your application's authentication secret
*   **Quick Start**
    *   **1. Environment Setup**
        *   Copy the environment template and configure your credentials:
            ```bash
            cp env_template.txt .env
            # Edit .env with your actual values
            ```
    *   **2. Basic File Upload**
        ```bash
        # Upload a single file
        python main.py --upload-only myfile.pdf
        
        # Upload to a specific SharePoint folder
        python main.py --upload-only myfile.pdf --sharepoint-folder "Documents/Reports"
        ```
    *   **3. SSH + Upload Workflow**
        ```bash
        # Download from remote server and upload to SharePoint
        python main.py --use-ssh --remote-path /path/to/remote/files --ssh-host server.com --ssh-user username --upload-to-sharepoint
        ```
    *   **4. Compression Workflow**
        ```bash
        # Download, compress, then upload
        python main.py --use-ssh --remote-path /path/to/remote/files --ssh-host server.com --ssh-user username --compress --upload-to-sharepoint
        ```
*   **Command Reference**
    *   **Core Options**
        *   `--config CONFIG` - Path to configuration file (default: config.json)
        *   `--verbose` - Enable detailed logging
        *   `--help` - Show all available options
    *   **SSH Options**
        *   `--use-ssh` - Enable SSH transfer mode
        *   `--remote-path PATH` - Remote directory/file path
        *   `--ssh-host HOST` - SSH server hostname
        *   `--ssh-user USER` - SSH username
        *   `--ssh-key PATH` - Path to SSH private key
        *   `--ssh-port PORT` - SSH port (default: 22)
    *   **Compression Options**
        *   `--compress` - Compress files before upload
        *   `--compression-level N` - Compression level 0-9 (default: 6)
        *   `--keep-original` - Keep original files after compression
    *   **Upload Options**
        *   `--upload-to-sharepoint` - Upload processed files to SharePoint
        *   `--upload-only FILE` - Upload existing file (skip SSH/compression)
        *   `--sharepoint-folder PATH` - Target SharePoint folder
*   **Configuration**
    *   **Environment Variables (.env)**
        ```bash
        TENANT_ID=your-tenant-id
        CLIENT_ID=your-client-id
        CLIENT_SECRET=your-client-secret
        SITE_ID=your-site-id
        DRIVE_ID=your-drive-id
        SHAREPOINT_HOST=graph.microsoft.com
        SCOPES=https://graph.microsoft.com/.default
        ```
    *   **Configuration File (config.json)**
        *   Alternatively, use a JSON configuration file:
            ```json
            {
              "TENANT_ID": "your-tenant-id",
              "CLIENT_ID": "your-client-id",
              "CLIENT_SECRET": "your-client-secret",
              "SITE_ID": "your-site-id",
              "DRIVE_ID": "your-drive-id",
              "SHAREPOINT_HOST": "graph.microsoft.com",
              "SCOPES": "https://graph.microsoft.com/.default"
            }
            ```
*   **Examples**
    *   **Example 1: Simple File Upload**
        ```bash
        python main.py --upload-only "report.pdf" --sharepoint-folder "Documents/Reports"
        ```
    *   **Example 2: SSH Download + Upload**
        ```bash
        python main.py \
          --use-ssh \
          --remote-path "/var/backups/daily" \
          --ssh-host "backup.company.com" \
          --ssh-user "admin" \
          --ssh-key "~/.ssh/id_rsa" \
          --upload-to-sharepoint \
          --sharepoint-folder "Backups/Daily"
        ```
    *   **Example 3: Compressed Archive Upload**
        ```bash
        python main.py \
          --use-ssh \
          --remote-path "/var/logs" \
          --ssh-host "server.com" \
          --ssh-user "user" \
          --compress \
          --compression-level 9 \
          --upload-to-sharepoint \
          --sharepoint-folder "Archives/Logs"
        ```
*   **Security Best Practices**
    1.  **Never commit credentials** to version control
    2.  **Use environment variables** for sensitive configuration
    3.  **Restrict file permissions** on `.env` files: `chmod 600 .env`
    4.  **Use SSH keys** instead of passwords when possible
    5.  **Regularly rotate** client secrets and access keys

## 3. Challenges and Resolutions

*   **Troubleshooting**
    *   **Authentication Issues**
        *   Verify your Azure AD application has `Files.ReadWrite.All` permissions
        *   Ensure your `CLIENT_ID`, `TENANT_ID`, and `CLIENT_SECRET` are correct
        *   Check that your application is properly registered in Azure AD
    *   **Upload Failures**
        *   Verify your `SITE_ID` and `DRIVE_ID` are correct
        *   Check SharePoint permissions for your application
        *   Ensure target folders exist or can be created
    *   **SSH Connection Issues**
        *   Test SSH connectivity: `ssh user@host`
        *   Verify SSH key permissions: `chmod 600 ~/.ssh/id_rsa`
        *   Check firewall and network connectivity
    *   **Large File Issues**
        *   Monitor available disk space for temporary files
        *   Consider using compression for large directories
        *   Check SharePoint file size limits

## 4. Final Status

*   **Logging**
    *   The application creates detailed logs in the `logs/` directory:
        *   `sharepoint-uploader.log` - Main application log
        *   Use `--verbose` for additional console output

## 5. Next Steps

*   **Support**
    *   For issues or questions:
        1.  Check the logs for detailed error messages
        2.  Verify your configuration and credentials
        3.  Test individual components (SSH, authentication, upload) separately
        4.  Refer to the deployment guide for setup assistance