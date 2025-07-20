import unittest
from unittest.mock import Mock, patch
from app.app_core import AppCore
from app.pdf_document import PDFDocument

class TestAppCore(unittest.TestCase):

    def setUp(self):
        with patch('app.app_core.FileOperations') as mock_file_ops, \
             patch('app.app_core.ProfileManager') as mock_profile_manager:
            self.app = Mock()
            self.app.background_task = Mock()
            self.app.pdf_documents = []
            self.app_core = AppCore(self.app)
            self.app_core.file_ops = mock_file_ops
            self.app_core.profile_manager = mock_profile_manager

    def test_add_document(self):
        """Test adding a document to the AppCore."""
        with patch('app.pdf_document.pymupdf.open'), patch('app.pdf_document.PDFDocument.load_metadata'):
            doc = PDFDocument("dummy.pdf")
            self.app_core.add_documents_from_details([{'filepath': 'dummy.pdf'}])
            self.assertEqual(len(self.app_core.get_documents()), 1)
            self.app.update_ui.assert_called_once()

    def test_clear_documents(self):
        """Test clearing all documents from the AppCore."""
        with patch('app.pdf_document.pymupdf.open'), patch('app.pdf_document.PDFDocument.load_metadata'):
            doc1 = PDFDocument("dummy1.pdf")
            doc2 = PDFDocument("dummy2.pdf")
            self.app_core.app.pdf_documents = [doc1, doc2]
            self.app_core.clear_documents()
            self.assertEqual(len(self.app_core.get_documents()), 0)
            self.app.update_ui.assert_called_once()

    def test_start_background_task(self):
        """Test starting a background task."""
        target_func = Mock()
        self.app_core.start_background_task(target_func, args=(1, 2), kwargs={'a': 3})
        self.app.background_task.start.assert_called_once_with(target_func, (1, 2), {'a': 3})

    def test_handle_task_result_success(self):
        """Test handling a successful task result."""
        with patch.object(self.app_core, '_handle_task_success') as mock_handler:
            self.app.task_queue.get_nowait.return_value = ("success", "test_data")
            self.app.task_queue.empty.side_effect = [False, True]
            self.app_core.check_task_queue()
            mock_handler.assert_called_once_with("test_data")

    def test_handle_task_result_error(self):
        """Test handling an error task result."""
        with patch.object(self.app_core, '_handle_task_error') as mock_handler:
            self.app.task_queue.get_nowait.return_value = ("error", "test_error")
            self.app.task_queue.empty.side_effect = [False, True]
            self.app_core.check_task_queue()
            mock_handler.assert_called_once_with("test_error")


if __name__ == '__main__':
    unittest.main()
