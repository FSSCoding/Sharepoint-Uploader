# Research Area 2: Remote Directory Transfer via SSH

This research area covers the requirements for securely and efficiently transferring a directory from a remote server to the local machine where the uploader script is running.

## 🎯 Key Research Questions

1.  **Choosing the Right Tool (SCP vs. rsync):**
    *   What are the pros and cons of using `scp` versus `rsync` for this project's use case?
    *   Does `rsync` offer significant advantages for resumability or efficiency when fetching the remote directory?
    *   How is `rsync` typically used over SSH?

2.  **Python Implementation:**
    *   What is the most robust Python library for executing remote commands and file transfers over SSH? (`paramiko`, `fabric`, or using the `subprocess` module to call the system's `scp`/`rsync` client).
    *   What are the best practices for handling SSH authentication (password vs. key-based)?
    *   How can the transfer be made resumable? If the local script is stopped and restarted, can the remote transfer pick up where it left off? (This is a key feature of `rsync`).

3.  **Error Handling and State Management:**
    *   How can the Python script detect and handle common SSH errors (e.g., connection refused, authentication failure, host key mismatch)?
    *   How can the script monitor the progress of the remote transfer?
    *   What state needs to be saved locally to enable resumability of the directory fetch?

4.  **Integration with Main Application:**
    *   How will the SSH transfer module be triggered (e.g., by the `--use-ssh` flag)?
    *   How will it report its status (progress, success, failure) back to the main application logic?
    *   Where will the fetched files be stored temporarily?

## 📚 Potential Sources

*   Documentation for `paramiko` and `fabric` libraries.
*   Manual pages (`man`) for `rsync` and `scp`.
*   Tutorials and articles on Python SSH automation.
*   Stack Overflow questions comparing `paramiko`, `fabric`, and `subprocess`.
*   Examples of using `rsync` over SSH for directory synchronization.