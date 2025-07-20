import unittest
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk
from app.action_panel import ActionPanel

class TestActionPanel(unittest.TestCase):

    def setUp(self):
        self.root = MagicMock()
        self.app = Mock()
        with patch('tkinter.ttk.LabelFrame'), patch('tkinter.ttk.Button'), \
             patch('tkinter.ttk.Progressbar'), patch('app.action_panel.Tooltip'):
            self.action_panel = ActionPanel(self.root, self.app)

    def tearDown(self):
        pass

    def test_progress_bar_update(self):
        """Test that the progress bar is updated correctly."""
        self.action_panel.progress_bar = MagicMock()
        self.action_panel.on_merge_completed(("path/to/file.pdf", 1.23))
        self.action_panel.progress_bar.__setitem__.assert_called_with('value', 100)

if __name__ == '__main__':
    unittest.main()
