"""Tests for the authentication module."""

import pytest
from unittest.mock import patch, MagicMock
from core.auth import get_access_token

# A sample JWT token structure for mocking purposes
MOCK_JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

@pytest.fixture
def mock_config():
    """Fixture to mock the config dictionary."""
    return {
        "TENANT_ID": "dummy_tenant",
        "CLIENT_ID": "dummy_client", 
        "CLIENT_SECRET": "dummy_secret",
        "SHAREPOINT_HOST": "dummy_host"
    }

@pytest.fixture
def mock_msal_success():
    """Fixture to mock a successful MSAL authentication."""
    mock_app = MagicMock()
    mock_app.acquire_token_for_client.return_value = {
        "access_token": MOCK_JWT_TOKEN
    }
    with patch('msal.ConfidentialClientApplication', return_value=mock_app) as mock_constructor:
        yield mock_constructor, mock_app

@pytest.fixture
def mock_msal_failure():
    """Fixture to mock a failed MSAL authentication."""
    mock_app = MagicMock()
    mock_app.acquire_token_for_client.return_value = {
        "error": "invalid_grant",
        "error_description": "Authentication failed"
    }
    with patch('msal.ConfidentialClientApplication', return_value=mock_app) as mock_constructor:
        yield mock_constructor, mock_app

def test_get_access_token_basic_functionality(mock_msal_success, mock_config):
    """Test basic token acquisition functionality."""
    mock_constructor, mock_app = mock_msal_success
    
    with patch('core.auth.config', mock_config):
        token = get_access_token()
        assert isinstance(token, str)
        assert len(token) > 0
        assert token == MOCK_JWT_TOKEN

def test_get_access_token_consistency(mock_msal_success, mock_config):
    """Test that the function returns consistent results."""
    mock_constructor, mock_app = mock_msal_success
    
    with patch('core.auth.config', mock_config):
        token1 = get_access_token()
        token2 = get_access_token()
        assert token1 == token2
        assert isinstance(token1, str)
        assert len(token1) > 0

def test_get_access_token_success(mock_msal_success, mock_config):
    """Test successful token acquisition from MS Graph."""
    mock_constructor, mock_app = mock_msal_success
    
    # Mock the config that gets loaded at module level
    with patch('core.auth.config', mock_config):
        token = get_access_token()

        # Verify that the MSAL client was initialized correctly
        authority_url = f"https://login.microsoftonline.com/{mock_config['TENANT_ID']}"
        mock_constructor.assert_called_once_with(
            mock_config['CLIENT_ID'],
            authority=authority_url,
            client_credential=mock_config['CLIENT_SECRET']
        )

        # Verify that the token acquisition method was called with the correct scope
        scopes = [f"https://{mock_config['SHAREPOINT_HOST']}/.default"]
        mock_app.acquire_token_for_client.assert_called_once_with(scopes=scopes)

        # Assert that the function returns the access token from the response
        assert token == MOCK_JWT_TOKEN

def test_get_access_token_failure(mock_msal_failure, mock_config):
    """Test handling of a failed token acquisition."""
    mock_constructor, mock_app = mock_msal_failure
    
    with patch('core.auth.config', mock_config):
        with pytest.raises(Exception) as excinfo:
            get_access_token()
        
        assert "Authentication failed" in str(excinfo.value)
        assert "invalid_grant" in str(excinfo.value)

def test_get_access_token_validates_token_format(mock_msal_success, mock_config):
    """Test that the returned token has the expected format."""
    mock_constructor, mock_app = mock_msal_success
    
    with patch('core.auth.config', mock_config):
        token = get_access_token()
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT tokens have three parts separated by dots
        assert token.count('.') == 2