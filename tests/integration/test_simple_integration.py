"""
Simple integration tests for PDF Merger Pro.

These tests verify that different components work together correctly,
focusing on integration concepts rather than complex file processing.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from tests.integration.base_integration_test import BaseIntegrationTest
from app.managers.config_manager import ConfigManager


class TestBasicIntegration(BaseIntegrationTest):
    """Test basic integration between components."""

    def test_config_manager_initialization_integration(self):
        """Test that ConfigManager integrates properly with the application."""
        config_manager = self.create_test_config_manager()

        # Test that config manager initializes with correct defaults
        assert config_manager.config['base_directory'] == str(Path.home())
        assert 'recent_directories' in config_manager.config
        assert 'profiles' in config_manager.config
        assert 'compression_level' in config_manager.config

        # Test that config can be saved and loaded
        config_manager.config['test_integration'] = 'success'
        config_manager.save_config()

        new_manager = ConfigManager(config_manager.config_path)
        assert new_manager.config['test_integration'] == 'success'

    def test_profile_config_integration(self):
        """Test that profiles integrate correctly with configuration."""
        config_manager = self.create_test_config_manager()

        # Set configuration that should be captured in profiles
        config_manager.config.update({
            'compression_level': 'high',
            'preserve_bookmarks': False,
            'output_color_mode': 'Grayscale'
        })

        # Create profile
        test_files = [{'filepath': '/test.pdf', 'selected_pages': [1, 2, 3]}]
        config_manager.save_profile('integration_test', test_files)

        # Verify profile captures config settings
        profile = config_manager.get_profile('integration_test')
        assert profile is not None
        assert profile['compression_level'] == 'high'
        assert profile['preserve_bookmarks'] is False
        assert profile['output_color_mode'] == 'Grayscale'

        # Verify file list is stored correctly
        assert len(profile['pdf_merger_pro_list']) == 1
        assert profile['pdf_merger_pro_list'][0]['filepath'] == '/test.pdf'

    def test_recent_directories_config_integration(self):
        """Test that recent directories integrate with configuration."""
        config_manager = self.create_test_config_manager()

        # Add recent directories
        with patch('os.path.isdir', return_value=True):
            config_manager.add_recent_directory('/docs/pdfs')
            config_manager.add_recent_directory('/work/projects')
            config_manager.add_recent_directory('/personal/files')

        # Verify directories are stored
        assert len(config_manager.config['recent_directories']) == 3

        # Save and reload
        config_manager.save_config()
        new_manager = ConfigManager(config_manager.config_path)

        # Verify directories persist
        assert len(new_manager.config['recent_directories']) == 3
        recent_dirs = new_manager.config['recent_directories']
        assert any('docs' in str(Path(d).resolve()) for d in recent_dirs)
        assert any('work' in str(Path(d).resolve()) for d in recent_dirs)
        assert any('personal' in str(Path(d).resolve()) for d in recent_dirs)

    def test_window_state_config_integration(self):
        """Test that window state integrates with configuration."""
        config_manager = self.create_test_config_manager()

        # Set window state
        geometry = "1200x800+100+200"
        sash_positions = {'main_pane': (300, 500), 'side_pane': (200,)}

        config_manager.save_window_state(geometry, sash_positions)

        # Verify window state is stored
        assert config_manager.config['window_geometry'] == geometry
        assert config_manager.config['panedwindow_sash_positions'] == sash_positions

        # Save and reload
        config_manager.save_config()
        new_manager = ConfigManager(config_manager.config_path)

        # Verify window state persists
        loaded_geometry, loaded_sash = new_manager.load_window_state()
        assert loaded_geometry == geometry
        assert loaded_sash == {'main_pane': [300, 500], 'side_pane': [200]}  # Tuples become lists in JSON

    def test_complete_workflow_integration(self):
        """Test a complete workflow integrating multiple components."""
        config_manager = self.create_test_config_manager()

        # Step 1: Configure application settings
        config_manager.config.update({
            'compression_level': 'maximum',
            'preserve_bookmarks': True,
            'output_color_mode': 'Colorful (Original)'
        })

        # Step 2: Add recent directories
        with patch('os.path.isdir', return_value=True):
            config_manager.add_recent_directory('/integration/docs')
            config_manager.add_recent_directory('/integration/work')

        # Step 3: Create and save a profile
        profile_files = [
            {'filepath': '/doc1.pdf', 'selected_pages': [1, 2, 3]},
            {'filepath': '/doc2.pdf', 'selected_pages': [1, 2, 3, 4, 5]}
        ]
        config_manager.save_profile('workflow_profile', profile_files)

        # Step 4: Set window state
        config_manager.save_window_state("1000x700+50+100", {'pane': (250,)})

        # Step 5: Save everything
        config_manager.save_config()

        # Step 6: Load in new session and verify everything
        new_manager = ConfigManager(config_manager.config_path)

        # Verify configuration
        assert new_manager.config['compression_level'] == 'maximum'
        assert new_manager.config['preserve_bookmarks'] is True
        assert new_manager.config['output_color_mode'] == 'Colorful (Original)'

        # Verify recent directories
        assert len(new_manager.config['recent_directories']) == 2

        # Verify profile
        profile = new_manager.get_profile('workflow_profile')
        assert profile is not None
        assert len(profile['pdf_merger_pro_list']) == 2
        assert profile['compression_level'] == 'maximum'

        # Verify window state
        geometry, sash = new_manager.load_window_state()
        assert geometry == "1000x700+50+100"
        assert sash == {'pane': [250]}


class TestErrorHandlingIntegration(BaseIntegrationTest):
    """Test error handling integration between components."""

    def test_config_error_handling_integration(self):
        """Test that configuration errors are handled gracefully."""
        # Create corrupted config file
        self.config_path.write_text("invalid json content {")

        # Should handle corruption gracefully
        config_manager = ConfigManager(self.config_path)

        # Should have loaded defaults
        assert 'base_directory' in config_manager.config
        assert 'recent_directories' in config_manager.config

        # Should be able to save new config
        config_manager.config['error_recovery'] = 'successful'
        config_manager.save_config()

        # Verify new config was saved
        new_manager = ConfigManager(config_manager.config_path)
        assert new_manager.config['error_recovery'] == 'successful'

    def test_profile_error_handling_integration(self):
        """Test profile error handling integration."""
        config_manager = self.create_test_config_manager()

        # Test invalid profile name
        with pytest.raises(ValueError, match="Profile name cannot be empty"):
            config_manager.save_profile("", [{'filepath': '/test.pdf', 'selected_pages': [1]}])

        # Test profile with valid data
        test_files = [{'filepath': '/valid.pdf', 'selected_pages': [1, 2]}]
        config_manager.save_profile('valid_profile', test_files)

        # Verify profile was created
        profile = config_manager.get_profile('valid_profile')
        assert profile is not None
        assert len(profile['pdf_merger_pro_list']) == 1

        # Test deleting non-existent profile
        result = config_manager.delete_profile('non_existent')
        assert result is False

        # Test deleting existing profile
        result = config_manager.delete_profile('valid_profile')
        assert result is True
        assert config_manager.get_profile('valid_profile') is None


class TestPerformanceIntegration(BaseIntegrationTest):
    """Test performance monitoring integration."""

    def test_performance_monitor_config_integration(self):
        """Test that performance monitoring integrates with configuration."""
        from app.managers.performance_monitor import get_performance_monitor

        config_manager = self.create_test_config_manager()
        perf_monitor = get_performance_monitor()

        # Performance monitor should be available
        assert perf_monitor is not None

        # Test that config manager can save performance-related settings
        config_manager.config['performance_logging'] = True
        config_manager.config['memory_threshold_mb'] = 500

        # Save and reload
        config_manager.save_config()
        new_manager = ConfigManager(config_manager.config_path)

        # Verify performance settings persist
        assert new_manager.config.get('performance_logging') is True
        assert new_manager.config.get('memory_threshold_mb') == 500

