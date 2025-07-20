import unittest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
from app.pdf_document import PDFDocument

class TestPDFDocument(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.pdf_path = os.path.join(self.test_dir, "test.pdf")
        with open(self.pdf_path, "w") as f:
            f.write("dummy pdf content")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('app.pdf_document.pymupdf.open')
    def test_load_metadata(self, mock_pymupdf_open):
        """Test that the PDF metadata is correctly loaded."""
        mock_doc = Mock()
        mock_doc.page_count = 10
        mock_doc.metadata = {"title": "Test PDF"}
        mock_pymupdf_open.return_value = mock_doc

        pdf_doc = PDFDocument(self.pdf_path)
        pdf_doc._pymupdf_doc = mock_doc
        pdf_doc.page_count = mock_doc.page_count
        pdf_doc.metadata = mock_doc.metadata
        self.assertEqual(pdf_doc.page_count, 10)
        self.assertEqual(pdf_doc.metadata["title"], "Test PDF")

    @patch('app.pdf_document.pymupdf.open')
    def test_get_preview(self, mock_pymupdf_open):
        """Test that a preview image can be generated."""
        mock_page = Mock()
        mock_page.get_pixmap.return_value.tobytes.return_value = b"image_data"
        mock_page.rect = Mock(width=100, height=100)
        mock_doc = Mock()
        mock_doc.page_count = 1
        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_pymupdf_open.return_value = mock_doc

        pdf_doc = PDFDocument(self.pdf_path)
        pdf_doc._pymupdf_doc = mock_doc
        pdf_doc.page_count = mock_doc.page_count
        preview_data, _ = pdf_doc.get_preview(0)
        self.assertEqual(preview_data, b"image_data")

    def test_get_file_size_str(self):
        """Test that the file size is correctly formatted."""
        pdf_doc = PDFDocument(self.pdf_path)
        # The dummy file is small, so it should be in bytes
        self.assertTrue(pdf_doc.get_file_size_str().endswith("Bytes"))

if __name__ == '__main__':
    unittest.main()
