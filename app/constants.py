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

# --- Task Queue and Timing ---
TASK_QUEUE_CHECK_INTERVAL = 100  # milliseconds

# --- Initial Values ---
DEFAULT_ZOOM_DISPLAY_FACTOR = 1.0
DEFAULT_PROGRESS_VALUE = 0.0
DEFAULT_CURRENT_PAGE = 0

# --- Merge Task Constants ---
MERGE_PROGRESS_FILE_WEIGHT = 90 # %
MERGE_PROGRESS_FINALIZE_WEIGHT = 10 # %
VALIDATION_REPORT_MAX_ISSUES = 20 # Max issues to show in messagebox

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

# --- Paths ---
# Suggestion: Define a standard location for config/logs
# For simplicity, keeping in current directory for now
DEFAULT_CONFIG_PATH = Path(DEFAULT_CONFIG_FILENAME)
DEFAULT_LOG_PATH = Path(DEFAULT_LOG_FILE_PATH)

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
