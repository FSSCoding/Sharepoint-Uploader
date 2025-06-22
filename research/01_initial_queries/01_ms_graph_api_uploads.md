# Research Area 1: Microsoft Graph API for SharePoint File Uploads

This research area focuses on understanding the core mechanics of interacting with the SharePoint REST API via Microsoft Graph for the purpose of file and folder manipulation.

## 🎯 Key Research Questions

1.  **Authentication:**
    *   What is the definitive process for establishing app-only (daemon) authentication using MSAL (`azure-identity` or `msal-python`)?
    *   What are the exact permissions (`Sites.ReadWrite.All`, `Files.ReadWrite.All`) required, and how are they consented to in Azure AD?
    *   How should tokens be managed (acquired, cached, refreshed) throughout the application's lifecycle?

2.  **Folder & Item Management:**
    *   How do you check for the existence of a folder or file at a specific path in a SharePoint document library?
    *   What is the API call to create a new folder?
    *   How do you resolve a SharePoint site/drive ID from a user-friendly name or URL?

3.  **Small File Uploads:**
    *   What is the API endpoint and method for uploading files considered "small" (e.g., < 4MB)?
    *   What are the request headers and body structure for a simple `PUT` upload?

4.  **Large File Uploads (Resumable Sessions):**
    *   What is the precise workflow for creating an `uploadSession` for a large file?
    *   How is the file uploaded in chunks? What are the required headers (e.g., `Content-Range`) for each chunk request?
    *   How do you query the status of an ongoing upload session to determine the next expected byte offset?
    *   What is the process for completing or canceling an upload session?

5.  **Session & Error Handling:**
    *   How does the API signal that an `uploadSession` has expired? What is the specific error code or message?
    *   What is the recommended strategy for resuming after a session expiry? (i.e., create a new session and query for offset, or does the old URL become valid again?)
    *   What are the common transient error codes (e.g., `503 Service Unavailable`, `429 Too Many Requests`) and the recommended retry strategies (e.g., respecting `Retry-After` headers)?

## 📚 Potential Sources

*   Official Microsoft Graph API Documentation (v1.0 and beta endpoints).
*   Microsoft Authentication Library (MSAL) for Python documentation.
*   GitHub examples for `azure-identity` and `msal-python`.
*   Stack Overflow discussions related to Graph API file uploads.
*   Blog posts from developers who have implemented similar solutions.