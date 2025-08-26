"""
Centralized imports for PDF processing libraries to avoid duplication across modules.
This module handles optional imports and provides a single point for PDF-related dependencies.
"""

# PDF processing libraries
import pymupdf
from pypdf import PdfWriter, PdfReader

# Optional archive support
try:
    import rarfile
    RARFILE_AVAILABLE = True
except ImportError:
    rarfile = None
    RARFILE_AVAILABLE = False

# Optional Word document conversion support
try:
    from docx2pdf import convert
    WORD_CONVERSION_AVAILABLE = True
except ImportError:
    WORD_CONVERSION_AVAILABLE = False
    convert = None

# Optional EPUB e-book conversion support
try:
    import ebooklib
    from ebooklib import epub
    import weasyprint
    EPUB_CONVERSION_AVAILABLE = True
except ImportError:
    ebooklib = None
    epub = None
    weasyprint = None
    EPUB_CONVERSION_AVAILABLE = False

# Optional performance monitoring support
try:
    import psutil
    PERFORMANCE_MONITORING_AVAILABLE = True
except ImportError:
    psutil = None
    PERFORMANCE_MONITORING_AVAILABLE = False

# Export what's needed - only include available modules
__all__ = [
    'pymupdf',
    'PdfWriter',
    'PdfReader',
    'RARFILE_AVAILABLE',
    'WORD_CONVERSION_AVAILABLE',
    'EPUB_CONVERSION_AVAILABLE',
    'PERFORMANCE_MONITORING_AVAILABLE'
]

# Add optional imports to exports if available
if RARFILE_AVAILABLE:
    __all__.append('rarfile')

if WORD_CONVERSION_AVAILABLE:
    __all__.append('convert')

if EPUB_CONVERSION_AVAILABLE:
    __all__.extend(['ebooklib', 'epub', 'weasyprint'])

if PERFORMANCE_MONITORING_AVAILABLE:
    __all__.append('psutil') 