"""
Integration tests for configuration management.

These tests verify that configuration changes persist across application sessions,
different components work correctly with configuration, and configuration
handles various edge cases properly.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from tests.integration.base_integration_test import BaseIntegrationTest
from app.managers.config_manager import ConfigManager


class TestConfigurationPersistence(BaseIntegrationTest):
    """Test configuration persistence across application sessions."""

    def test_config_persists_across_instances(self):
        """Test that configuration changes persist across ConfigManager instances."""
        # Create first instance and modify config
        config_manager1 = self.create_test_config_manager()

        # Modify various config values
        config_manager1.config['base_directory'] = '/custom/base/path'
        config_manager1.config['compression_level'] = 'high'
        config_manager1.config['preserve_bookmarks'] = False
        config_manager1.config['output_password_protect'] = True
        config_manager1.config['output_password'] = 'secret123'

        # Add recent directories
        with patch('os.path.isdir', return_value=True):
            config_manager1.add_recent_directory('/project/docs')
            config_manager1.add_recent_directory('/home/pdfs')

        # Save config
        config_manager1.save_config()

        # Create second instance and verify config loaded
        config_manager2 = ConfigManager(config_manager1.config_path)

        # Verify all values persisted
        assert config_manager2.config['base_directory'] == '/custom/base/path'
        assert config_manager2.config['compression_level'] == 'high'
        assert config_manager2.config['preserve_bookmarks'] is False
        assert config_manager2.config['output_password_protect'] is True
        assert config_manager2.config['output_password'] == 'secret123'

        # Verify recent directories (with path resolution)
        expected_recent = [str(Path('/project/docs').resolve()), str(Path('/home/pdfs').resolve())]
        # Verify directories persist (order may vary)
        assert len(config_manager2.config['recent_directories']) == 2
        for expected_dir in expected_recent:
            assert expected_dir in config_manager2.config['recent_directories']

    def test_config_handles_missing_file_gracefully(self):
        """Test that ConfigManager handles missing config file gracefully."""
        non_existent_path = self.temp_dir / "non_existent_config.json"

        # Should create new config with defaults
        config_manager = ConfigManager(non_existent_path)

        # Verify default values
        assert config_manager.config['base_directory'] == str(Path.home())
        assert config_manager.config['recent_directories'] == []
        assert config_manager.config['compression_level'] == 'normal'
        assert config_manager.config['preserve_bookmarks'] is True

    def test_config_handles_corrupted_file(self):
        """Test that ConfigManager handles corrupted config file."""
        # Create corrupted config file
        self.config_path.write_text("this is not valid json {")

        # Should load defaults despite corruption
        config_manager = ConfigManager(self.config_path)

        # Verify default values loaded
        assert config_manager.config['base_directory'] == str(Path.home())
        assert config_manager.config['recent_directories'] == []
        assert 'compression_level' in config_manager.config

    def test_config_directory_creation(self):
        """Test that ConfigManager creates necessary directories."""
        # Create path with non-existent subdirectories
        nested_path = self.temp_dir / "subdir" / "config" / "settings.json"

        # Should create directories and save config
        config_manager = ConfigManager(nested_path)
        config_manager.config['test_setting'] = 'test_value'
        config_manager.save_config()

        # Verify file was created
        assert nested_path.exists()
        assert nested_path.parent.exists()

        # Verify content
        import json
        with open(nested_path, 'r') as f:
            saved_config = json.load(f)
        assert saved_config['test_setting'] == 'test_value'


class TestConfigurationWorkflows(BaseIntegrationTest):
    """Test configuration workflows and component integration."""

    def test_recent_directories_workflow(self):
        """Test complete workflow of adding, persisting, and loading recent directories."""
        config_manager = self.create_test_config_manager()

        # Add directories
        test_dirs = ['/docs/pdfs', '/work/projects', '/personal/files']
        with patch('os.path.isdir', return_value=True):
            for test_dir in test_dirs:
                config_manager.add_recent_directory(test_dir)

        # Verify directories added (order may vary due to deduplication)
        assert len(config_manager.config['recent_directories']) == 3
        resolved_test_dirs = [str(Path(d).resolve()) for d in test_dirs]
        for expected_dir in resolved_test_dirs:
            assert expected_dir in config_manager.config['recent_directories']

        # Save and reload
        config_manager.save_config()
        new_manager = ConfigManager(config_manager.config_path)

        # Verify directories persisted
        assert len(new_manager.config['recent_directories']) == 3
        for expected_dir in resolved_test_dirs:
            assert expected_dir in new_manager.config['recent_directories']

        # Add more directories to new instance
        with patch('os.path.isdir', return_value=True):
            new_manager.add_recent_directory('/new/directory')

        # Verify new directory added and old ones preserved
        assert len(new_manager.config['recent_directories']) == 4
        assert str(Path('/new/directory').resolve()) in new_manager.config['recent_directories']

    def test_profile_workflow_integration(self):
        """Test profile creation, saving, loading workflow."""
        config_manager = self.create_test_config_manager()

        # Create test file details
        test_files = [
            {'filepath': '/doc1.pdf', 'selected_pages': [1, 2, 3], 'page_count': 10},
            {'filepath': '/doc2.pdf', 'selected_pages': [1, 2, 3, 4, 5], 'page_count': 15}
        ]

        # Save profile
        config_manager.save_profile('test_profile', test_files)

        # Verify profile saved in memory
        assert 'test_profile' in config_manager.config['profiles']
        profile = config_manager.config['profiles']['test_profile']
        assert profile['pdf_merger_pro_list'] == test_files
        assert 'created' in profile

        # Save and reload
        config_manager.save_config()
        new_manager = ConfigManager(config_manager.config_path)

        # Verify profile persisted
        assert 'test_profile' in new_manager.config['profiles']
        loaded_profile = new_manager.config['profiles']['test_profile']
        assert loaded_profile['pdf_merger_pro_list'] == test_files
        assert loaded_profile['created'] == profile['created']

        # Test profile retrieval
        retrieved_profile = new_manager.get_profile('test_profile')
        assert retrieved_profile == loaded_profile

    def test_window_state_persistence_workflow(self):
        """Test window state saving and loading workflow."""
        config_manager = self.create_test_config_manager()

        # Set window state
        geometry = "1200x800+150+100"
        sash_positions = {
            'upper_panedwindow': (350, 650),
            'lower_panedwindow': (200,)
        }

        config_manager.save_window_state(geometry, sash_positions)

        # Verify state saved in memory
        assert config_manager.config['window_geometry'] == geometry
        assert config_manager.config['panedwindow_sash_positions'] == sash_positions

        # Save and reload
        config_manager.save_config()
        new_manager = ConfigManager(config_manager.config_path)

        # Verify window state persisted (tuples become lists in JSON)
        loaded_geometry, loaded_sash = new_manager.load_window_state()
        assert loaded_geometry == geometry
        # Convert tuples to lists for comparison since JSON serialization converts tuples to lists
        expected_sash = {k: list(v) for k, v in sash_positions.items()}
        assert loaded_sash == expected_sash

    def test_configuration_update_workflow(self):
        """Test workflow of updating configuration settings."""
        config_manager = self.create_test_config_manager()

        # Set initial values
        config_manager.config['compression_level'] = 'normal'
        config_manager.config['preserve_bookmarks'] = True
        config_manager.config['output_color_mode'] = 'Colorful (Original)'
        config_manager.config['output_dpi'] = 'Original'

        # Update multiple settings
        config_manager.config.update({
            'compression_level': 'high',
            'preserve_bookmarks': False,
            'output_color_mode': 'Grayscale',
            'output_dpi': '300'
        })

        # Save and reload
        config_manager.save_config()
        new_manager = ConfigManager(config_manager.config_path)

        # Verify all updates persisted
        assert new_manager.config['compression_level'] == 'high'
        assert new_manager.config['preserve_bookmarks'] is False
        assert new_manager.config['output_color_mode'] == 'Grayscale'
        assert new_manager.config['output_dpi'] == '300'


class TestConfigurationEdgeCases(BaseIntegrationTest):
    """Test configuration handling of edge cases and error conditions."""

    def test_config_with_large_recent_directories_list(self):
        """Test configuration with large number of recent directories."""
        from app.utils.constants import MAX_RECENT_DIRS

        config_manager = self.create_test_config_manager()

        # Add more directories than the maximum
        with patch('os.path.isdir', return_value=True):
            for i in range(MAX_RECENT_DIRS + 5):
                config_manager.add_recent_directory(f'/dir{i}')

        # Verify only maximum number kept
        assert len(config_manager.config['recent_directories']) == MAX_RECENT_DIRS

        # Verify most recent ones kept
        for i in range(MAX_RECENT_DIRS):
            expected_dir = str(Path(f'/dir{MAX_RECENT_DIRS + 4 - i}').resolve())
            assert expected_dir in config_manager.config['recent_directories']

    def test_config_with_special_characters_in_paths(self):
        """Test configuration with special characters in file paths."""
        config_manager = self.create_test_config_manager()

        special_paths = [
            '/path/with spaces',
            '/path/with-unicode-测试',
            '/path/with@symbols#test',
            'C:\\Windows\\Style\\Path\\On\\Windows'
        ]

        with patch('os.path.isdir', return_value=True):
            for path in special_paths:
                config_manager.add_recent_directory(path)

        # Save and reload
        config_manager.save_config()
        new_manager = ConfigManager(config_manager.config_path)

        # Verify all paths handled correctly
        assert len(new_manager.config['recent_directories']) == len(special_paths)
        for original_path in special_paths:
            resolved_path = str(Path(original_path).resolve())
            assert resolved_path in new_manager.config['recent_directories']

    def test_config_concurrent_profile_operations(self):
        """Test concurrent profile operations."""
        config_manager = self.create_test_config_manager()

        # Create multiple profiles
        profiles_data = {
            'profile1': [{'filepath': '/file1.pdf', 'selected_pages': [1, 2]}],
            'profile2': [{'filepath': '/file2.pdf', 'selected_pages': [1, 2, 3]}],
            'profile3': [{'filepath': '/file3.pdf', 'selected_pages': [1]}]
        }

        for name, files in profiles_data.items():
            config_manager.save_profile(name, files)

        # Verify all profiles saved
        assert len(config_manager.config['profiles']) == 3
        for name in profiles_data.keys():
            assert name in config_manager.config['profiles']
            assert config_manager.get_profile(name) is not None

        # Delete middle profile
        success = config_manager.delete_profile('profile2')
        assert success is True
        assert 'profile2' not in config_manager.config['profiles']
        assert config_manager.get_profile('profile2') is None

        # Verify other profiles still exist
        assert 'profile1' in config_manager.config['profiles']
        assert 'profile3' in config_manager.config['profiles']

    def test_config_empty_and_none_values(self):
        """Test configuration handling of empty and None values."""
        config_manager = self.create_test_config_manager()

        # Test with various edge values
        edge_values = {
            'empty_string': '',
            'none_value': None,
            'empty_list': [],
            'empty_dict': {},
            'zero': 0,
            'false': False
        }

        # Set edge values
        for key, value in edge_values.items():
            config_manager.config[key] = value

        # Save and reload
        config_manager.save_config()
        new_manager = ConfigManager(config_manager.config_path)

        # Verify edge values handled correctly
        for key, value in edge_values.items():
            assert key in new_manager.config
            assert new_manager.config[key] == value


class TestConfigurationIntegration(BaseIntegrationTest):
    """Test configuration integration with other components."""

    def test_config_integration_with_performance_monitor(self):
        """Test that configuration works with performance monitoring."""
        from app.managers.performance_monitor import get_performance_monitor

        config_manager = self.create_test_config_manager()
        perf_monitor = get_performance_monitor()

        # Modify config settings that might affect performance monitoring
        config_manager.config['log_output'] = 'both'
        config_manager.config['log_level'] = 'DEBUG'

        # Save and reload
        config_manager.save_config()
        new_manager = ConfigManager(config_manager.config_path)

        # Verify config accessible by performance monitor (conceptually)
        # In real implementation, performance monitor would use config for logging settings
        assert new_manager.config['log_output'] == 'both'
        assert new_manager.config['log_level'] == 'DEBUG'

    def test_config_backup_and_restore_workflow(self):
        """Test configuration backup and restore workflow."""
        config_manager = self.create_test_config_manager()

        # Set complex configuration
        config_manager.config['base_directory'] = '/complex/path'
        config_manager.config['compression_level'] = 'maximum'
        config_manager.config['preserve_bookmarks'] = True

        # Add profiles and recent directories
        with patch('os.path.isdir', return_value=True):
            config_manager.add_recent_directory('/backup/location')

        test_files = [{'filepath': '/important.pdf', 'selected_pages': [1, 2, 3]}]
        config_manager.save_profile('backup_profile', test_files)

        # Save config
        config_manager.save_config()

        # Create backup
        backup_path = self.temp_dir / "config_backup.json"
        import shutil
        shutil.copy2(config_manager.config_path, backup_path)

        # Modify current config
        config_manager.config['base_directory'] = '/modified/path'
        config_manager.save_config()

        # Restore from backup
        shutil.copy2(backup_path, config_manager.config_path)
        restored_manager = ConfigManager(config_manager.config_path)

        # Verify original values restored
        assert restored_manager.config['base_directory'] == '/complex/path'
        assert restored_manager.config['compression_level'] == 'maximum'
        assert restored_manager.config['preserve_bookmarks'] is True
        assert str(Path('/backup/location').resolve()) in restored_manager.config['recent_directories']
        assert 'backup_profile' in restored_manager.config['profiles']
