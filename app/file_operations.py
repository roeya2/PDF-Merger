import os
import sys
import logging
import shutil
import tempfile
import zipfile
import json # Added for save/load list
from datetime import datetime # Added for timestamp
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path
import tkinter as tk # For clipboard access
from tkinter import filedialog, messagebox

# PDF processing libraries - use centralized imports
from app.common_imports import pymupdf, PdfReader, PdfWriter, RARFILE_AVAILABLE, convert, WORD_CONVERSION_AVAILABLE, EPUB_CONVERSION_AVAILABLE

from app.constants import (
    LOGGER_NAME, STATUS_EXTRACTION_STARTING, STATUS_ARCHIVE_PROCESSED_NO_PDFS,
    VALIDATION_REPORT_MAX_ISSUES,
    PDF_FILETYPE, ALL_FILES_FILETYPE, JSON_FILETYPE,
    ZIP_FILETYPE, RAR_FILETYPE, ARCHIVE_FILETYPES,
    DOCX_FILETYPE, DOC_FILETYPE, WORD_FILETYPES,
    EPUB_FILETYPE, EBOOK_FILETYPES,
    STATUS_CONVERTING_WORD, STATUS_WORD_CONVERTED, STATUS_WORD_CONVERSION_ERROR, STATUS_WORD_SUPPORT_MISSING,
    STATUS_CONVERTING_EPUB, STATUS_EPUB_CONVERTED, STATUS_EPUB_CONVERSION_ERROR, STATUS_EPUB_SUPPORT_MISSING,
    PROFILE_LIST_KEY, APP_NAME, APP_VERSION, STATUS_FILE_LIST_SAVED
)
from app.pdf_document import PDFDocument
from app.exceptions import FileHandlingError, CorruptFileError

class FileOperations:
    """Handles all file-related operations for the PDF Merger Pro application,
    including file/folder addition, archive extraction, drag & drop, and list save/load.
    """

    def __init__(self, app_core_context):
        """
        Initializes the FileOperations class.

        Args:
            app_core_context: The AppCore instance
                         providing access to shared resources like logger, config_manager,
                         status updates, and background task management.
        """
        self.app_core = app_core_context
        self.logger = logging.getLogger(LOGGER_NAME)
        # Direct access to app's root and config_manager via app_core.app
        self.app_root = self.app_core.app.root
        self.config_manager = self.app_core.app.config_manager
        # self.file_list_panel is accessed directly in methods that need it, e.g. self.app_core.app.file_list_panel

    # --- File/Folder Addition Request Methods (Called by UI panels) ---

    def request_add_files(self, file_paths: List[str]):
        """Requests adding files by path (initiates background task via AppCore)."""
        if not file_paths:
            return
        try:
            self.config_manager.add_recent_directory(os.path.dirname(file_paths[0]))
        except Exception:
            pass  # Ignore errors saving recent dir
        self.config_manager.save_config()
        self.app_core.app.set_status_busy(f"Adding {len(file_paths)} files...", mode="indeterminate")
        self.app_core.start_background_task(self.process_add_files_task, args=(file_paths,))

    def request_add_folder(self, folder_path: str):
        """Requests adding files from a folder (initiates background task via AppCore)."""
        if not folder_path:
            return
        try:
            self.config_manager.add_recent_directory(folder_path)
        except Exception:
            pass
        self.config_manager.save_config()

        supported_files_in_folder = []
        try:
            for entry in os.scandir(folder_path):
                entry_path = Path(entry.path)
                if entry.is_file():
                    file_extension = entry_path.suffix.lower()
                    if file_extension == '.pdf' or file_extension in ['.docx', '.doc'] or file_extension == '.epub':
                        supported_files_in_folder.append(str(entry_path.resolve()))
        except OSError as e:
            self.logger.error(f"Error scanning folder {folder_path}: {e}")
            self.app_core.app.show_message("Folder Error", f"Could not read files from folder:\n{e}", "error")
            return

        if supported_files_in_folder:
            self.logger.info(f"Found {len(supported_files_in_folder)} supported files (PDF, Word, and EPUB) in folder. Starting processing.")
            self.app_core.app.set_status_busy(f"Adding {len(supported_files_in_folder)} files from folder...", mode="indeterminate")
            self.app_core.start_background_task(self.process_add_files_task, args=(supported_files_in_folder,))
        else:
            self.logger.info(f"No supported files found in {folder_path}.")
            self.app_core.app.show_message("No Supported Files Found", f"No PDF files, Word documents, or EPUB e-books found in {folder_path}", "info")

    def request_add_from_archive(self, archive_path: str):
        """Requests extracting and adding files from an archive (initiates background task via AppCore)."""
        if not archive_path:
            return
        try:
            self.config_manager.add_recent_directory(os.path.dirname(archive_path))
        except Exception:
            pass
        self.config_manager.save_config()

        self.app_core.app.set_status_busy(STATUS_EXTRACTION_STARTING.format(os.path.basename(archive_path)), mode="indeterminate")
        self.app_core.start_background_task(self.process_extract_from_archive_task, args=(archive_path,))

    def request_paste_files(self):
        """Requests adding file paths from the clipboard (initiates background task via AppCore)."""
        try:
            clipboard_content = self.app_root.clipboard_get()
            self.logger.debug(f"Clipboard content obtained: '{clipboard_content[:100]}...'")
        except tk.TclError:
            self.logger.warning("Clipboard empty or does not contain text.")
            self.app_core.app.show_message("Clipboard Empty", "Clipboard does not contain text or cannot be accessed.", "warning")
            return

        potential_paths_list = []
        try:
            potential_paths_list = self.app_root.tk.splitlist(clipboard_content)
        except tk.TclError:
            self.logger.warning(f"TclError splitting clipboard content: '{clipboard_content}'. Falling back to manual parsing.")
            potential_paths_list = [line.strip().strip('"').strip("'") for line in clipboard_content.strip().replace('\r\n', '\n').splitlines() if line.strip()]

        supported_files_from_clipboard = []
        for path_str in potential_paths_list:
            if path_str:
                path_obj = Path(path_str)
                if path_obj.is_file():
                    file_extension = path_obj.suffix.lower()
                    if file_extension == '.pdf' or file_extension in ['.docx', '.doc'] or file_extension == '.epub':
                        try:
                            resolved_path = str(path_obj.resolve())
                            supported_files_from_clipboard.append(resolved_path)
                            self.logger.debug(f"Identified supported file from clipboard: {resolved_path}")
                        except Exception as e:
                            self.logger.warning(f"Could not resolve path '{path_str}' from clipboard: {e}")

        if supported_files_from_clipboard:
            self.logger.info(f"Found {len(supported_files_from_clipboard)} valid supported file paths in clipboard. Processing.")
            self.app_core.app.set_status_busy(f"Adding {len(supported_files_from_clipboard)} files from clipboard...", mode="indeterminate")
            self.app_core.start_background_task(self.process_add_files_task, args=(supported_files_from_clipboard,))
        else:
            self.logger.info("No valid supported file paths found in clipboard content.")
            self.app_core.app.show_message("No Supported Files Pasted", "No valid PDF, Word document, or EPUB e-book file paths found in clipboard content.", "info")

    def handle_drop(self, event):
        """Handles drag-and-drop events to add files or folders (initiates background task via AppCore)."""
        self.logger.info(f"File drop event detected. Data: '{event.data[:100]}...'")
        try:
            dropped_paths_raw = self.app_root.tk.splitlist(event.data)
            self.logger.debug(f"Parsed dropped paths using tk.splitlist: {dropped_paths_raw}")
        except tk.TclError:
            self.logger.warning(f"TclError splitting dropped paths: '{event.data}'. Falling back to manual parsing.")
            dropped_paths_raw = event.data.strip().strip('{').strip('}').replace('} {', '\n').splitlines()
            dropped_paths_raw = [p.strip().strip('"').strip("'") for p in dropped_paths_raw if p.strip()]

        dropped_items = [Path(p) for p in dropped_paths_raw if p]
        files_to_add = []  # Changed from pdf_files_to_add to include Word files
        archives_to_process = []

        for path_obj in dropped_items:
            try:
                resolved_path = path_obj.resolve()
            except Exception as e:
                self.logger.warning(f"Could not resolve dropped path {path_obj}: {e}")
                continue
            if not resolved_path.exists():
                self.logger.warning(f"Dropped path does not exist after resolving: {resolved_path}")
                continue
            if resolved_path.is_file():
                file_extension = resolved_path.suffix.lower()
                if file_extension == '.pdf':
                    files_to_add.append(str(resolved_path))
                elif file_extension in ['.docx', '.doc']:
                    files_to_add.append(str(resolved_path))  # Add Word files to processing list
                elif file_extension == '.epub':
                    files_to_add.append(str(resolved_path))  # Add EPUB files to processing list
                elif file_extension in ['.zip', '.rar']:
                    if file_extension == '.rar' and not RARFILE_AVAILABLE:
                        self.logger.warning(f"Dropped RAR archive '{resolved_path}', but rarfile is not available. Skipping.")
                        self.app_core.app.show_message("RAR Support Missing", "'rarfile' library not found. Cannot process RAR archives.", "warning")
                        continue
                    archives_to_process.append(str(resolved_path))
            elif resolved_path.is_dir():
                try:
                    for entry in os.scandir(resolved_path):
                        entry_path = Path(entry.path)
                        if entry.is_file():
                            entry_extension = entry_path.suffix.lower()
                            if entry_extension == '.pdf':
                                files_to_add.append(str(entry_path.resolve()))
                            elif entry_extension in ['.docx', '.doc']:
                                files_to_add.append(str(entry_path.resolve()))  # Add Word files from folders
                            elif entry_extension == '.epub':
                                files_to_add.append(str(entry_path.resolve()))  # Add EPUB files from folders
                except OSError as e:
                    self.logger.warning(f"Could not scan directory {resolved_path} from drop: {e}")

        if files_to_add:
            self.logger.info(f"Found {len(files_to_add)} files (PDF, Word, and EPUB) from drop. Processing.")
            if files_to_add:
                try:
                    self.config_manager.add_recent_directory(os.path.dirname(files_to_add[0]))
                except Exception:
                    pass
            self.config_manager.save_config()
            self.app_core.app.set_status_busy(f"Adding {len(files_to_add)} files from drop...", mode="indeterminate")
            self.app_core.start_background_task(self.process_add_files_task, args=(files_to_add,))

        if archives_to_process:
            self.logger.info(f"Found {len(archives_to_process)} archives from drop. Processing...")
            if not self.app_core.app.background_task.is_running():
                first_archive = archives_to_process[0]
                self.app_core.app.set_status_busy(STATUS_EXTRACTION_STARTING.format(os.path.basename(first_archive)), mode="indeterminate")
                self.app_core.start_background_task(self.process_extract_from_archive_task, args=(first_archive,))
                if len(archives_to_process) > 1:
                    self.app_core.app.show_message("Multiple Archives Dropped", f"Multiple archives were dropped. Only the first one ({os.path.basename(first_archive)}) will be processed now.", "info")
            else:
                self.app_core.app.show_message("Task Busy", "Cannot process dropped archives because a background task is already running.", "warning")

        if not files_to_add and not archives_to_process and dropped_items:
            self.app_core.app.show_message("No Supported Files Dropped", "No valid PDF files, Word documents, EPUB e-books, or supported archives were found in the dropped items.", "warning")

    # --- Background Task Implementations for File Processing ---

    def convert_epub_to_pdf(self, epub_path: str, output_dir: str) -> Optional[str]:
        """
        Converts an EPUB e-book to PDF using ebooklib and weasyprint.
        
        Args:
            epub_path: Path to the EPUB file
            output_dir: Directory where the converted PDF should be saved
            
        Returns:
            Path to the converted PDF file, or None if conversion failed
        """
        if not EPUB_CONVERSION_AVAILABLE:
            self.logger.error("EPUB conversion requested but required libraries are not available")
            return None
            
        try:
            from common_imports import ebooklib, epub, weasyprint
            
            epub_file = Path(epub_path)
            if not epub_file.exists():
                self.logger.error(f"EPUB file does not exist: {epub_path}")
                return None
                
            # Create output PDF path with same name but .pdf extension
            pdf_filename = epub_file.stem + ".pdf"
            output_pdf_path = os.path.join(output_dir, pdf_filename)
            
            self.logger.info(f"Converting EPUB e-book {epub_file.name} to PDF")
            
            # Read EPUB file
            book = epub.read_epub(epub_path)
            
            # Extract HTML content from EPUB
            html_content = []
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    content = item.get_content().decode('utf-8')
                    html_content.append(content)
            
            if not html_content:
                self.logger.error(f"No readable content found in EPUB: {epub_path}")
                return None
            
            # Combine HTML content into a single document
            combined_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>{book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else epub_file.stem}</title>
                <style>
                    body {{ font-family: serif; line-height: 1.6; margin: 2cm; }}
                    h1, h2, h3 {{ color: #333; }}
                    p {{ margin-bottom: 1em; }}
                </style>
            </head>
            <body>
                {''.join(html_content)}
            </body>
            </html>
            """
            
            # Convert HTML to PDF using weasyprint
            weasyprint.HTML(string=combined_html).write_pdf(output_pdf_path)
            
            if Path(output_pdf_path).exists():
                self.logger.info(f"Successfully converted {epub_file.name} to PDF")
                return output_pdf_path
            else:
                self.logger.error(f"Conversion completed but output file not found: {output_pdf_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error converting EPUB e-book {epub_path} to PDF: {e}", exc_info=True)
            return None

    def convert_word_to_pdf(self, word_path: str, output_dir: str) -> Optional[str]:
        """
        Converts a Word document to PDF using docx2pdf.
        
        Args:
            word_path: Path to the Word document (.doc or .docx)
            output_dir: Directory where the converted PDF should be saved
            
        Returns:
            Path to the converted PDF file, or None if conversion failed
        """
        if not WORD_CONVERSION_AVAILABLE:
            self.logger.error("Word conversion requested but docx2pdf is not available")
            return None
            
        try:
            word_file = Path(word_path)
            if not word_file.exists():
                self.logger.error(f"Word file does not exist: {word_path}")
                return None
                
            # Create output PDF path with same name but .pdf extension
            pdf_filename = word_file.stem + ".pdf"
            output_pdf_path = os.path.join(output_dir, pdf_filename)
            
            self.logger.info(f"Converting Word document {word_file.name} to PDF")
            
            # Convert using docx2pdf
            # The convert function can handle both .doc and .docx files
            convert(word_path, output_pdf_path)
            
            if Path(output_pdf_path).exists():
                self.logger.info(f"Successfully converted {word_file.name} to PDF")
                return output_pdf_path
            else:
                self.logger.error(f"Conversion completed but output file not found: {output_pdf_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error converting Word document {word_path} to PDF: {e}", exc_info=True)
            return None

    def process_add_files_task(self, file_paths: List[str], temp_dir_to_clean_path_str: Optional[str] = None) -> Tuple[str, Tuple[List[Dict], List[Tuple[str, str]], Optional[str]]]:
        """Background task to process a list of file paths, converting Word and EPUB files to PDF and validating them."""
        self.logger.info(f"Background task: Processing {len(file_paths)} potential files for addition.")
        new_docs_data = []
        problematic_files: List[Tuple[str, str]] = []
        total_paths = len(file_paths)
        processed_count = 0
        
        # Create temporary directory for conversions if needed
        temp_conversion_dir = None
        word_files_converted = 0
        epub_files_converted = 0
        
        # Separate different file types
        word_files = []
        epub_files = []
        pdf_files = []
        
        for path_str in file_paths:
            path = Path(path_str)
            if not path.is_file():
                self.logger.warning(f"Skipping non-existent path: {path}")
                problematic_files.append((path_str, "File not found"))
                continue
                
            file_extension = path.suffix.lower()
            if file_extension == '.pdf':
                pdf_files.append(path_str)
            elif file_extension in ['.docx', '.doc']:
                word_files.append(path_str)
            elif file_extension == '.epub':
                epub_files.append(path_str)
            else:
                self.logger.warning(f"Skipping unsupported file type: {path}")
                problematic_files.append((path_str, f"Unsupported file type: {file_extension}"))

        # Convert Word files to PDF if any exist
        if word_files:
            if not WORD_CONVERSION_AVAILABLE:
                self.logger.error("Word files found but conversion not available")
                for word_file in word_files:
                    problematic_files.append((word_file, STATUS_WORD_SUPPORT_MISSING))
            else:
                try:
                    if not temp_conversion_dir:
                        temp_conversion_dir = Path(tempfile.mkdtemp(prefix="pdfmergerpro_wordconv_"))
                        self.logger.info(f"Created temporary conversion directory: {temp_conversion_dir}")
                        
                        # Track this directory for cleanup on app exit
                        if temp_conversion_dir not in self.app_core.app.temp_conversion_dirs:
                            self.app_core.app.temp_conversion_dirs.append(temp_conversion_dir)
                            self.logger.debug(f"Tracking temporary conversion directory for app exit cleanup: {temp_conversion_dir}")
                    
                    for word_file in word_files:
                        processed_count += 1
                        progress = int((processed_count / total_paths) * 100)
                        word_filename = Path(word_file).name
                        self.app_core.app.queue_task_result(("success", ("progress_update", (STATUS_CONVERTING_WORD.format(word_filename), progress))))
                        
                        converted_pdf = self.convert_word_to_pdf(word_file, str(temp_conversion_dir))
                        if converted_pdf:
                            pdf_files.append(converted_pdf)  # Add converted PDF to processing list
                            word_files_converted += 1
                            self.logger.info(f"Successfully converted {word_filename} to PDF")
                        else:
                            problematic_files.append((word_file, STATUS_WORD_CONVERSION_ERROR.format(word_filename)))
                            
                except Exception as e:
                    self.logger.error(f"Error setting up Word conversion: {e}", exc_info=True)
                    for word_file in word_files:
                        problematic_files.append((word_file, f"Word conversion setup error: {e}"))

        # Convert EPUB files to PDF if any exist
        if epub_files:
            if not EPUB_CONVERSION_AVAILABLE:
                self.logger.error("EPUB files found but conversion not available")
                for epub_file in epub_files:
                    problematic_files.append((epub_file, STATUS_EPUB_SUPPORT_MISSING))
            else:
                try:
                    if not temp_conversion_dir:
                        temp_conversion_dir = Path(tempfile.mkdtemp(prefix="pdfmergerpro_epubconv_"))
                        self.logger.info(f"Created temporary conversion directory: {temp_conversion_dir}")
                        
                        # Track this directory for cleanup on app exit
                        if temp_conversion_dir not in self.app_core.app.temp_conversion_dirs:
                            self.app_core.app.temp_conversion_dirs.append(temp_conversion_dir)
                            self.logger.debug(f"Tracking temporary conversion directory for app exit cleanup: {temp_conversion_dir}")
                    
                    for epub_file in epub_files:
                        processed_count += 1
                        progress = int((processed_count / total_paths) * 100)
                        epub_filename = Path(epub_file).name
                        self.app_core.app.queue_task_result(("success", ("progress_update", (STATUS_CONVERTING_EPUB.format(epub_filename), progress))))
                        
                        converted_pdf = self.convert_epub_to_pdf(epub_file, str(temp_conversion_dir))
                        if converted_pdf:
                            pdf_files.append(converted_pdf)  # Add converted PDF to processing list
                            epub_files_converted += 1
                            self.logger.info(f"Successfully converted {epub_filename} to PDF")
                        else:
                            problematic_files.append((epub_file, STATUS_EPUB_CONVERSION_ERROR.format(epub_filename)))
                            
                except Exception as e:
                    self.logger.error(f"Error setting up EPUB conversion: {e}", exc_info=True)
                    for epub_file in epub_files:
                        problematic_files.append((epub_file, f"EPUB conversion setup error: {e}"))

        # Now process all PDF files (original + converted)
        for path_str in pdf_files:
            processed_count += 1
            path = Path(path_str)
            progress = int((processed_count / total_paths) * 100)
            self.app_core.app.queue_task_result(("success", ("progress_update", (f"Processing {path.name}...", progress))))

            try:
                resolved_path_str = str(path.resolve())
                is_encrypted = False
                page_count = 0
                try:
                    with open(resolved_path_str, 'rb') as f:
                        reader = PdfReader(f)
                        is_encrypted = reader.is_encrypted
                        if not is_encrypted:
                             page_count = len(reader.pages)
                        del reader
                except Exception as e_pypdf_check:
                    self.logger.warning(f"pypdf check failed for {path.name}: {e_pypdf_check}", exc_info=True)
                    problematic_files.append((path_str, f"Could not read with pypdf: {e_pypdf_check}"))
                    continue

                if is_encrypted:
                    self.logger.warning(f"Skipping encrypted PDF: {path.name}")
                    problematic_files.append((path_str, "Encrypted/Password Protected"))
                    continue
                
                if page_count > 0:
                    new_docs_data.append({
                        'filepath': resolved_path_str,
                        'filename': path.name,
                        'page_count': page_count,
                    })
                else:
                    self.logger.warning(f"Skipping PDF with 0 pages: {path.name}")
                    problematic_files.append((path_str, "No pages found or load error"))
            except Exception as e:
                self.logger.error(f"Error processing file {path}: {e}", exc_info=True)
                problematic_files.append((path_str, f"General error: {e}"))

        # Determine which temp directory to track for cleanup
        temp_dir_for_cleanup = None
        if temp_conversion_dir and temp_conversion_dir.exists():
            temp_dir_for_cleanup = str(temp_conversion_dir)
        elif temp_dir_to_clean_path_str:
            temp_dir_for_cleanup = temp_dir_to_clean_path_str

        self.logger.info(f"Background task: Processed {len(new_docs_data)} files for addition. Converted {word_files_converted} Word documents and {epub_files_converted} EPUB e-books.")
        return "files_added", (new_docs_data, problematic_files, temp_dir_for_cleanup)

    def process_load_list_task(self, file_details: List[Dict]) -> Tuple[str, Tuple[List[Dict], List[Tuple[str, str]], Optional[str]]]:
        """Background task to process file details loaded from a list/profile file."""
        self.logger.info(f"Background task: Processing {len(file_details)} file details from loaded list.")
        loaded_docs_details = []
        problematic_files: List[Tuple[str, str]] = []
        processed_count = 0
        total_count = len(file_details)

        for detail in file_details:
            processed_count += 1
            filepath = detail.get("filepath")
            selected_pages_from_list = detail.get("selected_pages", [])
            progress = int((processed_count / total_count) * 100)
            self.app_core.app.queue_task_result(("success", ("progress_update", (f"Loading {os.path.basename(filepath or 'N/A')}...", progress))))

            if not filepath or not Path(filepath).is_file():
                self.logger.warning(f"Skipping invalid/missing file from list: {filepath}")
                problematic_files.append((filepath or "N/A", "File not found or invalid path"))
                continue
            
            try:
                is_encrypted = False
                page_count = 0
                resolved_path_str = str(Path(filepath).resolve())
                try:
                    with open(resolved_path_str, 'rb') as f:
                        reader = PdfReader(f)
                        is_encrypted = reader.is_encrypted
                        if not is_encrypted:
                            page_count = len(reader.pages)
                        del reader
                except Exception as e_pypdf_check:
                    self.logger.warning(f"pypdf check failed for {os.path.basename(filepath)}: {e_pypdf_check}", exc_info=True)
                    problematic_files.append((filepath, f"Could not read with pypdf: {e_pypdf_check}"))
                    continue

                if is_encrypted:
                    self.logger.warning(f"Skipping encrypted PDF from list: {os.path.basename(filepath)}")
                    problematic_files.append((filepath, "Encrypted/Password Protected"))
                    continue

                if page_count > 0:
                    valid_selected_pages = [p for p in selected_pages_from_list if isinstance(p, int) and 0 <= p < page_count]
                    loaded_docs_details.append({
                        'filepath': resolved_path_str,
                        'filename': os.path.basename(filepath),
                        'page_count': page_count,
                        'selected_pages': valid_selected_pages
                    })
                    if len(valid_selected_pages) != len(selected_pages_from_list):
                         self.logger.warning(f"File {filepath} from list had invalid page indices.")
                else:
                    problematic_files.append((filepath, "No pages found or load error"))
            except Exception as e:
                self.logger.error(f"Error loading document {filepath} from list: {e}", exc_info=True)
                problematic_files.append((filepath, f"General error: {e}"))

        self.logger.info(f"Background task: Finished processing list. Found {len(loaded_docs_details)} valid documents.")
        return "files_added", (loaded_docs_details, problematic_files, None)

    def process_extract_from_archive_task(self, archive_path: str) -> Tuple[str, Tuple[List[str], Optional[str]]]:
        """Background task to extract PDF files from a ZIP or RAR archive."""
        self.logger.info(f"Starting extraction task from archive: {archive_path}")
        extracted_pdf_paths: List[str] = []
        temp_extract_dir_path: Optional[Path] = None

        try:
            temp_extract_dir_path = Path(tempfile.mkdtemp(prefix="pdfmergerpro_extract_"))
            self.logger.info(f"Created temporary extraction directory: {temp_extract_dir_path}")
            file_extension = Path(archive_path).suffix.lower()

            if file_extension == ".zip":
                try:
                    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                        for member_name in zip_ref.namelist():
                            expected_path = (temp_extract_dir_path / member_name).resolve()
                            if not expected_path.is_relative_to(temp_extract_dir_path.resolve()):
                                self.logger.error(f"Path traversal attempt in ZIP: {member_name}")
                                raise CorruptFileError("Archive contains unsafe paths.")
                        for member_name in zip_ref.namelist():
                            if member_name.lower().endswith(".pdf"):
                                try:
                                    extracted_file_path_str = zip_ref.extract(member_name, path=temp_extract_dir_path)
                                    canonical_extracted_path = Path(extracted_file_path_str).resolve()
                                    if canonical_extracted_path.is_relative_to(temp_extract_dir_path.resolve()):
                                        extracted_pdf_paths.append(str(canonical_extracted_path))
                                except Exception as e_extract:
                                    self.logger.error(f"Error extracting '{member_name}' from ZIP: {e_extract}", exc_info=True)
                except zipfile.BadZipFile as e:
                    raise CorruptFileError(f"Corrupt ZIP file: {e}")
            elif file_extension == ".rar" and RARFILE_AVAILABLE:
                try:
                    with rarfile.RarFile(archive_path, 'r') as rar_ref:
                        if rar_ref.needs_multipart():
                            raise CorruptFileError("Multi-volume RAR archives are not supported.")
                        for member in rar_ref.infolist():
                            if not member.isdir() and member.filename.lower().endswith(".pdf"):
                                try:
                                    rar_ref.extract(member, path=str(temp_extract_dir_path))
                                    extracted_file_path_str = os.path.join(temp_extract_dir_path, member.filename)
                                    canonical_extracted_path = Path(extracted_file_path_str).resolve()
                                    if canonical_extracted_path.is_relative_to(temp_extract_dir_path.resolve()):
                                        extracted_pdf_paths.append(str(canonical_extracted_path))
                                except Exception as e_extract:
                                    self.logger.error(f"Error extracting '{member.filename}' from RAR: {e_extract}", exc_info=True)
                except rarfile.BadRarFile as e:
                    raise CorruptFileError(f"Corrupt RAR file: {e}")
                except rarfile.NoUnrarTool:
                    raise FileHandlingError("RAR processing requires 'unrar' tool to be installed and in the system's PATH.")
            elif file_extension == ".rar" and not RARFILE_AVAILABLE:
                raise FileHandlingError("RAR processing not available (rarfile library missing).")
            else:
                raise FileHandlingError(f"Unsupported archive type: {file_extension}")

            temp_dir_str_for_tracking = str(temp_extract_dir_path) if extracted_pdf_paths else None
            if not extracted_pdf_paths and temp_extract_dir_path and temp_extract_dir_path.exists():
                if not any(temp_extract_dir_path.iterdir()): temp_extract_dir_path.rmdir()

            return "archive_extracted", (extracted_pdf_paths, temp_dir_str_for_tracking)
        except Exception as e_main:
            self.logger.error(f"Error in archive extraction for '{archive_path}': {e_main}", exc_info=True)
            if temp_extract_dir_path and temp_extract_dir_path.exists():
                shutil.rmtree(temp_extract_dir_path, ignore_errors=True)
            raise

    # --- File List Save/Load Operations ---
    def save_file_list(self):
        """Saves the current list of files and their page ranges to a JSON file."""
        if not self.app_core.get_documents():
            self.app_core.app.show_message("No Files", "There are no files in the list to save.", "info")
            self.logger.info("Save file list requested, but list is empty.")
            return
        self.logger.info("Save file list dialog initiated.")

        initial_dir = self.config_manager.config.get("default_output_dir", str(Path.home()))
        default_filename = "pdf_list.json"

        path = filedialog.asksaveasfilename(
            title="Save File List As",
            initialdir=initial_dir,
            initialfile=default_filename,
            defaultextension=".json",
            filetypes=[JSON_FILETYPE, ALL_FILES_FILETYPE],
            parent=self.app_root
        )
        if path:
            try:
                # Access file_list_panel via app_core.app, assuming it's initialized by the time this is called
                list_data = self.app_core.app.file_list_panel.get_file_list_details_for_save()
                save_data = {
                    PROFILE_LIST_KEY: list_data,
                    "version": APP_VERSION,
                    "timestamp": datetime.now().isoformat()
                }
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, indent=2)

                self.app_core.app.set_status(STATUS_FILE_LIST_SAVED.format(Path(path).name))
                self.app_core.app.show_message("Success", "File list saved successfully.", "info")
                try:
                    self.config_manager.add_recent_directory(os.path.dirname(path))
                except Exception:
                    pass
                self.config_manager.save_config()
            except (IOError, json.JSONDecodeError) as e:
                raise FileHandlingError(f"Could not save file list: {e}")
        else:
            self.logger.info("Save file list dialog cancelled.")

    def load_file_list(self):
        """Loads a file list and their page ranges from a JSON file."""
        self.logger.info("Load file list dialog initiated.")
        initial_dir = self.config_manager.config.get("default_output_dir", str(Path.home()))

        path = filedialog.askopenfilename(
            title="Load File List",
            initialdir=initial_dir,
            filetypes=[JSON_FILETYPE, ALL_FILES_FILETYPE],
            parent=self.app_root
        )
        if not path:
            self.logger.info("Load file list dialog cancelled.")
            return

        self.logger.info(f"Attempting to load file list from: {path}")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if PROFILE_LIST_KEY not in data or not isinstance(data[PROFILE_LIST_KEY], list):
                raise FileHandlingError(f"The selected file '{Path(path).name}' does not appear to be a valid {APP_NAME} file list.")

            if self.app_core.get_documents() and not self.app_core.app.ask_yes_no("Confirm Load", "Clear current list and load files from the selected list?"):
                self.logger.info("User cancelled loading file list over existing files.")
                return

            self.app_core.clear_documents()
            file_details_to_add = data[PROFILE_LIST_KEY]

            if not file_details_to_add:
                self.app_core.app.show_message("No Files Loaded", "No valid, existing files found in the list to load.", "info")
                self.app_core.app.update_ui()
                return

            self.app_core.app.set_status_busy(f"Loading {len(file_details_to_add)} files from list...", mode="indeterminate")
            self.app_core.start_background_task(self.process_load_list_task, args=(file_details_to_add,))

            try:
                self.config_manager.add_recent_directory(os.path.dirname(path))
            except Exception:
                pass
            self.config_manager.save_config()
        except (IOError, json.JSONDecodeError) as e:
            raise FileHandlingError(f"Could not load file list: {e}")