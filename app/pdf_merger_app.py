import os
import sys
import json
import logging
import zipfile
import tempfile
import shutil
import time
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path
from datetime import datetime
import tkinter.simpledialog
import queue # Explicitly import queue module

# Core dependencies
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
import tkinterdnd2 as tkdnd

# PDF processing libraries - use centralized imports
from app.common_imports import pymupdf, PdfWriter, PdfReader, RARFILE_AVAILABLE

# Import refactored classes and constants
from app.constants import (
    APP_NAME, APP_VERSION, LOGGER_NAME, DEFAULT_CONFIG_PATH,
    DEFAULT_OUTPUT_FILENAME, STATUS_READY, STATUS_NO_FILES,
    STATUS_FILES_LOADED, PROFILE_LIST_KEY, VALIDATION_REPORT_MAX_ISSUES,
    STATUS_ARCHIVE_PROCESSED_NO_PDFS, STATUS_ARCHIVE_ERROR,
    ALL_FILES_FILETYPE, PDF_FILETYPE, JSON_FILETYPE,
    ZIP_FILETYPE, RAR_FILETYPE, ARCHIVE_FILETYPES, WINDOW_GEOMETRY_KEY,
    PANEDWINDOW_SASH_KEY, STATUS_PROFILE_DELETED, STATUS_PROFILE_LOADED,
    STATUS_PROFILE_SAVED,
    DEFAULT_COMPRESSION,
    DEFAULT_PRESERVE_BOOKMARKS,
    DEFAULT_PASSWORD_PROTECT,
    DEFAULT_COLOR_MODE,
    DEFAULT_DPI,
    STATUS_ADDED_FILES,
    STATUS_NO_VALID_ADDED,
    DEFAULT_LOG_FILE_PATH,
    STATUS_EXTRACTION_STARTING,
    STATUS_REMOVED_FILES, 
    STATUS_LIST_CLEARED,
    STATUS_FILE_LIST_SAVED,
    TASK_QUEUE_CHECK_INTERVAL,
    DELETE_PROFILE_DIALOG_WIDTH,
    DELETE_PROFILE_DIALOG_HEIGHT
)
from app.utils import setup_application_logging
from app.tooltip import Tooltip
from app.background_task import BackgroundTask
from app.pdf_document import PDFDocument
from app.config_manager import ConfigManager

# Import the new manager classes
from app.app_core import AppCore
from app.app_initializer import AppInitializer
from app.layout_manager import LayoutManager
from app.menu_manager import MenuManager
from app.keyboard_manager import KeyboardManager

# Import the panel classes
from app.status_bar import StatusBar
from app.output_panel import OutputPanel
from app.action_panel import ActionPanel
from app.preview_panel import PreviewPanel
from app.file_list_panel import FileListPanel


class PDFMergerApp:
    """Main application class orchestrating the UI panels and core logic."""
    def __init__(self, root: tkdnd.TkinterDnD.Tk):
        self.root = root
        self.root.title(f"{APP_NAME} {APP_VERSION}")

        # 1. Initialize ConfigManager (needed for logging setup)
        self.config_manager = ConfigManager()

        # 2. Setup Logging based on config
        setup_application_logging(self.config_manager.config)
        self.logger = logging.getLogger(LOGGER_NAME)
        self.logger.info(f"{APP_NAME} v{APP_VERSION} initializing.")

        # 3. Load and apply window state (geometry, sash positions)
        self._saved_geometry, self._saved_sash_positions = self.config_manager.load_window_state()

        # 4. Initialize Manager Classes
        self.app_core = AppCore(self)
        self.app_initializer = AppInitializer(self)
        self.layout_manager = LayoutManager(self)
        self.menu_manager = MenuManager(self)
        self.keyboard_manager = KeyboardManager(self)

        # 5. Setup window geometry and state
        self.layout_manager.setup_window_geometry(self._saved_geometry, self._saved_sash_positions)

        # 6. Setup Drag and Drop
        self.root.drop_target_register(tkdnd.DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.app_core.handle_drop)

        # 7. Load Application Icon
        self.app_initializer.load_application_icon()

        # 8. Initialize core components and shared state
        self.pdf_documents: List[PDFDocument] = [] # Central list of documents
        self.temp_extraction_dirs: List[Path] = [] # Track temp dirs for cleanup on exit (archive extraction)
        self.temp_conversion_dirs: List[Path] = [] # Track temp dirs for cleanup on exit (Word conversion)
        self.task_queue = queue.Queue() # Queue for background task results
        self.background_task = BackgroundTask(self.task_queue) # Manager for background tasks

        # 9. Initialize shared Tkinter variables
        self.status_text = tk.StringVar(value=STATUS_READY)
        self.progress_value = tk.DoubleVar(value=0.0)
        self.search_term = tk.StringVar()

        # Preview Panel Variables
        self.preview_doc_index = tk.IntVar(value=-1) # Index of doc being previewed (-1 if none)
        self.preview_current_page = tk.IntVar(value=0) # Current page index (0-based)
        self.preview_max_pages = tk.IntVar(value=0) # Max page index (page_count - 1)
        self.preview_current_zoom_display_factor = tk.DoubleVar(value=1.0) # Actual zoom factor
        self.preview_is_fit_to_window = tk.BooleanVar(value=True) # Fit to window flag

        # Output Panel Variables (loaded from config initially)
        default_output_dir = self.config_manager.config.get("default_output_dir", str(Path.home()))
        self.output_path = tk.StringVar(value=os.path.join(default_output_dir, DEFAULT_OUTPUT_FILENAME))
        self.compression_level = tk.StringVar(value=self.config_manager.config.get("compression_level", DEFAULT_COMPRESSION))
        self.preserve_bookmarks = tk.BooleanVar(value=self.config_manager.config.get("preserve_bookmarks", DEFAULT_PRESERVE_BOOKMARKS))
        self.output_password_protect = tk.BooleanVar(value=self.config_manager.config.get("output_password_protect", DEFAULT_PASSWORD_PROTECT))
        self.output_password = tk.StringVar(value="") # Password is NOT loaded from config
        self.output_color_mode = tk.StringVar(value=self.config_manager.config.get("output_color_mode", DEFAULT_COLOR_MODE))
        self.output_dpi = tk.StringVar(value=self.config_manager.config.get("output_dpi", DEFAULT_DPI))

        # 10. Setup Styles
        self.app_initializer.setup_styles()

        # 11. Create UI Panels
        self.layout_manager.create_panels()

        # 12. Create Menu Bar
        self.menu_manager.create_menu_bar()

        # 13. Setup Keyboard Shortcuts
        self.keyboard_manager.setup_keyboard_shortcuts()

        # 14. Start Background Task Queue Monitor
        self.root.after(TASK_QUEUE_CHECK_INTERVAL, self.app_core.check_task_queue)

        # 15. Set Window Close Protocol
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # 16. Apply Saved Sash Positions (after panels are created)
        self.root.after(10, self.layout_manager.apply_saved_sash_positions)

        # 17. Initial UI Update
        self.update_ui() # Update status, button states etc.

        self.logger.info("PDFMergerApp UI initialized.")


    def _on_closing(self):
        """Handles the window close event, saving configuration before exit."""
        self.logger.info("WM_DELETE_WINDOW: Closing application...")
        try:
            if self.preview_panel._resize_job:  # Cancel preview resize job if it exists
                self.root.after_cancel(self.preview_panel._resize_job)
                self.preview_panel._resize_job = None

            # Save current window state
            try:
                window_geometry = self.root.geometry()
                sash_positions = {'upper_panedwindow': self.upper_panedwindow.sashpos()} if hasattr(self, 'upper_panedwindow') and self.upper_panedwindow.winfo_exists() else {}
                self.config_manager.save_window_state(window_geometry, sash_positions)
            except Exception as e:
                self.logger.warning(f"Failed to save window state: {e}")

            # Cleanup temporary directories (if any exist)
            for temp_dir in self.temp_extraction_dirs:
                if temp_dir.exists():
                    try:
                        shutil.rmtree(temp_dir)
                        self.logger.debug(f"Cleaned up temp extraction directory: {temp_dir}")
                    except Exception as cleanup_err:
                        self.logger.warning(f"Failed to cleanup temp extraction directory {temp_dir}: {cleanup_err}")
            
            for temp_dir in self.temp_conversion_dirs:
                if temp_dir.exists():
                    try:
                        shutil.rmtree(temp_dir)
                        self.logger.debug(f"Cleaned up temp conversion directory: {temp_dir}")
                    except Exception as cleanup_err:
                        self.logger.warning(f"Failed to cleanup temp conversion directory {temp_dir}: {cleanup_err}")
        finally:
            # This block will execute whether an exception occurred or not during the try block
            self.logger.info("Proceeding to destroy root window.")
            self.root.destroy()

        # --- Communication Methods (Called by Panels to interact with App/other Panels) ---

    def get_documents(self) -> List[PDFDocument]:
        """Provides access to current documents list via AppCore delegation."""
        return self.app_core.get_documents()

    def get_output_settings(self) -> Dict[str, Any]:
        """Provides access to current output settings from the OutputPanel."""
        # Delegate getting settings to the output panel
        return self.output_panel.get_output_settings()

    def start_background_task(self, target, args=(), kwargs=None):
        """Starts a new background task via the app's task manager."""
        return self.background_task.start(target, args, kwargs)

    def queue_task_result(self, result: Tuple[str, Any]):
        """Allows background tasks to queue results for the main thread."""
        self.task_queue.put(result)

    def update_ui(self):
        """Refreshes all UI elements that depend on application state."""
        # Update File List Panel display
        self.file_list_panel.update_file_list_display()
        self.file_list_panel.update_ui_state() # Update panel-specific UI (like button states)

        # Update Preview Panel state (labels, etc.)
        pdf_documents = self.app_core.get_documents()
        self.preview_panel.update_ui_state(len(pdf_documents))

        # Update Status Bar (unless it's displaying a busy message)
        current_status = self.status_text.get()
        is_busy_status = current_status.startswith("Merging") or \
                         current_status.startswith("Validating") or \
                         current_status.startswith("Loading") or \
                         current_status.startswith("Extracting") or \
                         "..." in current_status

        if not self.background_task.is_running() and not is_busy_status:
             if pdf_documents:
                total_pages_overall = sum(doc.page_count for doc in pdf_documents)
                self.status_bar.set_status(STATUS_FILES_LOADED.format(len(pdf_documents), total_pages_overall))
             else:
                self.status_bar.set_status(STATUS_NO_FILES)

        # Update Action Panel (e.g., Merge button state) - ActionPanel needs a method for this
        # For now, let's update merge button state directly here or via status_bar calls
        self.action_panel.merge_button.config(state=tk.DISABLED if self.background_task.is_running() or not pdf_documents else tk.NORMAL)

        self.logger.debug(f"Full UI update performed. Files: {len(pdf_documents)}, Preview Doc: {self.preview_doc_index.get()}")


    def set_status(self, message: str):
        """Sets the status bar text."""
        self.status_bar.set_status(message)

    def set_status_busy(self, message: str, mode: str = "determinate", maximum: float = 100.0):
        """Sets status bar message and configures/starts progress bar for busy state."""
        self.status_bar.set_status(message)
        self.status_bar.set_progress(0, mode=mode, maximum=maximum)
        if mode == "indeterminate":
            self.status_bar.progress_bar.start()
        else:
            self.status_bar.progress_bar.stop() # Ensure animation is stopped for determinate
        # Disable merge button when busy
        self.action_panel.merge_button.config(state=tk.DISABLED)
        self.root.update_idletasks() # Force UI update


    def clear_progress(self):
         """Clears the progress bar and stops animation."""
         self.status_bar.clear_progress()
         # Re-enable merge button if files exist (handled by _check_task_queue final block)


    def show_message(self, title: str, message: str, level: str = "info", parent=None):
        """Shows a message box."""
        # Use parent=self.root by default if not specified
        msg_parent = parent if parent else self.root
        if level == "info": messagebox.showinfo(title, message, parent=msg_parent)
        elif level == "warning": messagebox.showwarning(title, message, parent=msg_parent)
        elif level == "error": messagebox.showerror(title, message, parent=msg_parent)
        else: messagebox.showinfo(title, message, parent=msg_parent)

    def ask_yes_no(self, title: str, message: str, parent=None) -> bool:
        """Shows a yes/no confirmation message box."""
        # Use parent=self.root by default if not specified
        msg_parent = parent if parent else self.root
        return messagebox.askyesno(title, message, parent=msg_parent)

    def open_file_in_default_app(self, filepath: str):
        """Opens a file using the system's default application."""
        try:
            # Consider using subprocess.run for more robust handling
            # Example: subprocess.run(['open', filepath], check=True) on macOS
            # Example: subprocess.run(['xdg-open', filepath], check=True) on Linux
            # Example: os.startfile(filepath) on Windows
            # Using os.system is simpler but less safe/robust
            if sys.platform == "win32": os.startfile(filepath)
            elif sys.platform == "darwin": os.system(f'open "{filepath}"')
            else: os.system(f'xdg-open "{filepath}"')
        except Exception as e:
            self.logger.error(f"Error opening file '{filepath}': {e}")
            self.show_message("Cannot Open File", f"Could not automatically open the file: {e}", "warning")

    # --- Task Queue Monitoring and Result Handling ---
    # This is now handled by AppCore.check_task_queue()


    # --- Application Data Management (Methods operating on self.pdf_documents) ---
    # These methods delegate to AppCore for actual implementation.

    def request_add_files(self, file_paths: List[str]):
        """Delegates adding files to AppCore -> FileOperations."""
        self.logger.debug("PDFMergerApp: Delegating request_add_files to AppCore -> FileOperations.")
        self.app_core.file_ops.request_add_files(file_paths)

    def request_add_folder(self, folder_path: str):
        """Delegates adding files from a folder to AppCore -> FileOperations."""
        self.logger.debug("PDFMergerApp: Delegating request_add_folder to AppCore -> FileOperations.")
        self.app_core.file_ops.request_add_folder(folder_path)

    def request_add_from_archive(self, archive_path: str):
        """Delegates adding files from an archive to AppCore -> FileOperations."""
        self.logger.debug("PDFMergerApp: Delegating request_add_from_archive to AppCore -> FileOperations.")
        self.app_core.file_ops.request_add_from_archive(archive_path)


    def request_remove_documents_by_index(self, indices_to_remove: List[int]):
        """Delegates removing documents to AppCore."""
        self.logger.debug("PDFMergerApp: Delegating request_remove_documents_by_index to AppCore.")
        self.app_core.remove_documents_by_index(indices_to_remove)

    def request_clear_documents(self):
        """Delegates clearing documents to AppCore."""
        self.logger.debug("PDFMergerApp: Delegating request_clear_documents to AppCore.")
        self.app_core.clear_documents()

    def request_move_document(self, current_idx: int, direction: int):
        """Delegates moving documents to AppCore."""
        self.logger.debug("PDFMergerApp: Delegating request_move_document to AppCore.")
        self.app_core.move_document(current_idx, direction)

    # --- Preview Management ---

    def request_preview_document(self, doc_index: int, page_num: int = 0):
        """Delegates preview document request to AppCore."""
        self.logger.debug("PDFMergerApp: Delegating request_preview_document to AppCore.")
        self.app_core.request_preview_document(doc_index, page_num)

    def set_preview_document(self, doc_index: int):
        """Delegates setting preview document to AppCore."""
        self.logger.debug("PDFMergerApp: Delegating set_preview_document to AppCore.")
        self.app_core.set_preview_document(doc_index)

    # --- File List Save/Load (DELEGATED to AppCore which uses FileOperations) ---
    def _save_file_list(self):
        """Delegates saving the file list to AppCore -> FileOperations."""
        self.logger.debug("PDFMergerApp: Delegating _save_file_list to AppCore.")
        self.app_core.file_ops.save_file_list()

    def _load_file_list(self):
        """Delegates loading the file list to AppCore -> FileOperations."""
        self.logger.debug("PDFMergerApp: Delegating _load_file_list to AppCore.")
        self.app_core.file_ops.load_file_list()


    # --- Profile Management (DELEGATED to AppCore which uses ProfileManager) ---
    def _save_current_as_profile(self):
        """Delegates saving the current list and settings as a profile."""
        self.logger.debug("PDFMergerApp: Delegating _save_current_as_profile to AppCore.")
        self.app_core.save_current_as_profile() # AppCore will call profile_manager

    def _load_profile(self, profile_name: str):
        """Delegates loading a selected profile."""
        self.logger.debug(f"PDFMergerApp: Delegating _load_profile '{profile_name}' to AppCore.")
        self.app_core.load_profile(profile_name) # AppCore will call profile_manager

    def _delete_profile_dialog(self):
        """Delegates opening the delete profile dialog."""
        self.logger.debug("PDFMergerApp: Delegating _delete_profile_dialog to AppCore.")
        self.app_core.delete_profile_dialog() # AppCore will call profile_manager

    # _update_profiles_menu is now fully handled by MenuManager, which gets data from ProfileManager via AppCore.
    # The original _update_profiles_menu in PDFMergerApp was already a stub calling MenuManager.
    # So, no change needed here for _update_profiles_menu as it was already correctly delegated after Phase 2.


    # --- Helper for Placeholder Dialogs ---
    # These were in the original PDFMergerPro and remain here for now.

    def _edit_metadata_dialog(self):
        """Placeholder for metadata editing functionality."""
        self.logger.info("Edit metadata dialog (not implemented) accessed.")
        # Suggestion: Implement a dialog allowing editing of PDF metadata fields.
        self.show_message("Not Implemented", "Metadata editing feature is not yet implemented.", "info")

    def _show_preferences_dialog(self):
        """Placeholder for application preferences/settings."""
        self.logger.info("Preferences dialog (not implemented) accessed.")
        # Suggestion: Implement a dialog for configuration settings.
        self.show_message("Not Implemented", "Preferences feature is not yet implemented.", "info")

    def _show_help_dialog(self):
        """Displays the application help information."""
        self.logger.info("Help dialog accessed.")
        help_text = (
            f"{APP_NAME} - v{APP_VERSION}\n\n"
            "A utility for merging PDF files, Word documents, and EPUB e-books.\n\n"
            "Original Concept & Development: Roey Aharon\n"
            "Enhancements & Refinements: Claude AI & Human Review\n\n"
            "Key Features:\n"
            "- Add PDF files, Word documents (.docx, .doc), and EPUB e-books (.epub) or entire folders (drag & drop supported).\n"
            "- Word documents and EPUB e-books are automatically converted to PDF during merging.\n"
            "- Add files directly from ZIP or RAR archives.\n"
            "- Reorder files using Up/Down buttons.\n" # Note: DnD reordering is a suggestion
            "- Preview PDF pages with zoom (buttons/scroll wheel) and pan (click & drag when zoomed).\n"
            "- Select specific page ranges for each document to include in the merge.\n"
            "- Save and load file lists and profiles (including page ranges and settings).\n"
            "- Output options: Password protection, compression.\n\n"
            "Usage:\n"
            "1. Add PDF files, Word documents, and EPUB e-books via buttons, drag & drop, or paste.\n"
            "2. Double-click a file in the list to preview its contents.\n"
            "3. Select a file and click 'Set Page Range...' to choose specific pages for merging.\n"
            "4. Arrange files in the desired merge order using the Up/Down buttons.\n"
            "5. Set output options (path, compression, password).\n"
            "6. Click 'Merge PDFs'.\n\n"
            "Note: Word document conversion requires the 'docx2pdf' library. EPUB conversion requires\n"
            "'ebooklib' and 'weasyprint' libraries. If not installed, these files will be skipped\n"
            "with appropriate error messages and installation instructions.\n\n"
            f"Log files are stored as '{DEFAULT_LOG_FILE_PATH}' in the application directory (unless configured otherwise in Preferences - Not implemented)."
        )
        self.show_message(f"Help - {APP_NAME}", help_text, "info")

    def _show_about_dialog(self):
        """Displays information about the application."""
        self.logger.info("About dialog accessed.")
        about_text = (
            f"{APP_NAME} - Version {APP_VERSION}\n\n"
            "Advanced PDF merging utility with Word document and EPUB e-book support.\n\n"
            "Original Concept & Development: Roey Aharon\n"
            "Enhancements & Refinements: Claude AI & Human Review\n\n"
            "Built with Python, Tkinter, tkinterdnd2, PyMuPDF, pypdf, docx2pdf, ebooklib, weasyprint, and rarfile."
        )
        self.show_message(f"About {APP_NAME}", about_text, "info")

    def _check_updates(self):
        """Placeholder for check for updates functionality."""
        self.logger.info("Check for updates (not implemented) accessed.")
        # Suggestion: Implement update checking.
        self.show_message("Not Implemented", "Update checking feature is not yet implemented.", "info")


