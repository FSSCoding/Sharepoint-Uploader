"""Tests for the utils module."""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, mock_open
from core.utils import load_config, StatePersister


class TestLoadConfig:
    """Tests for the load_config function."""

    @patch('builtins.open', new_callable=mock_open, read_data='{"key": "value"}')
    def test_load_config_success(self, mock_file):
        """Test successful config loading."""
        # Arrange
        config_path = 'dummy/path/config.json'

        # Act
        config = load_config(config_path)

        # Assert
        assert config == {"key": "value"}
        mock_file.assert_called_once_with(config_path, 'r')

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_load_config_not_found(self, mock_file):
        """Test config file not found."""
        # Arrange
        config_path = 'non_existent/path/config.json'

        # Act & Assert
        with pytest.raises(SystemExit):
            load_config(config_path)

    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    def test_load_config_invalid_json(self, mock_file):
        """Test invalid JSON in config file."""
        # Arrange
        config_path = 'dummy/path/config.json'

        # Act & Assert
        with pytest.raises(SystemExit):
            load_config(config_path)


class TestStatePersister:
    """Tests for the StatePersister class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.persister = StatePersister()
        self.file_path = Path('/tmp/test_file.txt')
        self.state_file = self.persister.get_state_filepath(self.file_path)

    def test_get_state_filepath(self):
        """Test state file path generation."""
        # Assert
        assert self.state_file == Path(f"{self.file_path}.state.json")

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_state(self, mock_json_dump, mock_file):
        """Test saving state to file."""
        # Arrange
        state = {'uploadUrl': 'http://example.com/upload'}

        # Act
        self.persister.save_state(self.state_file, state)

        # Assert
        mock_file.assert_called_once_with(self.state_file, 'w')
        mock_json_dump.assert_called_once()

    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='{"uploadUrl": "http://example.com/upload"}')
    def test_load_state_exists(self, mock_file, mock_exists):
        """Test loading existing state file."""
        # Act
        state = self.persister.load_state(self.state_file)

        # Assert
        assert state == {'uploadUrl': 'http://example.com/upload'}

    @patch('pathlib.Path.exists', return_value=False)
    def test_load_state_not_exists(self, mock_exists):
        """Test loading non-existent state file."""
        # Act
        state = self.persister.load_state(self.state_file)

        # Assert
        assert state == {}

    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.unlink')
    def test_clear_state(self, mock_unlink, mock_exists):
        """Test clearing state file."""
        # Act
        self.persister.clear_state(self.state_file)

        # Assert
        mock_unlink.assert_called_once()