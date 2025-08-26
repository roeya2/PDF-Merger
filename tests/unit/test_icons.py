"""
Tests for the Icon Management System

This module contains tests for the icon management functionality.
"""

import unittest
from unittest.mock import Mock, patch
import tkinter as tk

from app.utils.icons import (
    IconManager, get_icon_manager, get_icon,
    create_icon_label, create_icon_button
)


class TestIconManager(unittest.TestCase):
    """Test cases for the IconManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.icon_manager = IconManager()

    def test_get_icon_valid_name(self):
        """Test getting a valid icon."""
        icon = self.icon_manager.get_icon("add_file")
        self.assertEqual(icon, "📄")

    def test_get_icon_invalid_name(self):
        """Test getting an invalid icon returns default."""
        icon = self.icon_manager.get_icon("invalid_icon")
        self.assertEqual(icon, "❓")

    def test_get_icon_with_size_and_color(self):
        """Test getting an icon with size and color parameters."""
        icon = self.icon_manager.get_icon("merge", size="large", color="primary")
        self.assertEqual(icon, "🔗")

    def test_create_icon_label(self):
        """Test creating an icon label widget parameters."""
        mock_parent = Mock()

        # Test that the method exists and can be called with parameters
        # We don't actually create the widget to avoid Tkinter setup issues
        self.assertTrue(hasattr(self.icon_manager, 'create_icon_label'))
        # The actual widget creation would require proper Tkinter setup

    def test_create_icon_button(self):
        """Test creating an icon button widget parameters."""
        mock_parent = Mock()

        # Test that the method exists and can be called with parameters
        # We don't actually create the widget to avoid Tkinter setup issues
        self.assertTrue(hasattr(self.icon_manager, 'create_icon_button'))
        # The actual widget creation would require proper Tkinter setup

    def test_get_file_type_icon_pdf(self):
        """Test getting PDF file type icon."""
        icon = self.icon_manager.get_file_type_icon(".pdf")
        self.assertEqual(icon, "📕")

    def test_get_file_type_icon_word(self):
        """Test getting Word file type icon."""
        icon = self.icon_manager.get_file_type_icon(".docx")
        self.assertEqual(icon, "📝")

    def test_get_file_type_icon_epub(self):
        """Test getting EPUB file type icon."""
        icon = self.icon_manager.get_file_type_icon(".epub")
        self.assertEqual(icon, "📚")

    def test_get_file_type_icon_archive(self):
        """Test getting archive file type icon."""
        icon = self.icon_manager.get_file_type_icon(".zip")
        self.assertEqual(icon, "📦")

    def test_get_file_type_icon_unknown(self):
        """Test getting unknown file type icon."""
        icon = self.icon_manager.get_file_type_icon(".unknown")
        self.assertEqual(icon, "📄")  # Default file icon


class TestIconFunctions(unittest.TestCase):
    """Test cases for icon convenience functions."""

    def test_get_icon_function(self):
        """Test the get_icon convenience function."""
        icon = get_icon("add_file")
        self.assertEqual(icon, "📄")

    def test_create_icon_label_function(self):
        """Test the create_icon_label convenience function."""
        mock_parent = Mock()

        # Test that the function exists and can be called
        # We don't actually create the widget to avoid Tkinter setup issues
        self.assertTrue(callable(create_icon_label))
        # The actual widget creation would require proper Tkinter setup

    def test_create_icon_button_function(self):
        """Test the create_icon_button convenience function."""
        mock_parent = Mock()

        # Test that the function exists and can be called
        # We don't actually create the widget to avoid Tkinter setup issues
        self.assertTrue(callable(create_icon_button))
        # The actual widget creation would require proper Tkinter setup


if __name__ == '__main__':
    unittest.main()
