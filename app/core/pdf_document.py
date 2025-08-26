import os
import tkinter as tk
import threading
import logging
from typing import List, Dict, Optional, Tuple, Any

# PDF processing libraries - use centralized imports
from ..utils.common_imports import pymupdf

from ..utils.constants import LOGGER_NAME, MIN_ZOOM, MAX_ZOOM

class PDFDocument:
    """Represents a single PDF file managed by the application."""
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.page_count = 0
        self.selected_pages: List[int] = [] # 0-indexed list of pages to include in merge
        self._pymupdf_doc: Optional[pymupdf.Document] = None # PyMuPDF document object
        self._pymupdf_lock = threading.Lock() # Lock for thread-safe access to _pymupdf_doc
        self.logger = logging.getLogger(LOGGER_NAME)
        self.logger.debug(f"PDFDocument instance created for: {self.filepath}")
        self.load_metadata()

    def load_metadata(self):
        """Loads page count and initial metadata using PyMuPDF."""
        self.close_document()
        try:
            with self._pymupdf_lock:
                self._pymupdf_doc = pymupdf.open(self.filepath)
                self.page_count = self._pymupdf_doc.page_count
                self.selected_pages = list(range(self.page_count)) # Default to all pages
                raw_metadata = self._pymupdf_doc.metadata if self._pymupdf_doc.metadata else {}
                self.metadata = {k: (v.decode('utf-8', errors='ignore') if isinstance(v, bytes) else v) for k, v in raw_metadata.items()}

            self.logger.debug(f"Loaded metadata for {self.filename}: pages={self.page_count}")
        except FileNotFoundError:
             self.logger.error(f"File not found: {self.filepath}")
             self._reset_state()
        except Exception as e:
            self.logger.error(f"Error loading metadata for {self.filename} from {self.filepath}: {e}", exc_info=True)
            self._reset_state()

    def _reset_state(self):
        """Resets internal state on error."""
        self.page_count = 0
        self.selected_pages = []
        self.metadata = {}
        self.close_document()

    def get_preview(self, page_num: int = 0, zoom_factor: float = 1.0, fit_size: Optional[Tuple[int, int]] = None) -> Optional[Tuple[bytes, float]]:
        """
        Generates preview image data (bytes) for a specific page.
        Supports explicit zoom factor or fitting to a given size.
        Returns (img_data_bytes, actual_zoom_used) or None on error.
        Designed to be called from a background thread.
        """
        if not self._pymupdf_doc or self.page_count == 0 or not (0 <= page_num < self.page_count):
             self.logger.warning(f"Cannot generate preview for {self.filename}: Doc not loaded, no pages, or invalid page_num {page_num}.")
             if not self._pymupdf_doc:
                self.load_metadata() # Attempt reload
                if not self._pymupdf_doc or not (0 <= page_num < self.page_count): return None

        effective_zoom_factor = zoom_factor
        try:
            with self._pymupdf_lock:
                page = self._pymupdf_doc[page_num]
                page_rect = page.rect

                if page_rect.width <= 0 or page_rect.height <= 0:
                     self.logger.warning(f"Page {page_num} of {self.filename} has zero dimensions. Cannot generate preview.")
                     return None

                matrix: pymupdf.Matrix
                if fit_size and fit_size[0] > 1 and fit_size[1] > 1:
                    zoom_x = fit_size[0] / page_rect.width
                    zoom_y = fit_size[1] / page_rect.height
                    actual_zoom = min(zoom_x, zoom_y)
                    actual_zoom = max(MIN_ZOOM, min(actual_zoom, MAX_ZOOM)) # Clamp
                    matrix = pymupdf.Matrix(actual_zoom, actual_zoom)
                    effective_zoom_factor = actual_zoom
                else:
                    effective_zoom_factor = max(MIN_ZOOM, min(zoom_factor, MAX_ZOOM)) # Clamp
                    matrix = pymupdf.Matrix(effective_zoom_factor, effective_zoom_factor)

                # Generate pixmap as RGB bytes (PPM format compatible)
                pix = page.get_pixmap(matrix=matrix, colorspace=pymupdf.csRGB, alpha=False)
                img_data = pix.tobytes("ppm")

                return (img_data, effective_zoom_factor) # Return raw data and zoom factor

        except Exception as e:
            self.logger.error(f"Error generating preview data for {self.filename}, page {page_num} (zoom {effective_zoom_factor:.2f}): {e}", exc_info=True)
            return None

    def close_document(self):
        """Closes the internal PyMuPDF document handle."""
        with self._pymupdf_lock:
            if self._pymupdf_doc:
                self._pymupdf_doc.close()
                self._pymupdf_doc = None
                self.logger.debug(f"PyMuPDF document handle closed for {self.filename}")

    def __str__(self) -> str:
        """String representation for the document."""
        return f"{self.filename} ({self.page_count} pages)"

    def get_file_size_str(self) -> str:
        """Gets the file size in a human-readable format."""
        try:
            if os.path.exists(self.filepath):
                size_bytes = os.path.getsize(self.filepath)
                if size_bytes >= 1024 * 1024:
                    return f"{size_bytes / (1024 * 1024):.2f} MB"
                elif size_bytes >= 1024:
                    return f"{size_bytes / 1024:.1f} KB"
                else:
                    return f"{size_bytes} Bytes"
            else:
                return "File Missing"
        except OSError as e:
            self.logger.warning(f"Could not get size for {self.filepath}: {e}")
            return "Error"

    def get_selected_pages_display(self) -> str:
        """Returns a user-friendly string representation of the selected pages."""
        if not self.selected_pages or len(self.selected_pages) == self.page_count:
            return "All Pages"
        # Simple placeholder: just show the count of selected pages
        return f"{len(self.selected_pages)} pages selected"