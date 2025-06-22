# Research Area 3: CLI Design, Configuration, and State Management

This research area focuses on the application's user-facing components, its internal architecture, and how it persists state to achieve resumability.

## 🎯 Key Research Questions

1.  **CLI Implementation:**
    *   What is the best library for building the CLI interface as specified (`argparse`, `click`, `typer`)? The blueprint implies a standard library approach might be sufficient.
    *   How should the CLI arguments (`--remote-path`, `--target-path`, etc.) be defined and parsed?
    *   How can we provide clear and helpful `--help` messages?

2.  **Rich CLI Feedback:**
    *   How can the `rich` library be used to display nested progress bars (e.g., an overall progress bar for the total upload and a per-file progress bar)?
    *   What `rich` components are best suited for displaying transfer rates, ETAs, and status messages?
    *   How can logging be integrated with `rich` to provide a seamless and informative display, especially in verbose mode?

3.  **Configuration Management:**
    *   What is the standard, most secure way to load `.env` files in Python?
    *   How should the application implement the override logic, where `config.json` values take precedence over `.env` values?
    *   What is a good structure for the `config.json` file?

4.  **State Persistence for Resumability:**
    *   What specific information needs to be saved to disk to allow for a clean resume? (e.g., for each file: source path, target SharePoint URL, upload session URL, last successfully uploaded byte offset, number of retries).
    *   What is the best format for this state file? (JSON, SQLite, etc.). JSON is simple and human-readable.
    *   How does the application detect an existing state file upon startup?
    *   How should the application handle graceful shutdowns (e.g., on `Ctrl+C`) to ensure the latest state is flushed to disk?

5.  **Application Architecture:**
    *   What is a logical way to structure the codebase into modules? (e.g., `main.py`, `core/auth.py`, `core/uploader.py`, `core/ssh.py`, `core/config.py`, `core/state.py`).
    *   How should the different components (SSH fetcher, Graph API uploader, progress display) interact with each other?
    *   How will the retry logic (e.g., exponential backoff) be implemented and managed?

## 📚 Potential Sources

*   Documentation for `argparse`, `click`, and `typer`.
*   The `rich` library's documentation and examples.
*   Tutorials on configuration management in Python (`python-dotenv`, `configparser`).
*   Articles on designing resumable applications and managing state.
*   Examples of well-structured Python CLI applications on GitHub.