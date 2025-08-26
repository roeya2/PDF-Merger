"""
Tests for the Recent Folders Manager

This module contains tests for the recent folders functionality.
"""

import unittest
from unittest.mock import Mock, patch
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta

from app.utils.constants import RECENT_FOLDERS_KEY
from app.managers.recent_folders_manager import (
    RecentFolder, RecentFoldersManager,
    get_recent_folders_manager, add_recent_folder, get_quick_access_folders
)
from app.managers.config_manager import ConfigManager


class TestRecentFolder(unittest.TestCase):
    """Test cases for the RecentFolder class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_path = self.temp_dir / "test_folder"
        self.test_path.mkdir()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.test_path.exists():
            shutil.rmtree(self.test_path, ignore_errors=True)
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_recent_folder_creation(self):
        """Test creating a RecentFolder."""
        folder = RecentFolder(str(self.test_path), "Test Folder")

        self.assertEqual(folder.path, str(self.test_path))
        self.assertEqual(folder.name, "Test Folder")
        self.assertIsInstance(folder.last_accessed, datetime)
        self.assertEqual(folder.access_count, 1)
        self.assertFalse(folder.is_favorite)

    def test_recent_folder_exists(self):
        """Test checking if folder exists."""
        folder = RecentFolder(str(self.test_path))
        self.assertTrue(folder.exists())

        nonexistent_path = self.temp_dir / "nonexistent"
        folder_nonexistent = RecentFolder(str(nonexistent_path))
        self.assertFalse(folder_nonexistent.exists())

    def test_recent_folder_to_dict(self):
        """Test converting RecentFolder to dictionary."""
        folder = RecentFolder(str(self.test_path), "Test Folder")
        folder.access_count = 5
        folder.is_favorite = True

        data = folder.to_dict()

        self.assertEqual(data['path'], str(self.test_path))
        self.assertEqual(data['name'], "Test Folder")
        self.assertEqual(data['access_count'], 5)
        self.assertTrue(data['is_favorite'])

    def test_recent_folder_from_dict(self):
        """Test creating RecentFolder from dictionary."""
        data = {
            'path': str(self.test_path),
            'name': 'Test Folder',
            'last_accessed': datetime.now().isoformat(),
            'access_count': 3,
            'is_favorite': True
        }

        folder = RecentFolder.from_dict(data)

        self.assertEqual(folder.path, str(self.test_path))
        self.assertEqual(folder.name, 'Test Folder')
        self.assertEqual(folder.access_count, 3)
        self.assertTrue(folder.is_favorite)

    def test_get_display_name(self):
        """Test getting display name."""
        # Same name as folder
        folder = RecentFolder(str(self.test_path))
        self.assertEqual(folder.get_display_name(), self.test_path.name)

        # Different display name
        folder_custom = RecentFolder(str(self.test_path), "Custom Name")
        self.assertEqual(folder_custom.get_display_name(), f"Custom Name ({self.test_path.name})")

    def test_get_short_path(self):
        """Test getting shortened path."""
        # Short path
        short_path = self.temp_dir / "short"
        short_path.mkdir()
        folder_short = RecentFolder(str(short_path))
        self.assertEqual(folder_short.get_short_path(), str(short_path))

        # Long path
        long_path = self.temp_dir / "very" / "long" / "path" / "to" / "folder"
        long_path.mkdir(parents=True)
        folder_long = RecentFolder(str(long_path))
        short_version = folder_long.get_short_path(20)
        self.assertTrue(len(short_version) <= 20)
        self.assertTrue(short_version.startswith("..."))


class TestRecentFoldersManager(unittest.TestCase):
    """Test cases for the RecentFoldersManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.config = {}
        self.config_manager.update_config = Mock()

        self.manager = RecentFoldersManager(self.config_manager)

        # Create test folders
        self.folder1 = self.temp_dir / "folder1"
        self.folder2 = self.temp_dir / "folder2"
        self.folder3 = self.temp_dir / "folder3"
        self.folder1.mkdir()
        self.folder2.mkdir()
        self.folder3.mkdir()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        for folder in [self.folder1, self.folder2, self.folder3]:
            if folder.exists():
                shutil.rmtree(folder, ignore_errors=True)
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_folder_new(self):
        """Test adding a new folder."""
        self.manager.add_folder(str(self.folder1))

        self.assertEqual(len(self.manager.recent_folders), 1)
        self.assertEqual(self.manager.recent_folders[0].path, str(self.folder1))
        self.config_manager.update_config.assert_called_once()

    def test_add_folder_existing(self):
        """Test adding an existing folder updates it."""
        self.manager.add_folder(str(self.folder1))
        original_time = self.manager.recent_folders[0].last_accessed

        # Add again
        self.manager.add_folder(str(self.folder1))

        self.assertEqual(len(self.manager.recent_folders), 1)
        self.assertEqual(self.manager.recent_folders[0].access_count, 2)
        # Should be moved to front
        self.assertEqual(self.manager.recent_folders[0].path, str(self.folder1))

    def test_add_folder_nonexistent(self):
        """Test adding a non-existent folder does nothing."""
        nonexistent = self.temp_dir / "nonexistent"
        self.manager.add_folder(str(nonexistent))

        self.assertEqual(len(self.manager.recent_folders), 0)

    def test_remove_folder(self):
        """Test removing a folder."""
        self.manager.add_folder(str(self.folder1))
        self.manager.add_folder(str(self.folder2))

        self.assertEqual(len(self.manager.recent_folders), 2)

        self.manager.remove_folder(str(self.folder1))

        self.assertEqual(len(self.manager.recent_folders), 1)
        self.assertEqual(self.manager.recent_folders[0].path, str(self.folder2))

    def test_clear_all(self):
        """Test clearing all folders."""
        self.manager.add_folder(str(self.folder1))
        self.manager.add_folder(str(self.folder2))

        self.manager.clear_all()

        self.assertEqual(len(self.manager.recent_folders), 0)

    def test_get_recent_folders_valid_only(self):
        """Test getting only valid folders."""
        self.manager.add_folder(str(self.folder1))
        self.manager.add_folder(str(self.folder2))

        # Remove folder2 to make it invalid
        self.folder2.rmdir()

        valid_folders = self.manager.get_recent_folders(include_invalid=False)
        all_folders = self.manager.get_recent_folders(include_invalid=True)

        self.assertEqual(len(valid_folders), 1)
        self.assertEqual(len(all_folders), 2)

    def test_toggle_favorite(self):
        """Test toggling favorite status."""
        self.manager.add_folder(str(self.folder1))

        folder = self.manager.recent_folders[0]
        self.assertFalse(folder.is_favorite)

        self.manager.toggle_favorite(str(self.folder1))
        self.assertTrue(folder.is_favorite)

        self.manager.toggle_favorite(str(self.folder1))
        self.assertFalse(folder.is_favorite)

    def test_get_favorite_folders(self):
        """Test getting favorite folders."""
        self.manager.add_folder(str(self.folder1))
        self.manager.add_folder(str(self.folder2))
        self.manager.add_folder(str(self.folder3))

        self.manager.toggle_favorite(str(self.folder1))
        self.manager.toggle_favorite(str(self.folder2))

        favorites = self.manager.get_favorite_folders()

        self.assertEqual(len(favorites), 2)
        self.assertTrue(all(f.is_favorite for f in favorites))

    def test_get_quick_access_folders(self):
        """Test getting quick access folders."""
        # Add multiple folders
        for i in range(8):
            folder = self.temp_dir / f"folder{i}"
            folder.mkdir(exist_ok=True)
            self.manager.add_folder(str(folder))

        # Make first two favorites
        self.manager.toggle_favorite(str(self.temp_dir / "folder0"))
        self.manager.toggle_favorite(str(self.temp_dir / "folder1"))

        quick_access = self.manager.get_quick_access_folders()

        # Should have favorites first, then recent non-favorites
        self.assertEqual(len(quick_access), 7)  # 2 favorites + 5 recent
        self.assertTrue(quick_access[0]['is_favorite'])
        self.assertTrue(quick_access[1]['is_favorite'])

    def test_cleanup_invalid_folders(self):
        """Test cleaning up invalid folders."""
        self.manager.add_folder(str(self.folder1))
        self.manager.add_folder(str(self.folder2))

        # Remove folder2
        self.folder2.rmdir()

        self.manager.cleanup_invalid_folders()

        valid_folders = self.manager.get_recent_folders()
        self.assertEqual(len(valid_folders), 1)
        self.assertEqual(valid_folders[0].path, str(self.folder1))

    def test_get_folder_stats(self):
        """Test getting folder statistics."""
        self.manager.add_folder(str(self.folder1))
        self.manager.add_folder(str(self.folder2))

        # Make one favorite and access it multiple times
        self.manager.toggle_favorite(str(self.folder1))
        self.manager.add_folder(str(self.folder1))  # Increases access count

        stats = self.manager.get_folder_stats()

        self.assertEqual(stats['total_folders'], 2)
        self.assertEqual(stats['valid_folders'], 2)
        self.assertEqual(stats['favorite_folders'], 1)
        self.assertEqual(stats['most_accessed'], 2)  # folder1 was accessed twice


class TestRecentFoldersFunctions(unittest.TestCase):
    """Test cases for recent folders convenience functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.config = {}

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.rmdir()

    def test_get_recent_folders_manager_singleton(self):
        """Test that get_recent_folders_manager returns a singleton."""
        # Initialize the manager first
        from app.managers.config_manager import ConfigManager
        from app.managers.recent_folders_manager import initialize_recent_folders_manager
        config_manager = ConfigManager()
        initialize_recent_folders_manager(config_manager)

        # Test the actual singleton behavior
        manager1 = get_recent_folders_manager()
        manager2 = get_recent_folders_manager()

        # Should be the same instance
        self.assertEqual(manager1, manager2)
        self.assertIsNotNone(manager1)
        self.assertIsInstance(manager1, RecentFoldersManager)

    @patch('app.managers.recent_folders_manager.get_recent_folders_manager')
    def test_add_recent_folder_function(self, mock_get_manager):
        """Test the add_recent_folder convenience function."""
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        add_recent_folder("/test/path")

        mock_manager.add_folder.assert_called_once_with("/test/path")

    @patch('app.managers.recent_folders_manager.get_recent_folders_manager')
    def test_get_quick_access_folders_function(self, mock_get_manager):
        """Test the get_quick_access_folders convenience function."""
        mock_manager = Mock()
        mock_manager.get_quick_access_folders.return_value = [{"path": "/test"}]
        mock_get_manager.return_value = mock_manager

        result = get_quick_access_folders()

        self.assertEqual(result, [{"path": "/test"}])
        mock_manager.get_quick_access_folders.assert_called_once()


if __name__ == '__main__':
    unittest.main()
