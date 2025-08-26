"""
Tests for the Advanced Compression Manager

This module contains tests for the advanced compression functionality.
"""

import unittest
from unittest.mock import Mock

from app.managers.advanced_compression_manager import (
    CompressionProfile, AdvancedCompressionManager,
    get_advanced_compression_manager, initialize_advanced_compression_manager
)


class TestCompressionProfile(unittest.TestCase):
    """Test cases for the CompressionProfile class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'name': 'Test Compression',
            'description': 'A test compression profile',
            'pypdf_level': 2,
            'estimated_ratio': '70-85%',
            'speed': 'Medium',
            'recommended_use': ['general', 'mixed']
        }

    def test_compression_profile_creation(self):
        """Test creating a CompressionProfile."""
        profile = CompressionProfile('test_profile', self.config)

        self.assertEqual(profile.profile_id, 'test_profile')
        self.assertEqual(profile.name, 'Test Compression')
        self.assertEqual(profile.description, 'A test compression profile')
        self.assertEqual(profile.pypdf_level, 2)
        self.assertEqual(profile.estimated_ratio, '70-85%')
        self.assertEqual(profile.speed, 'Medium')

    def test_get_settings(self):
        """Test getting profile settings."""
        profile = CompressionProfile('test_profile', self.config)
        settings = profile.get_settings()

        expected_settings = {
            'compression_level': 'test_profile',
            'pypdf_level': 2,
            'image_compression': 'auto',
            'text_compression': True,
            'font_optimization': True,
            'structure_optimization': True
        }

        self.assertEqual(settings, expected_settings)

    def test_get_display_info(self):
        """Test getting display information."""
        profile = CompressionProfile('test_profile', self.config)
        display_info = profile.get_display_info()

        expected_info = {
            'id': 'test_profile',
            'name': 'Test Compression',
            'description': 'A test compression profile',
            'estimated_ratio': '70-85%',
            'speed': 'Medium',
            'pypdf_level': 2
        }

        self.assertEqual(display_info, expected_info)

    def test_estimate_file_size_single_page(self):
        """Test estimating file size for single page."""
        profile = CompressionProfile('test_profile', self.config)
        original_size = 1000000  # 1 MB

        estimated_size, description = profile.estimate_file_size(original_size, 1)

        self.assertLess(estimated_size, original_size)
        self.assertIn('70-85%', description)

    def test_estimate_file_size_multiple_pages(self):
        """Test estimating file size for multiple pages."""
        profile = CompressionProfile('test_profile', self.config)
        original_size = 1000000  # 1 MB

        # Single page
        size_1, _ = profile.estimate_file_size(original_size, 1)
        # Multiple pages (more than 10 to trigger page factor)
        size_20, _ = profile.estimate_file_size(original_size, 20)

        # Multiple pages should have better compression ratio
        self.assertLess(size_20, size_1)


class TestAdvancedCompressionManager(unittest.TestCase):
    """Test cases for the AdvancedCompressionManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = AdvancedCompressionManager()

    def test_initialization(self):
        """Test manager initialization."""
        self.assertIsInstance(self.manager, AdvancedCompressionManager)
        self.assertGreater(len(self.manager.profiles), 0)

    def test_get_profile(self):
        """Test getting a profile by ID."""
        profile = self.manager.get_profile('normal')
        self.assertIsNotNone(profile)
        self.assertEqual(profile.profile_id, 'normal')

    def test_get_profile_invalid(self):
        """Test getting a non-existent profile."""
        profile = self.manager.get_profile('nonexistent')
        self.assertIsNone(profile)

    def test_get_all_profiles(self):
        """Test getting all profiles."""
        profiles = self.manager.get_all_profiles()
        self.assertGreater(len(profiles), 0)
        self.assertIsInstance(profiles[0], CompressionProfile)

    def test_get_profile_ids(self):
        """Test getting all profile IDs."""
        profile_ids = self.manager.get_profile_ids()
        self.assertGreater(len(profile_ids), 0)
        self.assertIn('normal', profile_ids)
        self.assertIn('maximum', profile_ids)

    def test_set_current_profile_valid(self):
        """Test setting a valid current profile."""
        result = self.manager.set_current_profile('high')
        self.assertTrue(result)
        self.assertEqual(self.manager.current_profile, 'high')

    def test_set_current_profile_invalid(self):
        """Test setting an invalid current profile."""
        result = self.manager.set_current_profile('nonexistent')
        self.assertFalse(result)
        self.assertIsNone(self.manager.current_profile)

    def test_get_current_profile(self):
        """Test getting the current profile."""
        self.manager.set_current_profile('fast')
        current = self.manager.get_current_profile()

        self.assertIsNotNone(current)
        self.assertEqual(current.profile_id, 'fast')

    def test_get_current_profile_none_set(self):
        """Test getting current profile when none is set."""
        current = self.manager.get_current_profile()
        self.assertIsNone(current)

    def test_get_settings_for_profile(self):
        """Test getting settings for a specific profile."""
        settings = self.manager.get_settings_for_profile('maximum')

        self.assertEqual(settings['compression_level'], 'maximum')
        self.assertEqual(settings['pypdf_level'], 4)
        self.assertTrue(settings['text_compression'])

    def test_get_current_settings_no_profile(self):
        """Test getting current settings when no profile is set."""
        settings = self.manager.get_current_settings()
        self.assertEqual(settings['compression_level'], 'normal')  # Default

    def test_update_custom_settings(self):
        """Test updating custom settings."""
        custom_settings = {
            'image_compression': 'lossless',
            'text_compression': False,
            'custom_setting': 'ignored'  # Should be ignored
        }

        self.manager.update_custom_settings(custom_settings)

        # Check that valid settings were updated
        self.assertEqual(len(self.manager.custom_settings), 2)
        self.assertEqual(self.manager.custom_settings['image_compression'], 'lossless')
        self.assertEqual(self.manager.custom_settings['text_compression'], False)

    def test_reset_custom_settings(self):
        """Test resetting custom settings."""
        # First set some custom settings
        self.manager.update_custom_settings({'image_compression': 'lossy'})
        self.assertGreater(len(self.manager.custom_settings), 0)

        # Then reset
        self.manager.reset_custom_settings()
        self.assertEqual(len(self.manager.custom_settings), 0)

    def test_get_compression_estimate(self):
        """Test getting compression size estimate."""
        estimate = self.manager.get_compression_estimate('maximum', 1000000, 1)

        self.assertIn('profile_id', estimate)
        self.assertIn('estimated_size', estimate)
        self.assertIn('savings_bytes', estimate)
        self.assertEqual(estimate['profile_id'], 'maximum')
        self.assertLess(estimate['estimated_size'], 1000000)  # Should be smaller

    def test_compare_profiles(self):
        """Test comparing multiple profiles."""
        comparisons = self.manager.compare_profiles(['none', 'normal', 'maximum'], 1000000, 1)

        self.assertEqual(len(comparisons), 3)
        # Should be sorted by estimated size (smallest first)
        self.assertEqual(comparisons[0]['profile_id'], 'maximum')  # Most compression
        self.assertEqual(comparisons[-1]['profile_id'], 'none')    # Least compression

    def test_get_recommended_profile(self):
        """Test getting recommended profile for criteria."""
        recommended = self.manager.get_recommended_profile({'speed': 'high'})
        self.assertEqual(recommended, 'none')

        recommended = self.manager.get_recommended_profile({'size': 'high'})
        self.assertEqual(recommended, 'maximum')

        recommended = self.manager.get_recommended_profile({})  # Default
        self.assertEqual(recommended, 'normal')

    def test_validate_compression_settings_valid(self):
        """Test validating valid compression settings."""
        settings = {
            'compression_level': 'normal',
            'image_compression': 'auto',
            'text_compression': True,
            'font_optimization': True,
            'structure_optimization': True
        }

        errors = self.manager.validate_compression_settings(settings)
        self.assertEqual(len(errors), 0)

    def test_validate_compression_settings_invalid(self):
        """Test validating invalid compression settings."""
        settings = {
            'compression_level': 'invalid_level',
            'image_compression': 'invalid_option',
            'text_compression': 'not_boolean'  # Should be boolean
        }

        errors = self.manager.validate_compression_settings(settings)
        self.assertGreater(len(errors), 0)

    def test_create_custom_profile(self):
        """Test creating a custom compression profile."""
        result = self.manager.create_custom_profile(
            'custom_test',
            'Custom Test Profile',
            'A custom compression profile',
            3,  # PyPDF level
            {'estimated_ratio': '50-70%', 'speed': 'Custom'}
        )

        self.assertTrue(result)
        self.assertIn('custom_test', self.manager.profiles)

        # Verify the custom profile
        custom_profile = self.manager.get_profile('custom_test')
        self.assertEqual(custom_profile.name, 'Custom Test Profile')
        self.assertEqual(custom_profile.pypdf_level, 3)

    def test_get_profile_statistics(self):
        """Test getting profile statistics."""
        stats = self.manager.get_profile_statistics()

        self.assertIn('total_profiles', stats)
        self.assertIn('available_profiles', stats)
        self.assertIn('custom_settings_count', stats)
        self.assertGreater(stats['total_profiles'], 0)

    def test_export_profile_settings(self):
        """Test exporting profile settings."""
        settings = self.manager.export_profile_settings('normal', 'dict')

        self.assertIsInstance(settings, dict)
        self.assertIn('compression_level', settings)
        self.assertIn('pypdf_level', settings)


class TestAdvancedCompressionFunctions(unittest.TestCase):
    """Test cases for advanced compression convenience functions."""

    def test_initialize_advanced_compression_manager(self):
        """Test initializing the global manager."""
        manager = initialize_advanced_compression_manager()

        self.assertIsInstance(manager, AdvancedCompressionManager)
        self.assertIsNotNone(manager)

    def test_get_advanced_compression_manager(self):
        """Test getting the global manager."""
        # First initialize
        initialize_advanced_compression_manager()

        # Then get it
        manager = get_advanced_compression_manager()

        self.assertIsInstance(manager, AdvancedCompressionManager)
        self.assertIsNotNone(manager)


if __name__ == '__main__':
    unittest.main()
