import os
from pathlib import Path

# --- Application Constants ---
APP_NAME = "PDF Merger Pro"
APP_VERSION = "2.4.0" # Increment version for this refactoring
LOGGER_NAME = "PDFMergerPro"

# --- Configuration Constants ---
DEFAULT_CONFIG_FILENAME = "merge_config.json"
DEFAULT_OUTPUT_FILENAME = "merged_output.pdf"
MAX_RECENT_DIRS = 10
DEFAULT_COMPRESSION = "normal"
DEFAULT_PRESERVE_BOOKMARKS = True
DEFAULT_PASSWORD_PROTECT = False
DEFAULT_COLOR_MODE = "Colorful (Original)"
DEFAULT_DPI = "Original"
DEFAULT_LOG_OUTPUT = "both"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FILE_PATH = "pdf_merger.log"
PROFILE_LIST_KEY = "pdf_merger_pro_list"
WINDOW_GEOMETRY_KEY = "window_geometry"
PANEDWINDOW_SASH_KEY = "panedwindow_sash_positions"

# --- UI/Preview Constants ---
THUMBNAIL_SIZE = (100, 140)
MIN_ZOOM, MAX_ZOOM = 0.05, 10.0
ZOOM_STEP_FACTOR = 1.25
CANVAS_RESIZE_DELAY = 200 # Milliseconds
PREVIEW_LOAD_DELAY = 50 # Milliseconds
PREVIEW_NO_DOC_MSG = "Double-click a file in the list to preview it."
PREVIEW_NO_FILES_MSG = "Add PDF files to preview"
PREVIEW_LOADING_MSG = "Loading page {}..."
PREVIEW_NO_PAGES_MSG = "Document has no pages"
PREVIEW_ERROR_MSG = "Preview Error"
PREVIEW_IMAGE_ERROR_MSG = "Image Format Error"
PREVIEW_NO_PREVIEW_MSG = "Could not generate preview for this page."

# --- New Zoom Constants (Potentially redundant with MIN/MAX_ZOOM) ---
DEFAULT_ZOOM_STEP = 0.1 # Incremental step for zoom in/out
MIN_ZOOM_FACTOR = MIN_ZOOM # Seems redundant, using existing MIN_ZOOM
MAX_ZOOM_FACTOR = MAX_ZOOM # Seems redundant, using existing MAX_ZOOM

# --- Window and Dialog Dimensions ---
DEFAULT_WINDOW_WIDTH = 1050
DEFAULT_WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 950
MIN_WINDOW_HEIGHT = 700
DELETE_PROFILE_DIALOG_WIDTH = 300
DELETE_PROFILE_DIALOG_HEIGHT = 120

# --- Font Specifications ---
DEFAULT_FONT_FAMILY = "Segoe UI"
HEADER_FONT_SIZE = 12
TITLE_FONT_SIZE = 14
ACTION_BUTTON_FONT_SIZE = 10
FALLBACK_FONT_SIZE = 10

# --- Enhanced Typography System ---
# Font Families
PRIMARY_FONT = "Segoe UI"           # Main UI font
MONOSPACE_FONT = "Consolas"          # For code/logs
HEADING_FONT = "Segoe UI Semibold"   # For headings

# Font Sizes (in pixels)
FONT_SIZE_XS = 9      # Extra small
FONT_SIZE_SM = 10     # Small
FONT_SIZE_MD = 11     # Medium (default)
FONT_SIZE_LG = 12     # Large
FONT_SIZE_XL = 14     # Extra large
FONT_SIZE_2XL = 16    # 2X large
FONT_SIZE_3XL = 18    # 3X large

# Font Weights
FONT_WEIGHT_NORMAL = "normal"
FONT_WEIGHT_MEDIUM = "medium"
FONT_WEIGHT_SEMIBOLD = "semibold"
FONT_WEIGHT_BOLD = "bold"

# --- UI Spacing and Padding ---
MAIN_FRAME_PADDING = 10
HEADER_BOTTOM_PADDING = 10
LOWER_FRAME_TOP_PADDING = 10
PANEL_HORIZONTAL_PADDING = 5
STATUS_BAR_TOP_PADDING = 10
TOOLTIP_FRAME_PADDING = (5, 3)
TOOLTIP_LABEL_PADDING = (3, 2)
SEARCH_LABEL_RIGHT_PADDING = 5
VERSION_LABEL_LEFT_PADDING = 5
VERSION_LABEL_TOP_PADDING = 4
FILE_LIST_RIGHT_PADDING = 5
PREVIEW_LEFT_PADDING = 5
OUTPUT_PANEL_RIGHT_PADDING = 10
ACTION_PANEL_LEFT_PADDING = 5
BUTTON_FRAME_PADDING = 10
BUTTON_HORIZONTAL_PADDING = 5
DIALOG_VERTICAL_PADDING = 5
DIALOG_HORIZONTAL_PADDING = 10

# --- Colors ---
TOOLTIP_BACKGROUND = "#FFFFE0"
TOOLTIP_FOREGROUND = "black"
VERSION_LABEL_COLOR = "gray"
ERROR_TEXT_COLOR = "red"

# --- Modern Color Palette ---
# Primary Colors
PRIMARY_COLOR = "#2563EB"  # Modern blue
PRIMARY_HOVER = "#1D4ED8"  # Darker blue for hover
PRIMARY_LIGHT = "#DBEAFE"  # Light blue for backgrounds
PRIMARY_DARK = "#1E40AF"   # Dark blue for text

# Secondary Colors
SECONDARY_COLOR = "#6B7280"  # Modern gray
SECONDARY_HOVER = "#4B5563"  # Darker gray for hover
SECONDARY_LIGHT = "#F3F4F6"  # Light gray for backgrounds

# Success Colors
SUCCESS_COLOR = "#10B981"  # Modern green
SUCCESS_LIGHT = "#D1FAE5"   # Light green background
SUCCESS_DARK = "#059669"    # Dark green for text

# Warning Colors
WARNING_COLOR = "#F59E0B"  # Modern amber
WARNING_LIGHT = "#FEF3C7"   # Light amber background
WARNING_DARK = "#D97706"    # Dark amber for text

# Error Colors
ERROR_COLOR = "#EF4444"     # Modern red
ERROR_LIGHT = "#FEE2E2"     # Light red background
ERROR_DARK = "#DC2626"      # Dark red for text

# Info Colors
INFO_COLOR = "#3B82F6"      # Modern blue
INFO_LIGHT = "#DBEAFE"      # Light blue background
INFO_DARK = "#2563EB"       # Dark blue for text

# Neutral Colors
BACKGROUND_COLOR = "#FFFFFF"    # Pure white
SURFACE_COLOR = "#F9FAFB"       # Off-white for surfaces
SURFACE_VARIANT = "#F3F4F6"     # Slightly darker surface
BORDER_COLOR = "#E5E7EB"        # Light border
BORDER_DARK = "#D1D5DB"         # Darker border
TEXT_PRIMARY = "#111827"        # Dark text
TEXT_SECONDARY = "#6B7280"      # Medium gray text
TEXT_DISABLED = "#9CA3AF"       # Light gray text

# Shadow Colors (for subtle shadows)
SHADOW_LIGHT = "#00000010"      # 6% black for light shadows
SHADOW_MEDIUM = "#00000015"     # 8% black for medium shadows
SHADOW_DARK = "#00000020"       # 13% black for dark shadows

# Accent Colors
ACCENT_COLOR = "#8B5CF6"        # Modern purple
ACCENT_LIGHT = "#EDE9FE"        # Light purple background

# --- Task Queue and Timing ---
TASK_QUEUE_CHECK_INTERVAL = 100  # milliseconds

# --- Initial Values ---
DEFAULT_ZOOM_DISPLAY_FACTOR = 1.0
DEFAULT_PROGRESS_VALUE = 0.0
DEFAULT_CURRENT_PAGE = 0

# --- Magic Numbers and Conversion Constants ---
PROGRESS_PERCENTAGE_MULTIPLIER = 100  # For progress calculations (percentage)
MEMORY_BYTES_TO_MB = 1024 * 1024  # Convert bytes to MB
MEMORY_THRESHOLD_MB = 500.0  # Memory threshold for monitoring
MILLISECONDS_PER_SECOND = 1000  # Milliseconds in a second
LOG_PREVIEW_MAX_LENGTH = 100  # Max characters to show in log previews

# --- Merge Task Constants ---
MERGE_PROGRESS_FILE_WEIGHT = 90 # %
MERGE_PROGRESS_FINALIZE_WEIGHT = 10 # %
VALIDATION_REPORT_MAX_ISSUES = 20 # Max issues to show in messagebox

# --- Quality Presets ---
QUALITY_PRESETS = {
    "web": {
        "name": "Web Optimized",
        "description": "Small file size for web sharing",
        "compression": "maximum",
        "color_mode": "Colorful (Original)",
        "dpi": "96",
        "preserve_bookmarks": True,
        "icon": "🌐"
    },
    "print": {
        "name": "Print Quality",
        "description": "High quality for printing",
        "compression": "normal",
        "color_mode": "Colorful (Original)",
        "dpi": "300",
        "preserve_bookmarks": True,
        "icon": "🖨️"
    },
    "archive": {
        "name": "Archive/Long-term",
        "description": "Maximum compression for storage",
        "compression": "maximum",
        "color_mode": "Colorful (Original)",
        "dpi": "Original",
        "preserve_bookmarks": True,
        "icon": "📦"
    },
    "screen": {
        "name": "Screen Reading",
        "description": "Optimized for digital reading",
        "compression": "normal",
        "color_mode": "Colorful (Original)",
        "dpi": "150",
        "preserve_bookmarks": True,
        "icon": "📱"
    },
    "draft": {
        "name": "Draft Quality",
        "description": "Fast processing, lower quality",
        "compression": "fast",
        "color_mode": "Colorful (Original)",
        "dpi": "Original",
        "preserve_bookmarks": False,
        "icon": "⚡"
    },
    "ebook": {
        "name": "E-book Format",
        "description": "Optimized for e-readers",
        "compression": "maximum",
        "color_mode": "Colorful (Original)",
        "dpi": "150",
        "preserve_bookmarks": True,
        "icon": "📖"
    }
}

# --- Advanced Compression Constants ---
COMPRESSION_LEVELS = {
    "none": {
        "name": "No Compression",
        "description": "Fastest processing, largest file size",
        "pypdf_level": 0,
        "estimated_ratio": "100%",
        "speed": "Very Fast"
    },
    "fast": {
        "name": "Fast Compression",
        "description": "Quick compression with moderate size reduction",
        "pypdf_level": 1,
        "estimated_ratio": "80-90%",
        "speed": "Fast"
    },
    "normal": {
        "name": "Normal Compression",
        "description": "Balanced compression and speed",
        "pypdf_level": 2,
        "estimated_ratio": "70-85%",
        "speed": "Medium"
    },
    "high": {
        "name": "High Compression",
        "description": "Better compression, slower processing",
        "pypdf_level": 3,
        "estimated_ratio": "60-80%",
        "speed": "Slow"
    },
    "maximum": {
        "name": "Maximum Compression",
        "description": "Best compression, slowest processing",
        "pypdf_level": 4,
        "estimated_ratio": "50-75%",
        "speed": "Very Slow"
    }
}

# --- Metadata Constants ---
DEFAULT_METADATA = {
    "title": "",
    "author": "",
    "subject": "",
    "keywords": "",
    "creator": f"{APP_NAME} v{APP_VERSION}",
    "producer": f"{APP_NAME} v{APP_VERSION}"
}

METADATA_MAX_LENGTH = {
    "title": 200,
    "author": 100,
    "subject": 500,
    "keywords": 1000
}

# --- UI Constants for New Features ---
QUALITY_PRESET_DIALOG_WIDTH = 500
QUALITY_PRESET_DIALOG_HEIGHT = 400
METADATA_DIALOG_WIDTH = 600
METADATA_DIALOG_HEIGHT = 500
COMPRESSION_DIALOG_WIDTH = 500
COMPRESSION_DIALOG_HEIGHT = 400

# --- Status Messages for New Features ---
STATUS_QUALITY_PRESET_APPLIED = "Quality preset '{}' applied."
STATUS_METADATA_SAVED = "Metadata saved successfully."
STATUS_ADVANCED_COMPRESSION_SET = "Advanced compression settings applied."
STATUS_METADATA_VALIDATION_ERROR = "Metadata validation error: {}"

# --- File Type Constants ---
PDF_FILETYPE = ("PDF Files", "*.pdf")
DOCX_FILETYPE = ("Word Documents (DOCX)", "*.docx")
DOC_FILETYPE = ("Word Documents (DOC)", "*.doc")
WORD_FILETYPES = ("Word Documents", "*.docx *.doc")
EPUB_FILETYPE = ("EPUB E-books", "*.epub")
EBOOK_FILETYPES = ("E-book Files", "*.epub")
JSON_FILETYPE = ("JSON Files", "*.json")
ZIP_FILETYPE = ("ZIP files", "*.zip")
RAR_FILETYPE = ("RAR files", "*.rar")
ARCHIVE_FILETYPES = ("Archive Files", "*.zip *.rar")
ALL_FILES_FILETYPE = ("All Files", "*.*")

# --- File Extensions ---
PDF_EXTENSION = ".pdf"
DOCX_EXTENSION = ".docx"
DOC_EXTENSION = ".doc"
EPUB_EXTENSION = ".epub"
ZIP_EXTENSION = ".zip"
RAR_EXTENSION = ".rar"
JSON_EXTENSION = ".json"

# --- Paths ---
# Suggestion: Define a standard location for config/logs
# For simplicity, keeping in current directory for now
DEFAULT_CONFIG_PATH = Path(DEFAULT_CONFIG_FILENAME)
DEFAULT_LOG_PATH = Path(DEFAULT_LOG_FILE_PATH)

# --- Recent Folders Configuration ---
MAX_RECENT_FOLDERS = 10
RECENT_FOLDERS_KEY = "recent_folders"

# --- UI Enhancement Constants ---
# Button and Widget Styling
BUTTON_CORNER_RADIUS = 6
FRAME_CORNER_RADIUS = 8
BORDER_WIDTH = 1
FOCUS_RING_WIDTH = 2

# Icon Sizes
ICON_SIZE_SMALL = 16
ICON_SIZE_MEDIUM = 20
ICON_SIZE_LARGE = 24

# Animation and Timing
HOVER_ANIMATION_DURATION = 150  # milliseconds
TRANSITION_DURATION = 200       # milliseconds

# Modern Spacing Scale (following 4px grid system)
SPACE_1 = 4    # 4px
SPACE_2 = 8    # 8px
SPACE_3 = 12   # 12px
SPACE_4 = 16   # 16px
SPACE_5 = 20   # 20px
SPACE_6 = 24   # 24px
SPACE_8 = 32   # 32px
SPACE_10 = 40  # 40px
SPACE_12 = 48  # 48px

# --- Other ---
# Define string constants for UI elements for consistency
# Renamed to match import names in app.py
STATUS_PREVIEW_NO_DOC_SELECTED = "Select a file and double-click to preview"
STATUS_PREVIEW_NO_FILES = "Add PDF files, Word documents, or EPUB e-books to preview"
STATUS_PREVIEW_LOADING = "Loading page {}..."
STATUS_PREVIEW_GENERATING = "Generating preview for {} page {}..."
STATUS_PREVIEW_NO_PAGE = "Document has no pages"
STATUS_PREVIEW_READY = "Preview ready for {} (page {})."
STATUS_PREVIEW_ERROR_LOADING = "Error loading preview for {}."
STATUS_PREVIEW_ERROR = "Preview Error"
STATUS_PREVIEW_IMAGE_ERROR = "Image Format Error"
STATUS_PREVIEW_NO_PREVIEW = "Could not generate preview for this page."

STATUS_READY = "Ready"
STATUS_NO_FILES = "No files selected. Drag & drop PDFs, Word documents, or EPUB e-books here or use File menu."
STATUS_FILES_LOADED = "{} files in list ({}) total pages."
STATUS_ADDED_FILES = "Added {} files."
STATUS_NO_VALID_ADDED = "No new valid PDF files were added."
STATUS_FILE_LIST_SAVED = "File list saved to {}."
STATUS_FILE_LIST_LOADED = "Loaded {} files from {}."
STATUS_VALIDATING_FILE = "Validating {} ({}/{}) ..."
STATUS_VALIDATION_COMPLETE = "Validation complete. All files OK."
STATUS_VALIDATION_ISSUES = "Validation complete. {} issue(s) found."
STATUS_REMOVED_FILES = "Removed {} files."
STATUS_LIST_CLEARED = "File list cleared."
STATUS_PROFILE_SAVED = "Profile '{}' saved."
STATUS_PROFILE_LOADED = "Loaded {} files from profile '{}'."
STATUS_PROFILE_DELETED = "Profile '{}' deleted."
STATUS_MERGE_STARTING = "Starting merge process..."
STATUS_MERGE_APPENDING = "Merging {} ({}/{})..."
STATUS_MERGE_APPENDING_PAGES = "Appending pages from {}..."
STATUS_MERGE_FINALIZING = "Finalizing and saving merged PDF..."
STATUS_MERGE_WRITING = "Writing output file..."
STATUS_MERGE_MOVING = "Moving output file..."
STATUS_MERGE_SUCCESS = "Merge successful! Output: {} ({:.2f} MB)"
STATUS_OUTPUT_SET = "Output file set to: {}"

# --- Enhanced Error Messages with Suggestions ---
ERROR_FILE_NOT_FOUND = "File not found: {filename}"
ERROR_FILE_NOT_FOUND_SUGGESTION = "Please check if the file exists and the path is correct. You can also try refreshing the file list."

ERROR_ENCRYPTED_PASSWORD_PROTECTED = "File is password protected: {filename}"
ERROR_ENCRYPTED_SUGGESTION = "This file requires a password to open. Please provide the password or choose a different file."

ERROR_NO_PAGES_FOUND = "No pages found in file: {filename}"
ERROR_NO_PAGES_SUGGESTION = "The file appears to be empty or corrupted. Please check if this is a valid PDF file."

ERROR_CORRUPTED_FILE = "File appears to be corrupted: {filename}"
ERROR_CORRUPTED_SUGGESTION = "The file may be damaged or not a valid PDF. Try opening it with a PDF viewer to verify."

ERROR_PERMISSION_DENIED = "Permission denied accessing file: {filename}"
ERROR_PERMISSION_SUGGESTION = "You don't have permission to read this file. Please check file permissions or choose a different file."

ERROR_UNSUPPORTED_FILE_TYPE = "Unsupported file type: {extension}"
ERROR_UNSUPPORTED_SUGGESTION = "This file type is not supported. Supported formats: PDF, DOCX, DOC, EPUB. You can also add files from ZIP/RAR archives."

ERROR_WORD_CONVERSION_FAILED = "Failed to convert Word document: {filename}"
ERROR_WORD_CONVERSION_SUGGESTION = "Word document conversion failed. Please ensure 'docx2pdf' is installed: pip install docx2pdf"

ERROR_EPUB_CONVERSION_FAILED = "Failed to convert EPUB e-book: {filename}"
ERROR_EPUB_CONVERSION_SUGGESTION = "EPUB conversion failed. Please ensure required libraries are installed: pip install ebooklib weasyprint"

ERROR_ARCHIVE_EXTRACTION_FAILED = "Failed to extract files from archive: {filename}"
ERROR_ARCHIVE_EXTRACTION_SUGGESTION = "Archive extraction failed. For RAR files, ensure 'unrar' is installed and available in PATH."

ERROR_OUTPUT_PATH_INVALID = "Invalid output path: {path}"
ERROR_OUTPUT_PATH_SUGGESTION = "Please choose a valid output path with write permissions. You can also check available disk space."

ERROR_GENERAL = "General error: {}"
ERROR_MERGE_FAILED_GENERAL = "Merge operation failed"
ERROR_MERGE_FAILED_SUGGESTION = "The merge operation encountered an error. Please check the log file for details and try with fewer files."

ERROR_MEMORY_INSUFFICIENT = "Insufficient memory for operation"
ERROR_MEMORY_SUGGESTION = "The operation requires more memory. Try processing fewer files at once or close other applications."
STATUS_EXTRACTION_STARTING = "Extracting PDFs from {}..."
STATUS_ARCHIVE_PROCESSED_NO_PDFS = "Archive processed. No PDFs added."
STATUS_ARCHIVE_ERROR = "Archive error: {}..." # Truncate error message

# Word file processing status messages
STATUS_CONVERTING_WORD = "Converting Word document: {}..."
STATUS_WORD_CONVERTED = "Converted {} Word documents to PDF."
STATUS_WORD_CONVERSION_ERROR = "Error converting Word document: {}"
STATUS_WORD_SUPPORT_MISSING = "Word conversion not available. Install python-docx2pdf: pip install docx2pdf"

# EPUB file processing status messages
STATUS_CONVERTING_EPUB = "Converting EPUB e-book: {}..."
STATUS_EPUB_CONVERTED = "Converted {} EPUB e-books to PDF."
STATUS_EPUB_CONVERSION_ERROR = "Error converting EPUB e-book: {}"
STATUS_EPUB_SUPPORT_MISSING = "EPUB conversion not available. Install required libraries: pip install ebooklib weasyprint"

# --- Additional Status Constants Found Missing ---
STATUS_MERGING = "Merging {} file(s)..." # Added definition
STATUS_VALIDATING = "Validating {} file(s)..." # Added definition
STATUS_VALIDATION_COMPLETE_ISSUES = "Validation complete. {} issue(s) found." # Added definition
STATUS_VALIDATION_COMPLETE_SUCCESS = "Validation complete. All files OK." # Added definition

# --- UI/Page Range Constants ---
STATUS_PAGE_RANGE_SET_SINGLE = "Page range set for selected file."
STATUS_PAGE_RANGE_SET_MULTIPLE = "Page ranges updated for {} selected files."
STATUS_PAGE_RANGE_INVALID = "Invalid page range entered. Please use format like '1,3,5-10'."
STATUS_NO_FILES_SELECTED_FOR_PAGES = "No files selected to configure page ranges."
PAGE_RANGE_DIALOG_WIDTH = 400 # Pixels, estimated
PAGE_RANGE_DIALOG_HEIGHT = 250 # Pixels, estimated
