# 🚀 Project Blueprint
> **Instructions**: Fill out the sections below with your project details, then feed this entire document to the Primary Orchestrator to begin autonomous development.
---
## 🎯 Project Goal & Vision
<!-- PASTE YOUR PROJECT DESCRIPTION HERE -->
<!-- Describe what you want to build, the problem it solves, and your vision for the final product -->
**Project Name**: SharePoint Folder Uploader CLI
**Project Description**:
```
A Python CLI tool that can upload any local or remote folder to a SharePoint document library using Microsoft Graph. It must:
* Run via SSH (or locally) and pull remote directories into a portable temp area
* Handle multi-gigabyte transfers (up to 10 GB+) with full resume capability
* Provide rich CLI feedback (using Rich) and robust logging
* Recover gracefully from network dropouts, API timeouts and session expiries
* Validate success, report failures and allow manual retry
All configuration (credentials, endpoints, chunk sizes, retry policies) lives in a `.env` or optional `config.json`, and the entire temp/cache folder is created next to the running script for portability.
```
**Target Users**:
```
System administrators, IT professionals, developers, or any user needing to automate folder uploads to SharePoint, potentially from remote servers.
```
**Core Value Proposition**:
```
Provides a robust, resumable, and automated solution for transferring large local or remote folder structures to SharePoint, minimizing manual effort and ensuring data integrity even with unstable network conditions.
```
---
## 🛠️ Technical Requirements
**Technology Stack** (if you have preferences):
```
Frontend: N/A (CLI tool)
Backend: Python
Database: N/A (uses local file system for temp/cache and state persistence)
APIs/Integrations: Microsoft Graph API
Deployment: CLI application, runnable via SSH or locally
Libraries: Rich (for CLI feedback), MSAL/azure-identity (for auth), libraries for SCP/rsync (e.g., paramiko for SSH, subprocess for rsync)
```
**Platform Targets**:
- [ ] Web Application
- [ ] Mobile App (iOS/Android)  
- [ ] Desktop Application
- [ ] API/Service
- [x] CLI Tool
- [ ] Other: ___________
**Performance Requirements**:
```
- Handle multi-gigabyte transfers (up to 10 GB+).
- Recover gracefully from network dropouts, API timeouts, and session expiries.
- Efficient chunked uploads for large files.
- Resume capability to avoid re-uploading entire files/folders.
```
---
## 📋 Functional Requirements
**Core Features** (Must-Have):
```
- Authenticate with Microsoft Graph using app-only credentials.
- Fetch remote directories via SSH (SCP/rsync) to a local temporary area.
- Upload local folder structures (including those fetched remotely) to a specified SharePoint document library path.
- Handle small file uploads directly.
- Handle large file uploads using chunked/resumable sessions.
- Persist upload state (session URL, offset) for resumability.
- Automatic retry mechanism with exponential back-off for chunk uploads.
- Re-create upload session and resume on session expiry.
- Create folders in SharePoint as needed to replicate the source structure.
- Provide rich CLI feedback using "Rich" (overall progress, per-file progress, ETA, transfer rate).
- Robust logging of operations, errors, and retries.
- Configuration via `.env` file (CLIENT_ID, TENANT_ID, CLIENT_SECRET, SITE_ID, DRIVE_ID).
- Optional configuration overrides via `config.json`.
- Automatic cleanup of temporary folder on full success (unless specified otherwise).
- Report upload successes and failures.
- Allow manual retry of failed items (implied by "report failures and allow manual retry").
- Graceful shutdown on SIGINT/SIGTERM, flushing in-flight session info.
- CLI flags for: `remote-path`, `target-path`, `use-ssh`, `temp-path`, `chunk-size`, `max-retries`, `post-delay`, `verbose`, `keep-temp`.
```
**Advanced Features** (Nice-to-Have):
```
- Post-upload validation by fetching file metadata (size/hash) - "optionally fetch file metadata".
- Configurable pause after each file or batch to allow SharePoint indexing.
- Supervisor loop to catch major network/API errors and attempt resume after a delay.
```
**User Workflows**:
```
1. Setup: User configures `.env` with Microsoft Graph API credentials and SharePoint site/drive IDs. Optionally creates `config.json` for overrides.
2. Local Upload: User runs `main.py --remote-path /local/source/folder --target-path /Documents/Destination`.
   - Tool authenticates, reads local folder structure.
   - For each file/folder:
     - Creates folder in SharePoint if it doesn't exist.
     - Uploads file (small or large resumable).
     - Shows progress, handles retries.
   - Cleans up temp (if applicable, though less critical for local). Reports status.
3. Remote Upload via SSH: User runs `main.py --remote-path user@host:/remote/source/folder --target-path /Documents/Destination --use-ssh`.
   - Tool authenticates with MS Graph.
   - Fetches remote folder to local temp path using rsync/scp.
   - Proceeds with upload from temp path as in Local Upload workflow.
   - Cleans up temp folder. Reports status.
4. Resuming Interrupted Upload: User re-runs the same command after an interruption.
   - Tool detects existing state in temp folder.
   - Remote fetcher (if applicable) resumes or re-syncs based on partial data.
   - Uploader checks SharePoint for existing items and resumes chunked uploads from the last known offset.
   - Continues until completion.
5. Debugging: User runs with `--keep-temp` and/or `--verbose` to inspect logs and temporary files after an issue.
```
---
## 🎨 Design & User Experience
**Design Preferences**:
```
CLI tool with rich, informative feedback using the "Rich" Python library.
Clear progress bars for overall transfer and individual file chunks.
Display ETA and transfer rates.
Robust logging for diagnostics.
```
**User Interface Requirements**:
```
- Clear CLI arguments and help messages.
- Informative status updates during operation.
- Clear error messages and guidance on failure.
- Periodic "still alive" log entries during long operations.
```
---
## 🔌 Integration Requirements
**External Services**:
```
- Microsoft Graph API (for SharePoint interaction)
- Remote server via SSH (for SCP/rsync operations if `--use-ssh` is active)
```
**Data Sources**:
```
- Local file system (for source files if not using SSH)
- Remote file system (via SSH, if specified)
- `.env` file for credentials and core configuration
- `config.json` (optional) for configuration overrides
- Local temporary directory for staging remote files and persisting upload state
```
---
## 🛡️ Security & Compliance
**Security Requirements**:
```
- Securely handle Microsoft Graph API credentials (CLIENT_ID, TENANT_ID, CLIENT_SECRET) from `.env`.
- Use secure protocols for remote file transfer (SSH keys recommended for rsync/scp).
- Ensure app-only permissions are correctly scoped (`Files.ReadWrite.All`, `Sites.ReadWrite.All`).
```
**Data Privacy**:
```
- Temporary files and state are stored locally in a user-specified or default temp path.
- No explicit requirements beyond handling credentials securely and transferring specified data.
```
---
## 📈 Success Criteria
**Launch Criteria** (When is this project "complete"?):
```
- All core features implemented and thoroughly tested.
- Successful end-to-end transfers of small and multi-gigabyte (e.g., 10GB+) folders, both local and remote (via SSH).
- Demonstrated resume capability after simulated network dropouts, API timeouts, and session expiries.
- Graceful handling of SIGINT/SIGTERM signals.
- Configuration via `.env` and `config.json` is functional.
- CLI flags operate as specified.
- Rich progress reporting and logging are functional and informative.
- Temporary files are managed correctly (created, used, cleaned up or kept as specified).
- Basic usage documentation (covering setup, env vars, CLI options, failure modes) is available.
- Validation of success and reporting of failures is implemented.
```
**Key Metrics**:
```
- Successful upload completion rate for various file sizes and quantities.
- Time taken to resume an interrupted multi-gigabyte upload.
- Robustness: Number of unhandled exceptions or crashes during stress testing (target: 0).
- User feedback on clarity of CLI output and ease of use.
- Percentage of files successfully uploaded compared to source, verified by count and optionally size/hash.
```
---
## ⚙️ Constraints & Preferences
**Budget/Time Constraints**:
```
[Not specified in the provided context]
```
**Technical Constraints**:
```
- Must use Python.
- Must use Microsoft Graph API for SharePoint interaction.
- Must be a CLI tool.
- Must support SSH (rsync/scp) for remote directory fetching.
- Temporary/cache folder created next to the running script by default (for portability).
```
**Team Preferences**:
```
[Not specified, but implied by the structure and requirements:]
- Modular design (as per `core/` submodules).
- Use of specific libraries like "Rich", "MSAL/azure-identity".
- Emphasis on robust error handling and resumability.
```
---
## 📚 Additional Context
**Inspiration/References**:
```
[Implied by functionality: robust CLI upload tools, rsync behavior, resumable download managers]
```
**Existing Assets**:
```
[None specified, project to be built from scratch based on the spec]
```
**Special Considerations**:
```
- Portability: temp/cache folder created next to the running script.
- Focus on resilience: handling network issues, API limits, session expiries.
- Rich user feedback is a key requirement.
- Needs to handle large file sizes (10GB+) and potentially large numbers of files.
- Configuration flexibility with `.env` and `config.json`.
```
---
## 🚀 Autonomous Development Instructions
**Agent Coordination Instructions**:
- Primary Orchestrator: Take this complete blueprint and initiate full project development
- Super Orchestrator: Analyze requirements and create comprehensive development plan
- All Agents: Work autonomously until ALL success criteria are met
- State Scribe: Track progress against each requirement and success criteria
- Continue development cycles until project is production-ready and meets all launch criteria
**Completion Signal**: Project is complete when all core features are implemented, tested, documented, and ready for production deployment with all success criteria satisfied.
---
*Ready to build? Feed this blueprint to your Primary Orchestrator and watch your project come to life!*
