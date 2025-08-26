"""
Tests for the File Type Detection System

This module contains tests for the file type detection functionality.
"""

import unittest
from unittest.mock import Mock, patch, mock_open
import tempfile
import os
from pathlib import Path

from app.utils.file_type_detector import (
    FileTypeDetector, get_file_type_detector,
    detect_file_type, validate_file_for_merge
)


class TestFileTypeDetector(unittest.TestCase):
    """Test cases for the FileTypeDetector class."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = FileTypeDetector()
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up test files
        for file_path in self.test_dir.glob("*"):
            if file_path.is_file():
                file_path.unlink()
        self.test_dir.rmdir()

    def test_detect_file_type_pdf(self):
        """Test detecting PDF file type."""
        pdf_path = self.test_dir / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\nTest PDF content")

        result = self.detector.detect_file_type(pdf_path)

        self.assertTrue(result['supported'])
        self.assertEqual(result['detected_type'], 'pdf')
        self.assertEqual(result['extension'], '.pdf')
        self.assertTrue(result['properties']['can_merge'])
        self.assertTrue(result['properties']['can_preview'])

    def test_detect_file_type_docx(self):
        """Test detecting DOCX file type."""
        docx_path = self.test_dir / "test.docx"
        # Create a mock DOCX file with ZIP signature
        docx_path.write_bytes(b"PK\x03\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00")

        result = self.detector.detect_file_type(docx_path)

        self.assertTrue(result['supported'])
        self.assertEqual(result['detected_type'], 'docx')
        self.assertEqual(result['extension'], '.docx')
        self.assertTrue(result['properties']['can_merge'])
        self.assertFalse(result['properties']['can_preview'])
        self.assertTrue(result['properties']['requires_conversion'])

    def test_detect_file_type_epub(self):
        """Test detecting EPUB file type."""
        epub_path = self.test_dir / "test.epub"
        # Create a mock EPUB file with ZIP signature and EPUB-specific content
        epub_path.write_bytes(b"PK\x03\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00mimetypeapplication/epub+zipMETA-INF/")

        result = self.detector.detect_file_type(epub_path)

        self.assertTrue(result['supported'])
        self.assertEqual(result['detected_type'], 'epub')
        self.assertEqual(result['extension'], '.epub')
        self.assertTrue(result['properties']['requires_conversion'])

    def test_detect_file_type_zip(self):
        """Test detecting ZIP file type."""
        zip_path = self.test_dir / "test.zip"
        zip_path.write_bytes(b"PK\x03\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00")

        result = self.detector.detect_file_type(zip_path)

        self.assertTrue(result['supported'])
        self.assertEqual(result['detected_type'], 'zip')
        self.assertFalse(result['properties']['can_merge'])

    def test_detect_file_type_unsupported(self):
        """Test detecting unsupported file type."""
        txt_path = self.test_dir / "test.txt"
        txt_path.write_text("This is a text file.")

        result = self.detector.detect_file_type(txt_path)

        self.assertFalse(result['supported'])
        self.assertEqual(result['detected_type'], 'unknown')
        self.assertFalse(result.get('properties'))

    def test_detect_nonexistent_file(self):
        """Test detecting non-existent file."""
        nonexistent_path = self.test_dir / "nonexistent.pdf"

        result = self.detector.detect_file_type(nonexistent_path)

        self.assertEqual(result['detected_type'], 'unknown')
        self.assertIn('file_not_found', result['error'])

    def test_validate_file_for_merge_valid_pdf(self):
        """Test validating a valid PDF for merge."""
        pdf_path = self.test_dir / "valid.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\nValid PDF content\n%%EOF")

        result = self.detector.validate_file_for_merge(pdf_path)

        self.assertTrue(result['valid'])
        self.assertEqual(result['reason'], 'valid')

    def test_validate_file_for_merge_empty_file(self):
        """Test validating an empty file."""
        empty_path = self.test_dir / "empty.pdf"
        empty_path.write_bytes(b"")  # Empty file

        result = self.detector.validate_file_for_merge(empty_path)

        self.assertFalse(result['valid'])
        self.assertEqual(result['reason'], 'empty_file')

    def test_get_file_type_display_info_pdf(self):
        """Test getting display info for PDF."""
        pdf_path = self.test_dir / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\nValid PDF content\n%%EOF")

        info = self.detector.get_file_type_display_info(pdf_path)

        self.assertEqual(info['icon'], '📕')
        self.assertEqual(info['description'], 'PDF Document')
        self.assertEqual(info['category'], 'document')
        self.assertTrue(info['can_preview'])
        self.assertFalse(info['requires_conversion'])

    def test_get_file_type_display_info_docx(self):
        """Test getting display info for DOCX."""
        docx_path = self.test_dir / "test.docx"
        docx_path.write_bytes(b"PK\x03\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00")

        info = self.detector.get_file_type_display_info(docx_path)

        self.assertEqual(info['icon'], '📝')
        self.assertEqual(info['description'], 'Word Document (DOCX)')
        self.assertEqual(info['category'], 'document')
        self.assertFalse(info['can_preview'])
        self.assertTrue(info['requires_conversion'])

    def test_batch_detect_files(self):
        """Test batch detection of multiple files."""
        # Create test files
        pdf_path = self.test_dir / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\nTest PDF")

        txt_path = self.test_dir / "test.txt"
        txt_path.write_text("Text file")

        file_paths = [pdf_path, txt_path]
        results = self.detector.batch_detect_files(file_paths)

        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]['supported'])  # PDF
        self.assertFalse(results[1]['supported'])  # TXT


class TestFileTypeDetectorFunctions(unittest.TestCase):
    """Test cases for file type detector convenience functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        for file_path in self.test_dir.glob("*"):
            if file_path.is_file():
                file_path.unlink()
        self.test_dir.rmdir()

    def test_detect_file_type_function(self):
        """Test the detect_file_type convenience function."""
        pdf_path = self.test_dir / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\nTest PDF")

        result = detect_file_type(pdf_path)

        self.assertTrue(result['supported'])
        self.assertEqual(result['detected_type'], 'pdf')

    def test_validate_file_for_merge_function(self):
        """Test the validate_file_for_merge convenience function."""
        pdf_path = self.test_dir / "valid.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\nValid PDF\n%%EOF")

        result = validate_file_for_merge(pdf_path)

        self.assertTrue(result['valid'])
        self.assertEqual(result['reason'], 'valid')

    def test_get_file_type_detector_singleton(self):
        """Test that get_file_type_detector returns a singleton."""
        # Test the actual singleton behavior
        detector1 = get_file_type_detector()
        detector2 = get_file_type_detector()

        # Should be the same instance
        self.assertEqual(detector1, detector2)
        self.assertIsNotNone(detector1)
        self.assertIsInstance(detector1, FileTypeDetector)


if __name__ == '__main__':
    unittest.main()
