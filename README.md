# PDF Merger Pro

**Version 2.4.0**

PDF Merger Pro is an advanced utility for merging PDF files, Word documents, and EPUB e-books with a modern graphical user interface.

## Table of Contents

*   [Features](#features)
*   [Getting Started](#getting-started)
    *   [Requirements](#requirements)
    *   [Installation](#installation)
*   [Usage](#usage)
*   [Supported File Types](#supported-file-types)
    *   [Word Document Support](#word-document-support)
    *   [EPUB E-book Support](#epub-e-book-support)
*   [Logging](#logging)
*   [Contributing](#contributing)
*   [License](#license)

## Features

*   **EPUB E-book Support:** Add EPUB e-books (.epub) alongside PDFs and Word documents - they are automatically converted to PDF during merging.
*   **Word Document Support:** Add Word documents (.docx, .doc) alongside PDFs - they are automatically converted to PDF during merging.
*   **Drag & Drop Support:** Easily add files and folders by dragging them into the application window.
*   **File Reordering:** Arrange the order of files in the list before merging. (Manual move buttons implemented, drag-and-drop reordering within the list is a planned enhancement).
*   **PDF Preview:** View PDF pages with zoom (buttons/scroll wheel) and pan (click & drag when zoomed).
*   **Page Range Selection:** Select specific pages or ranges from each PDF to include in the final merged document.
*   **Bookmark Preservation:** Optionally preserve existing bookmarks (outlines) from source PDFs.
*   **Configuration Profiles:** Save and load lists of files and their associated settings as profiles.
*   **Add from Archives:** Extract and add PDF files directly from ZIP or RAR archives.
*   **Output Options:** Configure output settings including password protection and compression level.
*   **Multi-threading:** Core operations like merging and file processing run in the background to keep the UI responsive.
*   **File Validation:** Check files for common issues before merging (e.g., not found, encrypted, no pages).

## Getting Started

### Requirements

*   Python 3.7+
*   Tkinter (usually included with Python)
*   The following Python packages (listed in `requirements.txt`):
    *   `tkinterdnd2`
    *   `pypdf`
    *   `pymupdf`
    *   `docx2pdf` (Required for Word document conversion. If you don't need Word support, you can skip this, but Word files will be ignored).
    *   `rarfile` (Required for RAR archive support. If you don't need RAR support, you can skip this, but the feature will be disabled).
*   For RAR support using the `rarfile` library, the external command-line tool `unrar` must be installed on your system and available in your system's PATH.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/roeya2/PDF-Merger.git
    cd pdf-merger-pro
    ```
2.  **Install the required Python packages using pip:**

    **For full functionality (PDF + Word + RAR support):**
    ```bash
    pip install -r requirements.txt
    ```

    **For PDF + Word support only (no RAR):**
    ```bash
    pip install tkinterdnd2 pypdf pymupdf docx2pdf
    ```

    **For PDF support only (no Word or RAR):**
    ```bash
    pip install tkinterdnd2 pypdf pymupdf
    ```
3.  **Install `unrar` (optional):**
    Ensure the `unrar` command-line tool is installed and in your PATH if you require RAR support. (Installation varies by operating system).

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

## Supported File Types

### Word Document Support

*   **Supported Formats:** .docx and .doc files
*   **Automatic Conversion:** Word documents are converted to PDF behind the scenes using the `docx2pdf` library
*   **Seamless Integration:** Converted Word documents appear in the file list and can be previewed, reordered, and have page ranges set just like regular PDFs
*   **Error Handling:** If `docx2pdf` is not installed, Word files will be skipped with clear error messages and installation instructions

### EPUB E-book Support

*   **Supported Formats:** .epub files
*   **Automatic Conversion:** EPUB e-books are converted to PDF behind the scenes using the `ebooklib` and `weasyprint` libraries
*   **Seamless Integration:** Converted EPUB e-books appear in the file list and can be previewed, reordered, and have page ranges set just like regular PDFs
*   **Error Handling:** If `ebooklib` or `weasyprint` is not installed, EPUB e-books will be skipped with clear error messages and installation instructions

## Logging

The application logs information, warnings, and errors to a file named `pdf_merger.log` in the application's root directory.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
