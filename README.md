# PDF Merger Pro

## Version 2.7.0

PDF Merger Pro is an advanced utility for merging PDF files, Word documents, and EPUB e-books with a modern graphical user interface and comprehensive output control.

### Recent Improvements (v2.7.0)
- **🎨 Modern UI/UX Design**: Complete visual overhaul with modern color palette, icons, and styling
- **🔍 Intelligent File Detection**: Auto-detection of file types with enhanced format support
- **📁 Recent Folders**: Quick access to frequently used directories
- **❌ Enhanced Error Handling**: Specific error messages with actionable suggestions
- **🎯 Consistent Design System**: Professional color scheme and typography throughout
- **📱 Icon Integration**: Meaningful icons for all UI elements
- **⚡ Performance Improvements**: Better background processing and memory management
- **🔧 Code Quality**: Further improvements in maintainability and structure
- **🖼️ Quality Presets**: One-click optimization for web, print, archive, and more
- **🗜️ Advanced Compression**: Granular control over file size vs quality trade-offs
- **📝 Metadata Editing**: Full control over PDF metadata (title, author, subject, keywords)

### New Features in v2.7.0
- **Quality Presets**: Pre-configured settings for web, print, archive, screen reading, draft, and e-book formats
- **Advanced Compression**: Five compression levels with detailed control over image, text, and font optimization
- **Metadata Management**: Complete editing of PDF properties including validation and bulk operations
- **Modern Color Palette**: Professional color scheme with primary, secondary, success, warning, and error states
- **Icon System**: Unicode-based icons for buttons, file types, and UI elements
- **File Type Auto-Detection**: Intelligent detection using content signatures, not just extensions
- **Recent Folders Management**: Quick access to frequently used directories with favorites
- **Enhanced Error Messages**: Specific errors with suggested solutions and recovery steps
- **Modern Typography**: Consistent font weights and sizes across the application
- **Improved Accessibility**: Better contrast ratios and keyboard navigation

## Features

### File Processing
*   **EPUB E-book Support:** Add EPUB e-books (.epub) alongside PDFs and Word documents - they are automatically converted to PDF during merging.
*   **Word Document Support:** Add Word documents (.docx, .doc) alongside PDFs - they are automatically converted to PDF during merging.
*   **Intelligent File Detection:** Auto-detects file types using content signatures for better accuracy than extension-based detection.
*   **Drag & Drop Support:** Easily add files and folders by dragging them into the application window.
*   **File Reordering:** Arrange the order of files in the list before merging with intuitive move buttons.
*   **Add from Archives:** Extract and add PDF files directly from ZIP or RAR archives.

### Preview & Selection
*   **PDF Preview:** View PDF pages with zoom (buttons/scroll wheel) and pan (click & drag when zoomed).
*   **Page Range Selection:** Select specific pages or ranges from each PDF to include in the final merged document.
*   **File Type Icons:** Visual indicators for different file types (PDF, Word, EPUB, Archives).

### Output & Configuration
*   **Quality Presets:** One-click optimization with presets for web, print, archive, screen, draft, and e-book formats
*   **Advanced Compression:** Five compression levels (none, fast, normal, high, maximum) with granular control
*   **Metadata Editing:** Complete control over PDF properties (title, author, subject, keywords) with validation
*   **Bookmark Preservation:** Optionally preserve existing bookmarks (outlines) from source PDFs.
*   **Configuration Profiles:** Save and load lists of files and their associated settings as profiles.
*   **Output Options:** Configure output settings including password protection and compression level.
*   **Recent Folders:** Quick access to frequently used directories with favorites support.

### User Experience
*   **Modern UI Design:** Professional color palette with primary, secondary, success, warning, and error states.
*   **Icon Integration:** Meaningful Unicode icons throughout the interface for better visual communication.
*   **Enhanced Error Handling:** Specific error messages with actionable suggestions for problem resolution.
*   **Consistent Typography:** Professional font hierarchy with appropriate weights and sizes.
*   **Improved Accessibility:** Better contrast ratios and keyboard navigation support.

### Performance & Reliability
*   **Multi-threading:** Core operations like merging and file processing run in the background to keep the UI responsive.
*   **File Validation:** Check files for common issues before merging (e.g., not found, encrypted, no pages).
*   **Memory Optimization:** Efficient processing of large files with progress tracking.
*   **Robust Error Recovery:** Graceful handling of file processing errors with detailed logging.

## Requirements

*   Python 3.7+
*   Tkinter (usually included with Python)
*   The following Python packages (listed in `requirements.txt`):
    *   `tkinterdnd2` - Drag and drop functionality
    *   `pypdf` - PDF processing and merging
    *   `pymupdf` - PDF rendering and manipulation
    *   `docx2pdf` - Word document conversion (optional - if not installed, Word files will be ignored)
    *   `rarfile` - RAR archive support (optional - if not installed, RAR support will be disabled)
    *   `ebooklib` - EPUB processing (optional - if not installed, EPUB support will be disabled)
    *   `weasyprint` - EPUB to PDF conversion (optional - if not installed, EPUB support will be disabled)
    *   `python-magic` - File type detection (optional - if not installed, fallback to extension-based detection)

### Optional Dependencies
*   **python-magic**: Enables content-based file type detection for better accuracy
*   **docx2pdf**: Enables Word document (.docx, .doc) to PDF conversion
*   **rarfile + unrar**: Enables extraction of PDF files from RAR archives
*   **ebooklib + weasyprint**: Enables EPUB e-book to PDF conversion

### Installation Options

**Full Installation (All Features):**
```bash
pip install tkinterdnd2 pypdf pymupdf docx2pdf rarfile ebooklib weasyprint python-magic
```

**PDF + Word Support:**
```bash
pip install tkinterdnd2 pypdf pymupdf docx2pdf
```

**PDF Support Only:**
```bash
pip install tkinterdnd2 pypdf pymupdf
```

### External Tools
*   For RAR support: Install `unrar` command-line tool and ensure it's in your system's PATH

## Installation

1.  Make sure you have Python installed.
2.  Install the required Python packages using pip:

    ```bash
    pip install -r requirements.txt
    ```

    **For full functionality (PDF + Word + RAR support):**
    ```bash
    pip install tkinterdnd2 pypdf pymupdf docx2pdf rarfile
    ```

    **For PDF + Word support only (no RAR):**
    ```bash
    pip install tkinterdnd2 pypdf pymupdf docx2pdf
    ```

    **For PDF support only (no Word or RAR):**
    ```bash
    pip install tkinterdnd2 pypdf pymupdf
    ```

3.  Ensure the `unrar` command-line tool is installed and in your PATH if you require RAR support. (Installation varies by operating system).

## Usage

1.  Ensure all application Python files are located in the `app/` directory, and icon files in the `assets/` directory.
2.  Run the main application script from your terminal:

    ```bash
    python main.py
    ```

3.  Add PDF files, Word documents, or EPUB e-books, folders, or archives using the "File" menu or by dragging them into the application window.
4.  Word documents (.docx, .doc) and EPUB e-books (.epub) will be automatically converted to PDF during the merging process.
5.  Arrange files, set page ranges (double-click a file or use the button), and configure output options.
6.  Click "Merge PDFs".

## Word Document Support

*   **Supported Formats:** .docx and .doc files
*   **Automatic Conversion:** Word documents are converted to PDF behind the scenes using the `docx2pdf` library
*   **Seamless Integration:** Converted Word documents appear in the file list and can be previewed, reordered, and have page ranges set just like regular PDFs
*   **Error Handling:** If `docx2pdf` is not installed, Word files will be skipped with clear error messages and installation instructions

## EPUB E-book Support

*   **Supported Formats:** .epub files
*   **Automatic Conversion:** EPUB e-books are converted to PDF behind the scenes using the `ebooklib` and `weasyprint` libraries
*   **Seamless Integration:** Converted EPUB e-books appear in the file list and can be previewed, reordered, and have page ranges set just like regular PDFs
*   **Error Handling:** If `ebooklib` or `weasyprint` is not installed, EPUB e-books will be skipped with clear error messages and installation instructions

## Logging

The application logs information, warnings, and errors to a file named `pdf_merger.log` in the application's root directory.

## Development

### Code Structure
The application follows a modular architecture with clear separation of concerns:

- **`app/`**: Main application directory containing all source code
  - **`core/`**: Core application logic and main classes
    - **`pdf_merger_app.py`**: Main application window and UI orchestration
    - **`app_core.py`**: Core application logic and coordination
    - **`app_initializer.py`**: Application initialization and setup
    - **`pdf_document.py`**: PDF document representation and management
    - **`background_task.py`**: Background task management
  - **`ui/`**: User interface components and panels
    - **`action_panel.py`**: Merge actions and controls
    - **`file_list_panel.py`**: File list management and display
    - **`preview_panel.py`**: PDF preview functionality
    - **`output_panel.py`**: Output options configuration
    - **`layout_manager.py`**: UI layout management
    - **`menu_manager.py`**: Menu bar management
    - **`status_bar.py`**: Status bar component
    - **`tooltip.py`**: Tooltip functionality
    - **`keyboard_manager.py`**: Keyboard shortcut management
    - **`modern_style.py`**: Modern UI styling and theming system
  - **`managers/`**: Manager classes for specific functionality
    - **`config_manager.py`**: Configuration management and persistence
    - **`profile_manager.py`**: User profile management
    - **`performance_monitor.py`**: Performance monitoring and statistics
    - **`recent_folders_manager.py`**: Recent folders tracking and management
    - **`quality_presets_manager.py`**: Quality presets management and validation
    - **`advanced_compression_manager.py`**: Advanced compression settings and profiles
    - **`metadata_manager.py`**: PDF metadata editing and validation
  - **`utils/`**: Utility functions and shared components
    - **`constants.py`**: Centralized constants, colors, file extensions, and status messages
    - **`utils.py`**: General utility functions
    - **`common_imports.py`**: Centralized library imports
    - **`file_operations.py`**: File processing and validation operations
    - **`icons.py`**: Icon management and Unicode icon definitions
    - **`file_type_detector.py`**: Intelligent file type detection system
    - **`error_handler.py`**: Enhanced error handling with user-friendly messages
- **`config/`**: Configuration files
  - **`merge_config.json`**: Default merge configuration
  - **`pytest.ini`**: Test configuration
- **`docs/`**: Documentation files
  - **`DEVELOPER.md`**: Developer documentation and guidelines

### Coding Practices
- **Constants over Magic Numbers**: All magic numbers and strings are defined as named constants
- **DRY Principle**: Code duplication is eliminated through helper methods and utility functions
- **Error Handling**: Consistent error messages with user-friendly suggestions
- **Documentation**: Comprehensive docstrings for all functions and classes
- **Type Hints**: Full type annotations for better code maintainability
- **Modular Architecture**: Clean separation of concerns with manager classes
- **Design System**: Consistent color palette, typography, and iconography

### Testing
The application includes comprehensive tests covering all major components:

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/unit/          # Unit tests for individual components
pytest tests/integration/   # Integration tests for component interaction

# Run tests with coverage
pytest --cov=app tests/

# Run specific new feature tests
pytest tests/unit/test_icons.py                    # Icon management tests
pytest tests/unit/test_file_type_detector.py       # File detection tests
pytest tests/unit/test_recent_folders_manager.py   # Recent folders tests
pytest tests/unit/test_error_handler.py           # Error handling tests
pytest tests/unit/test_quality_presets_manager.py  # Quality presets tests
pytest tests/unit/test_advanced_compression_manager.py # Advanced compression tests
pytest tests/unit/test_metadata_manager.py         # Metadata management tests
```

### Test Coverage
- **Icon Management**: Tests for Unicode icon system and widget creation
- **File Type Detection**: Tests for content-based and extension-based detection
- **Recent Folders**: Tests for folder tracking, favorites, and persistence
- **Error Handler**: Tests for error classification and user-friendly messages
- **Quality Presets**: Tests for preset management, validation, and application
- **Advanced Compression**: Tests for compression profiles, settings, and estimation
- **Metadata Manager**: Tests for metadata editing, validation, and persistence
- **Integration**: Tests for component interaction and system behavior

### Code Quality
The codebase maintains high standards:
- No magic numbers or strings (all constants defined)
- Consistent naming conventions following Python standards
- Comprehensive error handling with user-friendly messages
- Modular and maintainable code structure with clear responsibilities
- Extensive test coverage for reliability
- Modern Python features (type hints, f-strings, dataclasses where appropriate)
- Professional UI/UX with consistent design system

### Performance Considerations
- **Background Processing**: Long-running tasks use threading to keep UI responsive
- **Memory Management**: Efficient file processing with proper cleanup
- **Lazy Loading**: Components initialized only when needed
- **Caching**: Icon and style resources cached for performance
- **Progress Tracking**: Real-time progress updates for user feedback