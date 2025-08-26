"""
Tests for the Metadata Manager

This module contains tests for the metadata management functionality.
"""

import unittest
from unittest.mock import Mock, patch
import tempfile
from pathlib import Path

from app.managers.metadata_manager import (
    MetadataManager, MetadataValidator,
    get_metadata_manager, initialize_metadata_manager
)
from app.managers.config_manager import ConfigManager
from app.utils.constants import DEFAULT_METADATA


class TestMetadataValidator(unittest.TestCase):
    """Test cases for the MetadataValidator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = MetadataValidator()

    def test_validate_title_valid(self):
        """Test validating valid title."""
        errors = self.validator.validate_title("A Valid Title")
        self.assertEqual(len(errors), 0)

    def test_validate_title_too_long(self):
        """Test validating title that is too long."""
        long_title = "A" * 300  # Exceeds max length
        errors = self.validator.validate_title(long_title)
        self.assertGreater(len(errors), 0)
        self.assertIn("too long", errors[0].lower())

    def test_validate_author_valid(self):
        """Test validating valid author."""
        errors = self.validator.validate_author("John Doe")
        self.assertEqual(len(errors), 0)

    def test_validate_author_too_long(self):
        """Test validating author that is too long."""
        long_author = "A" * 200  # Exceeds max length
        errors = self.validator.validate_author(long_author)
        self.assertGreater(len(errors), 0)
        self.assertIn("too long", errors[0].lower())

    def test_validate_subject_valid(self):
        """Test validating valid subject."""
        errors = self.validator.validate_subject("A valid subject description")
        self.assertEqual(len(errors), 0)

    def test_validate_keywords_valid(self):
        """Test validating valid keywords."""
        errors = self.validator.validate_keywords("keyword1, keyword2, keyword3")
        self.assertEqual(len(errors), 0)

    def test_validate_keywords_too_long(self):
        """Test validating keywords that are too long."""
        long_keywords = "keyword," * 300  # Exceeds max length
        errors = self.validator.validate_keywords(long_keywords)
        self.assertGreater(len(errors), 0)
        self.assertIn("too long", errors[0].lower())

    def test_validate_all_valid(self):
        """Test validating all valid metadata."""
        metadata = {
            'title': 'Valid Title',
            'author': 'Valid Author',
            'subject': 'Valid Subject',
            'keywords': 'valid, keywords, here'
        }

        validation_results = self.validator.validate_all(metadata)

        for field, errors in validation_results.items():
            self.assertEqual(len(errors), 0, f"Field {field} should have no errors")

    def test_validate_all_invalid(self):
        """Test validating all invalid metadata."""
        metadata = {
            'title': 'A' * 300,  # Too long
            'author': 'A' * 200,  # Too long
            'subject': '',  # Empty subject
            'keywords': 'A' * 2000  # Too long
        }

        validation_results = self.validator.validate_all(metadata)

        # Should have errors for title, author, and keywords
        self.assertGreater(len(validation_results['title']), 0)
        self.assertGreater(len(validation_results['author']), 0)
        self.assertGreater(len(validation_results['subject']), 0)
        self.assertGreater(len(validation_results['keywords']), 0)

    def test_is_valid_true(self):
        """Test is_valid returns True for valid metadata."""
        metadata = {
            'title': 'Valid Title',
            'author': 'Valid Author',
            'subject': 'Valid Subject',
            'keywords': 'valid, keywords'
        }

        self.assertTrue(self.validator.is_valid(metadata))

    def test_is_valid_false(self):
        """Test is_valid returns False for invalid metadata."""
        metadata = {
            'title': 'A' * 300,  # Too long
            'author': 'Valid Author',
            'subject': 'Valid Subject',
            'keywords': 'valid, keywords'
        }

        self.assertFalse(self.validator.is_valid(metadata))


class TestMetadataManager(unittest.TestCase):
    """Test cases for the MetadataManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = MetadataManager()
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        self.test_dir.rmdir()

    def test_initialization(self):
        """Test manager initialization."""
        self.assertIsInstance(self.manager, MetadataManager)
        self.assertIsNotNone(self.manager.current_metadata)
        self.assertEqual(self.manager.current_metadata['title'], '')

    def test_set_metadata_valid(self):
        """Test setting valid metadata."""
        metadata = {
            'title': 'Test Title',
            'author': 'Test Author',
            'subject': 'Test Subject',
            'keywords': 'test, keywords'
        }

        result = self.manager.set_metadata(metadata)

        self.assertTrue(result)
        self.assertEqual(self.manager.current_metadata['title'], 'Test Title')
        self.assertEqual(self.manager.current_metadata['author'], 'Test Author')

    def test_set_metadata_invalid(self):
        """Test setting invalid metadata."""
        metadata = {
            'title': 'A' * 300,  # Too long
            'author': 'Test Author',
            'subject': 'Test Subject',
            'keywords': 'test, keywords'
        }

        result = self.manager.set_metadata(metadata)

        self.assertFalse(result)
        self.assertEqual(self.manager.current_metadata['title'], '')  # Should remain unchanged

    def test_get_metadata(self):
        """Test getting current metadata."""
        metadata = self.manager.get_metadata()
        self.assertIsInstance(metadata, dict)
        self.assertIn('title', metadata)
        self.assertIn('author', metadata)

    def test_get_field(self):
        """Test getting a specific field."""
        self.manager.current_metadata['title'] = 'Test Title'
        title = self.manager.get_field('title')
        self.assertEqual(title, 'Test Title')

    def test_set_field_valid(self):
        """Test setting a valid field."""
        result = self.manager.set_field('title', 'New Title')
        self.assertTrue(result)
        self.assertEqual(self.manager.current_metadata['title'], 'New Title')

    def test_set_field_invalid(self):
        """Test setting an invalid field."""
        long_title = 'A' * 300
        result = self.manager.set_field('title', long_title)
        self.assertFalse(result)
        self.assertEqual(self.manager.current_metadata['title'], '')  # Should remain unchanged

    def test_set_field_invalid_name(self):
        """Test setting a non-existent field."""
        result = self.manager.set_field('nonexistent_field', 'value')
        self.assertFalse(result)

    def test_reset_to_defaults(self):
        """Test resetting metadata to defaults."""
        # First set some values
        self.manager.set_field('title', 'Custom Title')
        self.assertEqual(self.manager.current_metadata['title'], 'Custom Title')

        # Then reset
        self.manager.reset_to_defaults()
        self.assertEqual(self.manager.current_metadata['title'], '')

    def test_clear_field(self):
        """Test clearing a specific field."""
        self.manager.set_field('title', 'Test Title')
        self.assertEqual(self.manager.current_metadata['title'], 'Test Title')

        self.manager.clear_field('title')
        self.assertEqual(self.manager.current_metadata['title'], '')

    def test_clear_all(self):
        """Test clearing all metadata fields."""
        # Set some values
        self.manager.set_field('title', 'Test Title')
        self.manager.set_field('author', 'Test Author')
        self.manager.set_field('subject', 'Test Subject')

        self.manager.clear_all()

        # Creator and producer should remain
        self.assertNotEqual(self.manager.current_metadata['creator'], '')
        self.assertNotEqual(self.manager.current_metadata['producer'], '')

        # Others should be cleared
        self.assertEqual(self.manager.current_metadata['title'], '')
        self.assertEqual(self.manager.current_metadata['author'], '')
        self.assertEqual(self.manager.current_metadata['subject'], '')

    def test_get_field_info(self):
        """Test getting field information."""
        info = self.manager.get_field_info('title')
        self.assertIn('label', info)
        self.assertIn('description', info)
        self.assertEqual(info['label'], 'Title')

    def test_get_all_field_info(self):
        """Test getting information for all fields."""
        field_info = self.manager.get_all_field_info()
        self.assertIsInstance(field_info, dict)
        self.assertIn('title', field_info)
        self.assertIn('author', field_info)

    def test_get_validation_errors(self):
        """Test getting validation errors."""
        # Set invalid data
        self.manager.current_metadata['title'] = 'A' * 300  # Too long

        errors = self.manager.get_validation_errors()
        self.assertIn('title', errors)
        self.assertGreater(len(errors['title']), 0)

    def test_format_keywords_for_display(self):
        """Test formatting keywords for display."""
        keywords = "keyword1,keyword2,   keyword3  "
        formatted = self.manager.format_keywords_for_display(keywords)
        self.assertEqual(formatted, "keyword1, keyword2, keyword3")

    def test_format_keywords_for_storage(self):
        """Test formatting keywords for storage."""
        keywords = "  keyword1,  keyword2  ,  keyword3  "
        formatted = self.manager.format_keywords_for_storage(keywords)
        self.assertEqual(formatted, "keyword1, keyword2, keyword3")

    def test_get_metadata_summary(self):
        """Test getting metadata summary."""
        # Set some values
        self.manager.set_field('title', 'Test Title')
        self.manager.set_field('author', 'Test Author')

        summary = self.manager.get_metadata_summary()

        self.assertIn('total_fields', summary)
        self.assertIn('filled_fields', summary)
        self.assertIn('has_errors', summary)
        self.assertEqual(summary['filled_fields'], 4)  # title, author, creator, producer

    def test_export_metadata(self):
        """Test exporting metadata in different formats."""
        # Set some test data
        self.manager.set_field('title', 'Test Title')
        self.manager.set_field('author', 'Test Author')

        # Test dict format
        dict_export = self.manager.export_metadata('dict')
        self.assertIsInstance(dict_export, dict)
        self.assertEqual(dict_export['title'], 'Test Title')

        # Test list format
        list_export = self.manager.export_metadata('list')
        self.assertIsInstance(list_export, list)
        self.assertGreater(len(list_export), 0)

        # Test CSV format
        csv_export = self.manager.export_metadata('csv')
        self.assertIsInstance(csv_export, str)
        self.assertIn('Test Title', csv_export)

        # Test invalid format
        with self.assertRaises(ValueError):
            self.manager.export_metadata('invalid')

    def test_save_to_config(self):
        """Test saving metadata to config."""
        config_manager = Mock()
        config_manager.update_config = Mock()

        # Set some test data
        self.manager.set_field('title', 'Test Title')

        result = self.manager.save_to_config(config_manager)
        self.assertTrue(result)

        # Verify the config was updated
        config_manager.update_config.assert_called_once()

    def test_load_from_config(self):
        """Test loading metadata from config."""
        config_manager = Mock(spec=ConfigManager)
        config_manager.config = {
            'default_metadata': {
                'title': 'Loaded Title',
                'author': 'Loaded Author'
            }
        }

        result = self.manager.load_from_config(config_manager)
        self.assertTrue(result)
        self.assertEqual(self.manager.current_metadata['title'], 'Loaded Title')
        self.assertEqual(self.manager.current_metadata['author'], 'Loaded Author')


class TestMetadataManagerFunctions(unittest.TestCase):
    """Test cases for metadata manager convenience functions."""

    def test_initialize_metadata_manager(self):
        """Test initializing the global manager."""
        manager = initialize_metadata_manager()

        self.assertIsInstance(manager, MetadataManager)
        self.assertIsNotNone(manager)

    def test_get_metadata_manager(self):
        """Test getting the global manager."""
        # First initialize
        initialize_metadata_manager()

        # Then get it
        manager = get_metadata_manager()

        self.assertIsInstance(manager, MetadataManager)
        self.assertIsNotNone(manager)


if __name__ == '__main__':
    unittest.main()
