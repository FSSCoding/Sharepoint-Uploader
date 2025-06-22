import msal
import os
from pathlib import Path
from dotenv import load_dotenv
from core.utils import load_config

# Load environment variables from .env file if it exists
env_file = Path('.env')
if env_file.exists():
    load_dotenv(env_file)
    # Use environment variables if available, otherwise fall back to config.json
    config = {
        'TENANT_ID': os.getenv('TENANT_ID'),
        'CLIENT_ID': os.getenv('CLIENT_ID'), 
        'CLIENT_SECRET': os.getenv('CLIENT_SECRET'),
        'SITE_ID': os.getenv('SITE_ID'),
        'DRIVE_ID': os.getenv('DRIVE_ID'),
        'SHAREPOINT_HOST': os.getenv('SHAREPOINT_HOST', 'graph.microsoft.com'),
        'SCOPES': os.getenv('SCOPES', 'https://graph.microsoft.com/.default')
    }
    # Check if all required env vars are present
    required_vars = ['TENANT_ID', 'CLIENT_ID', 'CLIENT_SECRET', 'SITE_ID', 'DRIVE_ID']
    if all(config.get(var) for var in required_vars):
        print("🔐 Using credentials from .env file")
    else:
        print("⚠️  Some credentials missing from .env, falling back to config.json")
        config = load_config('config.json')
else:
    config = load_config('config.json')

def get_access_token():
    """
    Acquires an access token from Microsoft Graph using the MSAL library.

    This function uses the client credentials flow to authenticate the application
    and retrieve an access token required for API calls.

    Returns:
        str: The access token.

    Raises:
        Exception: If token acquisition fails.
    """
    tenant_id = config.get("TENANT_ID")
    client_id = config.get("CLIENT_ID")
    client_secret = config.get("CLIENT_SECRET")
    sharepoint_host = config.get("SHAREPOINT_HOST")

    authority = f"https://login.microsoftonline.com/{tenant_id}"
    scopes = [f"https://{sharepoint_host}/.default"]

    app = msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret
    )

    result = app.acquire_token_for_client(scopes=scopes)

    if "access_token" in result:
        return result["access_token"]
    else:
        error_details = result.get("error_description", "No error description provided.")
        raise Exception(f"Authentication failed: {result.get('error')} - {error_details}")