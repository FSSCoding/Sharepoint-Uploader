import json
import logging
import tempfile
from pathlib import Path
from rich.logging import RichHandler

class StatePersister:
    """Handles reading and writing the state of resumable uploads to a JSON file."""

    def get_state_filepath(self, original_path: Path) -> Path:
        """Returns the standardized path for a state file."""
        return Path(f"{original_path}.state.json")

    def load_state(self, file_path: Path) -> dict:
        """Reads and deserializes the JSON state file."""
        if not file_path.exists():
            return {}
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Could not read state file {file_path}: {e}. Starting fresh.")
            return {}

    def save_state(self, file_path: Path, state: dict):
        """Serializes and writes the current state to the file."""
        try:
            with open(file_path, "w") as f:
                json.dump(state, f, indent=4)
        except IOError as e:
            logging.error(f"Could not write to state file {file_path}: {e}")

    def clear_state(self, file_path: Path):
        """Deletes the state file."""
        try:
            if file_path.exists():
                file_path.unlink()
        except IOError as e:
            logging.error(f"Could not delete state file {file_path}: {e}")


class PathManager:
    """Manages filesystem paths."""

    def __init__(self, temp_dir: str = None):
        if temp_dir:
            self._temp_path = Path(temp_dir)
        else:
            self._temp_path = Path(tempfile.gettempdir()) / "sharepoint_uploader_temp"

    def get_temp_path(self) -> Path:
        """Returns the path to the temporary directory, creating it if it doesn't exist."""
        self._temp_path.mkdir(parents=True, exist_ok=True)
        return self._temp_path

    def cleanup_temp_path(self):
        """Recursively deletes the temporary directory."""
        if self._temp_path.exists():
            import shutil
            shutil.rmtree(self._temp_path)


class Logger:
    """Centralized configuration for the rich logging handler."""

    @staticmethod
    def setup_logging(verbose: bool):
        """Configures a RichHandler for Python's logging module."""
        log_level = "DEBUG" if verbose else "INFO"
        logging.basicConfig(
            level=log_level,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(rich_tracebacks=True, tracebacks_suppress=[json])],
            force=True,
        )

def load_config(config_path: str) -> dict:
    """Loads a JSON configuration file, creating a default one if it doesn't exist."""
    config_file = Path(config_path)
    
    # If config file doesn't exist, create it from template
    if not config_file.exists():
        template_path = config_file.parent / "config.json.template"
        if template_path.exists():
            logging.info(f"📋 Config file not found. Creating default config: {config_path}")
            try:
                # Copy template to config file
                import shutil
                shutil.copy2(template_path, config_file)
                logging.info(f"✅ Created default config file from template")
                logging.warning(f"⚠️  Please edit {config_path} with your actual credentials before using the application")
            except Exception as e:
                logging.error(f"❌ Error creating config file from template: {e}")
                import sys
                sys.exit(1)
        else:
            # Create a basic default config if no template exists
            default_config = {
                "TENANT_ID": "your-tenant-id-here",
                "CLIENT_ID": "your-client-id-here", 
                "CLIENT_SECRET": "your-client-secret-here",
                "SITE_ID": "your-site-id-here",
                "DRIVE_ID": "your-drive-id-here",
                "SHAREPOINT_HOST": "graph.microsoft.com",
                "SCOPES": "https://graph.microsoft.com/.default"
            }
            try:
                logging.info(f"📋 Config file and template not found. Creating default config: {config_path}")
                with open(config_file, "w") as f:
                    json.dump(default_config, f, indent=2)
                logging.info(f"✅ Created default config file")
                logging.warning(f"⚠️  Please edit {config_path} with your actual credentials before using the application")
            except Exception as e:
                logging.error(f"❌ Error creating default config file: {e}")
                import sys
                sys.exit(1)
    
    # Load and return the config
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
            
        # Validate that config has placeholder values
        placeholder_values = ["your-tenant-id-here", "your-client-id-here", "your-client-secret-here", 
                             "your-site-id-here", "your-drive-id-here"]
        
        has_placeholders = any(
            config.get(key, "").strip() in placeholder_values 
            for key in ["TENANT_ID", "CLIENT_ID", "CLIENT_SECRET", "SITE_ID", "DRIVE_ID"]
        )
        
        if has_placeholders:
            logging.warning(f"⚠️  Configuration file {config_path} contains placeholder values")
            logging.warning(f"⚠️  Please update the configuration with your actual Microsoft Graph API credentials")
            logging.info(f"💡 You can find setup instructions in the documentation")
            
        return config
        
    except json.JSONDecodeError as e:
        logging.error(f"❌ Error parsing JSON in config file {config_path}: {e}")
        import sys
        sys.exit(1)
    except Exception as e:
        logging.error(f"❌ Error loading config file {config_path}: {e}")
        import sys
        sys.exit(1)

import time
import httpx
from functools import wraps

def api_retry(max_retries=5, initial_delay=1, backoff_factor=2):
    """
    A decorator for retrying API calls with exponential backoff.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    if isinstance(e, httpx.HTTPStatusError) and e.response.status_code < 500:
                        # Don't retry on 4xx client errors, except for 401 which is handled elsewhere
                        if e.response.status_code != 401:
                            raise
                    
                    logging.warning(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {delay}s...")
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logging.error(f"API call failed after {max_retries} attempts.")
                        raise
        return wrapper
    return decorator