import unittest
import os
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Mock the tkinter module before it's imported by other modules
import sys
mock_tkinter = MagicMock()
sys.modules['tkinter'] = mock_tkinter
sys.modules['tkinter.filedialog'] = mock_tkinter.filedialog
sys.modules['tkinter.messagebox'] = mock_tkinter.messagebox

from app.file_operations import FileOperations
from app.pdf_document import PDFDocument

class TestFileOperations(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.app_core = Mock()
        self.app_core.app = Mock()
        self.app_core.app.root = MagicMock()
        self.file_ops = FileOperations(self.app_core)

        # Create some dummy files
        self.pdf_path = os.path.join(self.test_dir, "test.pdf")
        self.word_path = os.path.join(self.test_dir, "test.docx")
        self.epub_path = os.path.join(self.test_dir, "test.epub")
        self.unsupported_path = os.path.join(self.test_dir, "test.txt")

        with open(self.pdf_path, "w") as f:
            f.write("dummy pdf content")
        with open(self.word_path, "w") as f:
            f.write("dummy word content")
        with open(self.epub_path, "w") as f:
            f.write("dummy epub content")
        with open(self.unsupported_path, "w") as f:
            f.write("dummy text content")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_request_add_files(self):
        """Test adding a list of files."""
        with patch.object(self.file_ops, 'process_add_files_task') as mock_task:
            self.file_ops.request_add_files([self.pdf_path, self.word_path])
            self.app_core.start_background_task.assert_called_once()
            # Check that the task was called with the correct arguments
            args, kwargs = self.app_core.start_background_task.call_args
            self.assertEqual(kwargs['args'], ([self.pdf_path, self.word_path],))

    def test_request_add_folder(self):
        """Test adding files from a folder."""
        with patch.object(self.file_ops, 'process_add_files_task') as mock_task:
            self.file_ops.request_add_folder(self.test_dir)
            self.app_core.start_background_task.assert_called_once()
            # Check that the task was called with all supported files in the folder
            args, kwargs = self.app_core.start_background_task.call_args
            self.assertIn(self.pdf_path, kwargs['args'][0])
            self.assertIn(self.word_path, kwargs['args'][0])
            self.assertIn(self.epub_path, kwargs['args'][0])
            self.assertNotIn(self.unsupported_path, kwargs['args'][0])

    @patch('app.file_operations.zipfile.ZipFile')
    def test_request_add_from_archive_zip(self, mock_zip):
        """Test adding files from a ZIP archive."""
        archive_path = os.path.join(self.test_dir, "test.zip")
        with open(archive_path, "w") as f:
            f.write("dummy zip content")

        with patch.object(self.file_ops, 'process_extract_from_archive_task') as mock_task:
            self.file_ops.request_add_from_archive(archive_path)
            self.app_core.start_background_task.assert_called_once_with(
                self.file_ops.process_extract_from_archive_task, args=(archive_path,)
            )

    @patch('app.file_operations.filedialog.asksaveasfilename')
    @patch('app.file_operations.filedialog.askopenfilename')
    def test_save_and_load_file_list(self, mock_askopenfilename, mock_asksaveasfilename):
        """Test saving and loading a file list."""
        # Mock the documents in the app_core
        with patch('app.pdf_document.pymupdf.open'), patch('app.pdf_document.PDFDocument.load_metadata'):
            doc1 = PDFDocument(self.pdf_path)
            doc1.page_count = 10
            doc1.selected_pages = [0, 1, 2]
            doc2 = PDFDocument(self.word_path)
            doc2.page_count = 5
            doc2.selected_pages = [3, 4]
            self.app_core.get_documents.return_value = [doc1, doc2]

        # Mock the file list panel to return the details for saving
        self.app_core.app.file_list_panel.get_file_list_details_for_save.return_value = [
            {"filepath": self.pdf_path, "selected_pages": [0, 1, 2]},
            {"filepath": self.word_path, "selected_pages": [3, 4]},
        ]

        # Mock the file dialog to return a path
        save_path = os.path.join(self.test_dir, "test_list.json")
        mock_asksaveasfilename.return_value = save_path

        # Test saving
        self.file_ops.save_file_list()

        # Check that the file was created and contains the correct data
        self.assertTrue(os.path.exists(save_path))
        with open(save_path, 'r') as f:
            data = json.load(f)
        self.assertEqual(len(data['pdf_merger_pro_list']), 2)
        self.assertEqual(data['pdf_merger_pro_list'][0]['filepath'], self.pdf_path)

        # Mock the file dialog for loading
        mock_askopenfilename.return_value = save_path

        # Test loading
        with patch.object(self.file_ops, 'process_load_list_task') as mock_task:
            self.file_ops.load_file_list()
            self.app_core.clear_documents.assert_called_once()
            self.app_core.start_background_task.assert_called_once()
            args, kwargs = self.app_core.start_background_task.call_args
            self.assertEqual(len(kwargs['args'][0]), 2)


if __name__ == '__main__':
    unittest.main()
