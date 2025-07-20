import unittest
from unittest.mock import Mock, patch
from app.app_core import AppCore

class TestErrorHandling(unittest.TestCase):

    def setUp(self):
        self.app = Mock()
        self.app_core = AppCore(self.app)

    def test_handle_file_not_found_error(self):
        """Test that a 'file_not_found' error is handled correctly."""
        error_message = "path/to/nonexistent/file.pdf"
        self.app_core._handle_task_error(("file_not_found", error_message))
        self.app.show_message.assert_called_once_with(
            "File Not Found",
            f"The following file could not be found:\n\n{error_message}",
            "error"
        )

    def test_handle_permission_denied_error(self):
        """Test that a 'permission_denied' error is handled correctly."""
        error_message = "path/to/protected/file.pdf"
        self.app_core._handle_task_error(("permission_denied", error_message))
        self.app.show_message.assert_called_once_with(
            "Permission Denied",
            f"You do not have permission to access the following file:\n\n{error_message}",
            "error"
        )

if __name__ == '__main__':
    unittest.main()
