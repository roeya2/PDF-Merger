"""
Tests for the Quality Presets Manager

This module contains tests for the quality presets functionality.
"""

import unittest
from unittest.mock import Mock, patch
from pathlib import Path

from app.managers.quality_presets_manager import (
    QualityPreset, QualityPresetsManager,
    get_quality_presets_manager, initialize_quality_presets_manager
)
from app.managers.config_manager import ConfigManager


class TestQualityPreset(unittest.TestCase):
    """Test cases for the QualityPreset class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'name': 'Test Preset',
            'description': 'A test preset',
            'compression': 'maximum',
            'color_mode': 'Colorful (Original)',
            'dpi': '300',
            'preserve_bookmarks': True,
            'icon': '🧪'
        }

    def test_quality_preset_creation(self):
        """Test creating a QualityPreset."""
        preset = QualityPreset('test_preset', self.config)

        self.assertEqual(preset.preset_id, 'test_preset')
        self.assertEqual(preset.name, 'Test Preset')
        self.assertEqual(preset.description, 'A test preset')
        self.assertEqual(preset.icon, '🧪')

    def test_get_settings(self):
        """Test getting preset settings."""
        preset = QualityPreset('test_preset', self.config)
        settings = preset.get_settings()

        expected_settings = {
            'compression': 'maximum',
            'color_mode': 'Colorful (Original)',
            'dpi': '300',
            'preserve_bookmarks': True
        }

        self.assertEqual(settings, expected_settings)

    def test_get_display_info(self):
        """Test getting display information."""
        preset = QualityPreset('test_preset', self.config)
        display_info = preset.get_display_info()

        expected_info = {
            'id': 'test_preset',
            'name': 'Test Preset',
            'description': 'A test preset',
            'icon': '🧪'
        }

        self.assertEqual(display_info, expected_info)

    def test_get_compression_info(self):
        """Test getting compression information."""
        preset = QualityPreset('test_preset', self.config)
        compression_info = preset.get_compression_info()

        # Should return compression level info from constants
        self.assertIn('name', compression_info)
        self.assertIn('description', compression_info)
        self.assertEqual(compression_info['name'], 'Maximum Compression')


class TestQualityPresetsManager(unittest.TestCase):
    """Test cases for the QualityPresetsManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.config = {}
        self.config_manager.update_config = Mock()

        self.manager = QualityPresetsManager(self.config_manager)

    def test_initialization(self):
        """Test manager initialization."""
        self.assertIsInstance(self.manager, QualityPresetsManager)
        self.assertGreater(len(self.manager.presets), 0)

    def test_get_preset(self):
        """Test getting a preset by ID."""
        preset = self.manager.get_preset('web')
        self.assertIsNotNone(preset)
        self.assertEqual(preset.preset_id, 'web')

    def test_get_preset_invalid(self):
        """Test getting a non-existent preset."""
        preset = self.manager.get_preset('nonexistent')
        self.assertIsNone(preset)

    def test_get_all_presets(self):
        """Test getting all presets."""
        presets = self.manager.get_all_presets()
        self.assertGreater(len(presets), 0)
        self.assertIsInstance(presets[0], QualityPreset)

    def test_get_builtin_presets(self):
        """Test getting built-in presets."""
        builtin_presets = self.manager.get_builtin_presets()
        self.assertGreater(len(builtin_presets), 0)

        # Check that all built-in presets have expected properties
        for preset in builtin_presets:
            self.assertIsNotNone(preset.icon)
            self.assertIsNotNone(preset.description)

    def test_apply_preset_success(self):
        """Test applying a preset successfully."""
        output_settings = {}

        result = self.manager.apply_preset('web', output_settings)

        self.assertTrue(result)
        self.assertEqual(output_settings['compression'], 'maximum')
        self.assertEqual(output_settings['dpi'], '96')

    def test_apply_preset_invalid(self):
        """Test applying a non-existent preset."""
        output_settings = {}

        result = self.manager.apply_preset('nonexistent', output_settings)

        self.assertFalse(result)
        self.assertEqual(len(output_settings), 0)

    def test_create_custom_preset(self):
        """Test creating a custom preset."""
        settings = {
            'compression': 'high',
            'color_mode': 'Colorful (Original)',
            'dpi': '150',
            'preserve_bookmarks': False
        }

        result = self.manager.create_custom_preset(
            'custom_test',
            'Custom Test Preset',
            'A custom preset for testing',
            settings
        )

        self.assertTrue(result)
        self.assertIn('custom_test', self.manager.presets)

        # Verify the custom preset was created correctly
        custom_preset = self.manager.get_preset('custom_test')
        self.assertEqual(custom_preset.name, 'Custom Test Preset')
        self.assertEqual(custom_preset.icon, '⭐')  # Custom preset icon

    def test_create_custom_preset_duplicate(self):
        """Test creating a custom preset with existing ID."""
        settings = {
            'compression': 'normal',
            'color_mode': 'Colorful (Original)',
            'dpi': 'Original',
            'preserve_bookmarks': True
        }

        # Try to create a preset with the same ID as a built-in preset
        result = self.manager.create_custom_preset(
            'web',  # This already exists as a built-in preset
            'Duplicate Preset',
            'This should fail',
            settings
        )

        self.assertFalse(result)

    def test_delete_custom_preset(self):
        """Test deleting a custom preset."""
        # First create a custom preset
        settings = {'compression': 'normal', 'color_mode': 'Colorful (Original)'}
        self.manager.create_custom_preset('custom_delete', 'Delete Me', 'Test', settings)

        # Now delete it
        result = self.manager.delete_custom_preset('custom_delete')

        self.assertTrue(result)
        self.assertNotIn('custom_delete', self.manager.presets)

    def test_delete_builtin_preset(self):
        """Test that built-in presets cannot be deleted."""
        result = self.manager.delete_custom_preset('web')  # Built-in preset

        self.assertFalse(result)
        self.assertIn('web', self.manager.presets)  # Should still exist

    def test_get_recommended_preset(self):
        """Test getting recommended preset for use cases."""
        recommended = self.manager.get_recommended_preset('web')
        self.assertEqual(recommended, 'web')

        recommended = self.manager.get_recommended_preset('print')
        self.assertEqual(recommended, 'print')

        recommended = self.manager.get_recommended_preset('unknown')
        self.assertEqual(recommended, 'normal')  # Default fallback

    def test_validate_preset_settings_valid(self):
        """Test validating valid preset settings."""
        settings = {
            'compression': 'normal',
            'color_mode': 'Colorful (Original)',
            'dpi': '300',
            'preserve_bookmarks': True
        }

        errors = self.manager.validate_preset_settings(settings)
        self.assertEqual(len(errors), 0)

    def test_validate_preset_settings_invalid(self):
        """Test validating invalid preset settings."""
        settings = {
            'compression': 'invalid_compression',
            'color_mode': 'Invalid Mode',
            'dpi': '9999',
            'preserve_bookmarks': True
        }

        errors = self.manager.validate_preset_settings(settings)
        self.assertGreater(len(errors), 0)
        error_text = ' '.join(errors)
        self.assertIn('compression', error_text)
        self.assertIn('color', error_text)  # Check for 'color' instead of 'color_mode'

    def test_get_preset_statistics(self):
        """Test getting preset statistics."""
        stats = self.manager.get_preset_statistics()

        self.assertIn('total_presets', stats)
        self.assertIn('available_presets', stats)
        self.assertGreater(stats['total_presets'], 0)


class TestQualityPresetsFunctions(unittest.TestCase):
    """Test cases for quality presets convenience functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.config = {}

    def test_initialize_quality_presets_manager(self):
        """Test initializing the global manager."""
        manager = initialize_quality_presets_manager(self.config_manager)

        self.assertIsInstance(manager, QualityPresetsManager)
        self.assertIsNotNone(manager)

    def test_get_quality_presets_manager(self):
        """Test getting the global manager."""
        # First initialize
        initialize_quality_presets_manager(self.config_manager)

        # Then get it
        manager = get_quality_presets_manager()

        self.assertIsInstance(manager, QualityPresetsManager)
        self.assertIsNotNone(manager)


if __name__ == '__main__':
    unittest.main()
