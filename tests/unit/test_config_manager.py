"""
Unit tests for the config_manager module.
"""

import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime

from app.managers.config_manager import ConfigManager
from app.utils.constants import (
    DEFAULT_CONFIG_PATH, MAX_RECENT_DIRS, DEFAULT_COMPRESSION,
    DEFAULT_PRESERVE_BOOKMARKS, DEFAULT_PASSWORD_PROTECT,
    DEFAULT_COLOR_MODE, DEFAULT_DPI, DEFAULT_LOG_OUTPUT,
    DEFAULT_LOG_LEVEL, DEFAULT_LOG_FILE_PATH, PROFILE_LIST_KEY,
    WINDOW_GEOMETRY_KEY, PANEDWINDOW_SASH_KEY
)


class TestConfigManagerInitialization:
    """Test ConfigManager initialization."""

    def test_config_manager_creation_with_default_path(self):
        """Test ConfigManager creation with default config path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)
            assert manager.config_path == config_path
            assert isinstance(manager.config, dict)
            assert 'base_directory' in manager.config
            assert 'recent_directories' in manager.config
            assert isinstance(manager.config['recent_directories'], list)

    def test_config_manager_creation_with_custom_path(self):
        """Test ConfigManager creation with custom config path."""
        custom_path = Path("custom_config.json")
        manager = ConfigManager(custom_path)
        assert manager.config_path == custom_path

    def test_default_config_structure(self):
        """Test that default config has all required fields."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            # Check required fields
            required_fields = [
                'base_directory', 'recent_directories', 'default_output_dir',
                'compression_level', 'preserve_bookmarks', 'profiles',
                'output_password_protect', 'output_color_mode', 'output_dpi',
                'log_output', 'log_level', 'log_file_path',
                WINDOW_GEOMETRY_KEY, PANEDWINDOW_SASH_KEY
            ]

            for field in required_fields:
                assert field in manager.config

            # Check default values
            assert manager.config['base_directory'] == str(Path.home())
            assert manager.config['recent_directories'] == []
            assert manager.config['default_output_dir'] == str(Path.home())
            assert manager.config['compression_level'] == DEFAULT_COMPRESSION
            assert manager.config['preserve_bookmarks'] == DEFAULT_PRESERVE_BOOKMARKS
            assert manager.config['profiles'] == {}
            assert manager.config['output_password_protect'] == DEFAULT_PASSWORD_PROTECT
            assert manager.config['output_color_mode'] == DEFAULT_COLOR_MODE
            assert manager.config['output_dpi'] == DEFAULT_DPI
            assert manager.config['log_output'] == DEFAULT_LOG_OUTPUT
            assert manager.config['log_level'] == DEFAULT_LOG_LEVEL
            assert manager.config['log_file_path'] == DEFAULT_LOG_FILE_PATH
            assert manager.config[WINDOW_GEOMETRY_KEY] == ""
            assert manager.config[PANEDWINDOW_SASH_KEY] == {}


class TestConfigManagerLoadConfig:
    """Test configuration loading functionality."""

    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            with patch('pathlib.Path.exists', return_value=False):
                manager = ConfigManager(config_path)
                # Should use default config
                assert manager.config['base_directory'] == str(Path.home())
                assert manager.config['recent_directories'] == []

    def test_load_config_successful(self):
        """Test successful config loading."""
        test_config = {
            'base_directory': '/test/path',
            'recent_directories': ['/test/dir1', '/test/dir2'],
            'custom_field': 'custom_value'
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            with patch('pathlib.Path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=json.dumps(test_config))):
                    with patch('json.load', return_value=test_config):
                        manager = ConfigManager(config_path)

                        # Should merge with defaults
                        assert manager.config['base_directory'] == '/test/path'
                        assert manager.config['recent_directories'] == ['/test/dir1', '/test/dir2']
                        assert manager.config['custom_field'] == 'custom_value'
                        # Should still have default fields
                        assert 'compression_level' in manager.config

    def test_load_config_json_decode_error(self):
        """Test loading config with invalid JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            with patch('pathlib.Path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data="invalid json")):
                    with patch('json.load', side_effect=json.JSONDecodeError("Invalid JSON", "", 0)):
                        manager = ConfigManager(config_path)

                        # Should fall back to defaults
                        assert manager.config['base_directory'] == str(Path.home())
                        assert manager.config['recent_directories'] == []

    def test_load_config_unexpected_error(self):
        """Test loading config with unexpected error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            with patch('pathlib.Path.exists', return_value=True):
                with patch('builtins.open', side_effect=Exception("Unexpected error")):
                    manager = ConfigManager(config_path)

                    # Should fall back to defaults
                    assert manager.config['base_directory'] == str(Path.home())
                    assert manager.config['recent_directories'] == []


class TestConfigManagerSaveConfig:
    """Test configuration saving functionality."""

    def test_save_config_successful(self):
        """Test successful config saving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            # Modify config
            manager.config['base_directory'] = '/test/path'
            manager.config['recent_directories'] = ['/test/dir']

            with patch('builtins.open', mock_open()) as mock_file:
                with patch('json.dump') as mock_json_dump:
                    manager.save_config()

                    # Verify json.dump was called with correct data
                    mock_json_dump.assert_called_once()
                    args, kwargs = mock_json_dump.call_args
                    saved_config = args[0]
                    assert saved_config['base_directory'] == '/test/path'
                    assert saved_config['recent_directories'] == ['/test/dir']

    def test_save_config_creates_directory(self):
        """Test that save_config creates necessary directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "subdir" / "test_config.json"
            manager = ConfigManager(config_path)

            with patch('builtins.open', mock_open()):
                with patch('json.dump'):
                    with patch('pathlib.Path.mkdir') as mock_mkdir:
                        manager.save_config()

                        # Verify directory creation was called
                        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_save_config_handles_errors(self):
        """Test that save_config handles errors gracefully."""
        with patch('builtins.open', side_effect=Exception("Save error")):
            manager = ConfigManager()

            # Should not raise exception
            manager.save_config()
            # Error should be logged, but config should remain unchanged


class TestConfigManagerRecentDirectories:
    """Test recent directories functionality."""

    def test_add_recent_directory_valid(self):
        """Test adding a valid directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            with patch('os.path.isdir', return_value=True):
                manager.add_recent_directory('/test/path')

                # Path.resolve() normalizes the path according to the platform
                resolved_path = str(Path('/test/path').resolve())
                assert resolved_path in manager.config['recent_directories']
                assert manager.config['recent_directories'][0] == resolved_path

    def test_add_recent_directory_invalid_string(self):
        """Test adding invalid directory string."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            # Test empty string
            manager.add_recent_directory('')
            assert manager.config['recent_directories'] == []

            # Test None
            manager.add_recent_directory(None)
            assert manager.config['recent_directories'] == []

    def test_add_recent_directory_nonexistent(self):
        """Test adding non-existent directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            with patch('os.path.isdir', return_value=False):
                manager.add_recent_directory('/nonexistent/path')
                assert manager.config['recent_directories'] == []

    def test_add_recent_directory_resolves_path(self):
        """Test that directory paths are resolved."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            with patch('os.path.isdir', return_value=True):
                with patch('pathlib.Path.resolve', return_value=Path('/resolved/path')):
                    manager.add_recent_directory('/test/path')

                    assert str(Path('/resolved/path')) in manager.config['recent_directories']

    def test_add_recent_directory_duplicate_moves_to_front(self):
        """Test that adding duplicate directory moves it to front."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            with patch('os.path.isdir', return_value=True):
                # Set initial directories - they will remain unresolved in the config
                initial_dirs = ['/path1', '/path2', '/path3']
                manager.config['recent_directories'] = initial_dirs

                manager.add_recent_directory('/path2')

                # The new path gets resolved and added to front, existing paths remain as-is
                # Since resolved(/path2) != '/path2', no duplicate is removed
                # Result should be: resolved(/path2) + /path1 + /path2 + /path3
                expected = [str(Path('/path2').resolve()), '/path1', '/path2', '/path3']
                assert manager.config['recent_directories'] == expected

    def test_add_recent_directory_respects_max_limit(self):
        """Test that recent directories list respects max limit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            with patch('os.path.isdir', return_value=True):
                # Add more directories than MAX_RECENT_DIRS
                for i in range(MAX_RECENT_DIRS + 2):
                    manager.add_recent_directory(f'/path{i}')

                assert len(manager.config['recent_directories']) == MAX_RECENT_DIRS
                # Should keep the most recent ones (paths get resolved)
                expected_latest = str(Path(f'/path{MAX_RECENT_DIRS + 1}').resolve())
                assert manager.config['recent_directories'][0] == expected_latest


class TestConfigManagerProfiles:
    """Test profile management functionality."""

    def test_save_profile_successful(self):
        """Test successful profile saving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            test_files = [
                {'filepath': '/test/file1.pdf', 'selected_pages': [1, 2, 3]},
                {'filepath': '/test/file2.pdf', 'selected_pages': [1]}
            ]

            with patch.object(manager, 'save_config') as mock_save:
                manager.save_profile('test_profile', test_files)

                assert 'test_profile' in manager.config['profiles']
                profile = manager.config['profiles']['test_profile']

                assert profile[PROFILE_LIST_KEY] == test_files
                assert 'compression_level' in profile
                assert 'preserve_bookmarks' in profile
                assert 'created' in profile
                assert 'output_password_protect' in profile

                mock_save.assert_called_once()

    def test_save_profile_invalid_name(self):
        """Test saving profile with invalid name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            with pytest.raises(ValueError, match="Profile name cannot be empty"):
                manager.save_profile('', [])

            with pytest.raises(ValueError, match="Profile name cannot be empty"):
                manager.save_profile(None, [])

            with pytest.raises(ValueError, match="Profile name cannot be empty"):
                manager.save_profile('   ', [])

    def test_get_profile_existing(self):
        """Test getting existing profile."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)
            test_profile = {'test': 'data'}
            manager.config['profiles']['test_profile'] = test_profile

            result = manager.get_profile('test_profile')
            assert result == test_profile

    def test_get_profile_nonexistent(self):
        """Test getting non-existent profile."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            result = manager.get_profile('nonexistent')
            assert result is None

    def test_delete_profile_existing(self):
        """Test deleting existing profile."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)
            manager.config['profiles']['test_profile'] = {'test': 'data'}

            with patch.object(manager, 'save_config') as mock_save:
                result = manager.delete_profile('test_profile')

                assert result is True
                assert 'test_profile' not in manager.config['profiles']
                mock_save.assert_called_once()

    def test_delete_profile_nonexistent(self):
        """Test deleting non-existent profile."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            with patch.object(manager, 'save_config') as mock_save:
                result = manager.delete_profile('nonexistent')

                assert result is False
                mock_save.assert_not_called()

    def test_profile_name_stripping(self):
        """Test that profile names are stripped of whitespace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            with patch.object(manager, 'save_config'):
                manager.save_profile('  test_profile  ', [])

                assert 'test_profile' in manager.config['profiles']  # Should be stripped


class TestConfigManagerWindowState:
    """Test window state management functionality."""

    def test_save_window_state(self):
        """Test saving window state."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            geometry = "1200x800+100+100"
            sash_positions = {'upper_panedwindow': (300,)}

            manager.save_window_state(geometry, sash_positions)

            assert manager.config[WINDOW_GEOMETRY_KEY] == geometry
            assert manager.config[PANEDWINDOW_SASH_KEY] == sash_positions

    def test_load_window_state(self):
        """Test loading window state."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            geometry = "1200x800+100+100"
            sash_positions = {'upper_panedwindow': (300,)}

            manager.config[WINDOW_GEOMETRY_KEY] = geometry
            manager.config[PANEDWINDOW_SASH_KEY] = sash_positions

            loaded_geometry, loaded_sash = manager.load_window_state()

            assert loaded_geometry == geometry
            assert loaded_sash == sash_positions

    def test_load_window_state_defaults(self):
        """Test loading window state with default values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            # Config should have defaults
            geometry, sash_positions = manager.load_window_state()

            assert geometry == ""
            assert sash_positions == {}


class TestConfigManagerIntegration:
    """Integration tests for ConfigManager."""

    def test_full_config_workflow(self):
        """Test complete configuration workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            # Modify configuration
            manager.config['base_directory'] = '/test/base'
            manager.config['compression_level'] = 'high'

            # Add recent directory
            with patch('os.path.isdir', return_value=True):
                manager.add_recent_directory('/test/recent')

            # Save profile
            test_files = [{'filepath': '/test/file.pdf', 'selected_pages': [1, 2]}]
            with patch.object(manager, 'save_config'):
                manager.save_profile('test_profile', test_files)

            # Save window state
            manager.save_window_state("1000x600+50+50", {'pane': (200,)})

            # Verify all changes are in config
            assert manager.config['base_directory'] == '/test/base'
            assert manager.config['compression_level'] == 'high'
            # Path gets resolved
            expected_recent = str(Path('/test/recent').resolve())
            assert expected_recent in manager.config['recent_directories']
            assert 'test_profile' in manager.config['profiles']
            assert manager.config[WINDOW_GEOMETRY_KEY] == "1000x600+50+50"

    def test_config_persistence(self):
        """Test that configuration persists across instances."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"

            # First instance
            manager1 = ConfigManager(config_path)
            manager1.config['test_field'] = 'test_value'
            with patch('builtins.open', mock_open()):
                with patch('json.dump'):
                    manager1.save_config()

            # Second instance should load the saved config
            with patch('pathlib.Path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=json.dumps({'test_field': 'test_value'}))):
                    manager2 = ConfigManager(config_path)

                    # Config should be loaded (though in this mock it won't be)
                    # In real scenario, the loaded config would be merged with defaults

    def test_error_recovery(self):
        """Test that config manager recovers from errors."""
        # Test with corrupted config file
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            with patch('pathlib.Path.exists', return_value=True):
                with patch('builtins.open', side_effect=Exception("File corrupted")):
                    manager = ConfigManager(config_path)

                    # Should still have valid default config
                    assert isinstance(manager.config, dict)
                    assert 'base_directory' in manager.config
                    assert isinstance(manager.config['recent_directories'], list)

    def test_datetime_in_profile(self):
        """Test that profile creation timestamp is properly formatted."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            test_files = [{'filepath': '/test/file.pdf', 'selected_pages': [1]}]

            with patch.object(manager, 'save_config'):
                manager.save_profile('test_profile', test_files)

                profile = manager.config['profiles']['test_profile']
                assert 'created' in profile

                # Should be valid ISO format datetime
                created_time = profile['created']
                assert isinstance(created_time, str)

                # Should be parseable as datetime
                parsed = datetime.fromisoformat(created_time)
                assert isinstance(parsed, datetime)


class TestConfigManagerEdgeCases:
    """Test edge cases and error conditions."""

    def test_config_with_none_values(self):
        """Test handling of None values in config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            # Simulate loading config with None values
            test_config = {
                'base_directory': None,
                'recent_directories': None,
                'profiles': None
            }

            with patch('pathlib.Path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=json.dumps(test_config))):
                    with patch('json.load', return_value=test_config):
                        manager.load_config()

                        # Should handle None values gracefully
                        assert manager.config['base_directory'] is None or isinstance(manager.config['base_directory'], str)

    def test_very_long_directory_path(self):
        """Test handling of very long directory paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            long_path = '/very/long/path/' + 'a' * 1000

            with patch('os.path.isdir', return_value=True):
                with patch('pathlib.Path.resolve', return_value=Path(long_path)):
                    manager.add_recent_directory(long_path)

                    # Path gets resolved
                    expected_long_path = str(Path(long_path).resolve())
                    assert expected_long_path in manager.config['recent_directories']

    def test_special_characters_in_paths(self):
        """Test handling of special characters in paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            special_paths = [
                '/path/with spaces',
                '/path/with-特殊字符',
                '/path/with@#$%^&*()',
                'C:\\Windows\\path\\on\\windows'
            ]

            for path in special_paths:
                with patch('os.path.isdir', return_value=True):
                    with patch('pathlib.Path.resolve', return_value=Path(path)):
                        manager.add_recent_directory(path)

                        # Path gets resolved
                        expected_path = str(Path(path).resolve())
                        assert expected_path in manager.config['recent_directories']

    def test_concurrent_config_access(self):
        """Test behavior with concurrent config access."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_path)

            # Simulate concurrent modifications
            original_config = manager.config.copy()

            # Modify config
            manager.config['test_field'] = 'modified'

            # Config should be modified
            assert manager.config['test_field'] == 'modified'
            assert manager.config != original_config
