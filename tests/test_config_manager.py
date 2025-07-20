import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import Mock, patch
from app.config_manager import ConfigManager
from pathlib import Path

class TestConfigManager(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_path = Path(self.test_dir) / "config.json"
        self.config_manager = ConfigManager(self.config_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_load_config_file_not_found(self):
        """Test that a default config is created if the file doesn't exist."""
        with patch('app.config_manager.Path.exists', return_value=False):
            self.config_manager.load_config()
            self.assertEqual(self.config_manager.config.get("theme", "system"), "system")

    def test_save_and_load_config(self):
        """Test saving and then loading the config."""
        self.config_manager.config["theme"] = "dark"
        self.config_manager.config["language"] = "fr"
        self.config_manager.save_config()

        new_config_manager = ConfigManager(self.config_path)
        new_config_manager.load_config()
        self.assertEqual(new_config_manager.config.get("theme"), "dark")
        self.assertEqual(new_config_manager.config.get("language"), "fr")

    def test_add_recent_directory(self):
        """Test adding a recent directory."""
        with patch('os.path.isdir', return_value=True):
            self.config_manager.add_recent_directory("/path/to/dir1")
            self.config_manager.add_recent_directory("/path/to/dir2")
            self.config_manager.add_recent_directory("/path/to/dir1")  # Should not add duplicates

        recent_dirs = self.config_manager.config.get("recent_directories")
        self.assertEqual(len(recent_dirs), 2)
        self.assertEqual(recent_dirs[0], "/path/to/dir1")
        self.assertEqual(recent_dirs[1], "/path/to/dir2")

if __name__ == '__main__':
    unittest.main()
