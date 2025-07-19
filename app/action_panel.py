import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
import logging
import os
import shutil
import tempfile
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import json

# PDF processing libraries - use centralized imports
from app.common_imports import pymupdf, PdfWriter, PdfReader

from app.constants import (
    LOGGER_NAME, MERGE_PROGRESS_FILE_WEIGHT, MERGE_PROGRESS_FINALIZE_WEIGHT,
    VALIDATION_REPORT_MAX_ISSUES, STATUS_MERGE_STARTING, STATUS_MERGE_APPENDING,
    STATUS_MERGE_APPENDING_PAGES, STATUS_MERGE_FINALIZING, STATUS_MERGE_WRITING,
    STATUS_MERGE_MOVING, STATUS_MERGE_SUCCESS, STATUS_VALIDATING_FILE,
    STATUS_VALIDATION_COMPLETE, STATUS_VALIDATION_ISSUES,
    DEFAULT_COMPRESSION, DEFAULT_PRESERVE_BOOKMARKS, DEFAULT_COLOR_MODE, DEFAULT_DPI
)

from app.tooltip import Tooltip
from app.pdf_document import PDFDocument
from app.background_task import BackgroundTask
from app.exceptions import MergeError, ValidationError, PasswordProtectedError

class ActionPanel(ttk.LabelFrame):
    """Represents the Actions section (Merge, Validate) of the UI."""
    def __init__(self, parent, app, **kwargs): # Pass the main application instance
        super().__init__(parent, text="Actions", padding=5, **kwargs)
        self.logger = logging.getLogger(LOGGER_NAME)
        self.app = app # Reference to the main Application class

        self._create_widgets()
        self.logger.debug("ActionPanel initialized.")

    def _create_widgets(self):
        """Creates the widgets within the actions panel."""
        Tooltip(self, "Core actions for processing the PDF list.")

        self.merge_button = ttk.Button(self, text="Merge PDFs", style="Action.TButton", command=self._start_merge_process)
        self.merge_button.pack(padx=5, pady=5, fill=tk.X)
        Tooltip(self.merge_button, "Start the PDF merging process using the current list and settings (Ctrl+M).")

        self.validate_button = ttk.Button(self, text="Validate Files", command=self._validate_files)
        self.validate_button.pack(padx=5, pady=5, fill=tk.X)
        Tooltip(self.validate_button, "Check if all files in the list are valid and readable PDF documents before merging.")

    def _start_merge_process(self):
        """Initiates the PDF merging process."""
        self.logger.info("Initiating merge process.")

        # Get the list of documents from the main application
        pdf_documents = self.app.app_core.get_documents()
        if not pdf_documents:
            self.app.show_message("No Files", "Please add PDF files to the list before merging.", "warning")
            self.logger.warning("Merge requested, but file list is empty.")
            return

        # Get output settings from the OutputPanel (access via main app)
        output_settings = self.app.get_output_settings()
        output_file = output_settings.get("output_path", "").strip()

        if not output_file:
            self.app.show_message("No Output File", "Please specify an output file path.", "warning")
            self.logger.warning("Merge cancelled: No output file path specified.")
            # Prompt user to choose output file (delegated back to app or OutputPanel)
            # The app or OutputPanel would need a public method for this
            # For now, just warn and return
            return

        output_path_obj = Path(output_file)

        # Check if the output file exists and ask for overwrite confirmation
        if output_path_obj.exists():
            if not self.app.ask_yes_no("File Exists", f"Output file '{output_path_obj.name}' already exists. Overwrite?"):
                self.logger.info("User chose not to overwrite existing output file. Merge cancelled.")
                return # User cancelled overwrite, stop merge process
            self.logger.info(f"User chose to overwrite existing output file: {output_file}")
        else:
             # Ensure the output directory exists
             try:
                 output_path_obj.parent.mkdir(parents=True, exist_ok=True)
             except OSError as e:
                  raise MergeError(f"Could not create output directory:\n{output_path_obj.parent}\n{e}")


        # Check password requirement if enabled
        password_to_use: Optional[str] = None
        if output_settings.get("password_protect"):
            password_to_use = output_settings.get("password")
            if not password_to_use:
                self.app.show_message("Password Missing", "Password protection is enabled, but no password is set.", "warning")
                self.logger.warning("Merge cancelled: Password protection enabled but no password set.")
                return # Cannot proceed without a password

        # Prepare the list of documents and selected pages for the merge task
        docs_to_merge_info = []
        total_pages_to_merge = 0
        for doc in pdf_documents:
            # Ensure selected pages are valid indices for this document
            valid_selected_pages = [p for p in doc.selected_pages if isinstance(p, int) and 0 <= p < doc.page_count]
            if valid_selected_pages:
                # Store only the necessary info for the background task
                docs_to_merge_info.append({'filepath': doc.filepath, 'selected_pages': valid_selected_pages})
                total_pages_to_merge += len(valid_selected_pages)
            else:
                 self.logger.warning(f"Document {doc.filename} has no pages selected or no valid pages. Skipping from merge.")

        if not docs_to_merge_info:
            self.app.show_message("No Pages to Merge", "No documents have any pages selected for merging.", "warning")
            self.logger.warning("Merge cancelled: No documents/pages selected for merging.")
            return # No pages to merge after checking selected ranges

        # Get other merge options from the OutputPanel (passed via output_settings)
        compression_level = output_settings.get("compression_level", DEFAULT_COMPRESSION)
        preserve_bookmarks = output_settings.get("preserve_bookmarks", DEFAULT_PRESERVE_BOOKMARKS)
        color_mode_val = output_settings.get("color_mode", DEFAULT_COLOR_MODE)
        dpi_setting_val = output_settings.get("dpi", DEFAULT_DPI)

        self.logger.info(f"Starting merge task for {len(docs_to_merge_info)} documents ({total_pages_to_merge} pages). Output: {output_file}, PreserveBookmarks: {preserve_bookmarks}, Compression: {compression_level}, PasswordProtected: {bool(password_to_use)}, ColorMode: {color_mode_val}, DPI: {dpi_setting_val}")

        # Update UI status and disable button via main app
        self.app.set_status_busy(STATUS_MERGE_STARTING, mode="determinate", maximum=MERGE_PROGRESS_FILE_WEIGHT)

        # Start the merge process in a background task via the main app's task manager
        self.app.start_background_task(
            self._perform_merge_task,
            args=(docs_to_merge_info, output_file, preserve_bookmarks, compression_level, password_to_use, color_mode_val, dpi_setting_val)
        )


    def _perform_merge_task(self, docs_info: List[Dict], output_path: str, preserve_bookmarks: bool, compression_level: str, password: Optional[str], color_mode: str, dpi_setting: str) -> Tuple[str, Tuple[str, float]]:
        """
        Background task that performs the actual PDF merging using pypdf.
        Handles appending pages, compression, and encryption.
        Reports progress via the task queue.
        Returns ("merge_complete", (output_filepath, final_size_mb)) on success.
        Raises exception on failure.
        """
        merger = PdfWriter()
        total_docs = len(docs_info)
        total_pages_processed = 0
        total_pages_to_process = sum(len(d['selected_pages']) for d in docs_info)

        temp_output_path: Optional[Path] = None
        output_path_obj = Path(output_path)

        try:
            temp_output_path = output_path_obj.with_suffix(".pdf_part_tmp")
            self.logger.info(f"Merge task: Using temporary file for output: {temp_output_path}")

            # --- Placeholder/Note for Color Mode and DPI ---
            if color_mode != DEFAULT_COLOR_MODE or dpi_setting != DEFAULT_DPI:
                 self.logger.warning(f"Merge task: Color Mode ('{color_mode}') or DPI ('{dpi_setting}') settings are experimental/not functional. Merging with original settings.")
            # --- End Placeholder ---

            # Append pages from each document
            for i, doc_info in enumerate(docs_info):
                filepath = doc_info['filepath']
                selected_pages = doc_info['selected_pages'] # These are 0-indexed indices

                # Report progress (message and percentage)
                file_progress_perc = (i / total_docs) * MERGE_PROGRESS_FILE_WEIGHT
                self.app.queue_task_result(("success", ("progress_update", (STATUS_MERGE_APPENDING.format(Path(filepath).name, i+1, total_docs), file_progress_perc))))

                self.logger.debug(f"Merge task: Appending '{Path(filepath).name}', pages: {selected_pages}")

                reader = None
                try:
                    reader = PdfReader(filepath)
                    if reader.is_encrypted:
                        raise PasswordProtectedError(f"File '{Path(filepath).name}' is password protected.")

                    merger.append(fileobj=reader, pages=selected_pages, import_outline=preserve_bookmarks)

                    total_pages_processed += len(selected_pages)
                    page_progress_perc = (total_pages_processed / total_pages_to_process) * MERGE_PROGRESS_FILE_WEIGHT
                    self.app.queue_task_result(("success", ("progress_update", (STATUS_MERGE_APPENDING_PAGES.format(Path(filepath).name), page_progress_perc))))

                except PasswordProtectedError as e_pwd:
                    self.logger.error(f"Error appending pages from '{Path(filepath).name}': {e_pwd}", exc_info=True)
                    raise MergeError(str(e_pwd)) from e_pwd
                except Exception as e_append:
                    self.logger.error(f"Error appending pages from '{Path(filepath).name}': {e_append}", exc_info=True)
                    raise MergeError(f"Failed to append pages from {Path(filepath).name}") from e_append
                finally:
                    if reader:
                        reader.close()

            # Finalize and save
            self.app.queue_task_result(("success", ("progress_update", (STATUS_MERGE_FINALIZING, MERGE_PROGRESS_FILE_WEIGHT + 1))))

            # Apply compression
            if compression_level != "none":
                self.logger.debug(f"Merge task: Applying compression.")
                try:
                    for page in merger.pages:
                        page.compress_content_streams()
                    self.logger.debug("Merge task: Content streams compressed.")
                except Exception as e_comp:
                    self.logger.warning(f"Error applying compression: {e_comp}. Proceeding without full compression.", exc_info=True)

            # Apply password encryption
            if password:
                self.logger.debug("Merge task: Encrypting PDF.")
                try:
                    merger.encrypt(password)
                    self.logger.debug("Merge task: PDF encrypted.")
                except Exception as e_encrypt:
                    raise MergeError(f"Failed to apply encryption: {e_encrypt}") from e_encrypt

            self.app.queue_task_result(("success", ("progress_update", (STATUS_MERGE_WRITING, MERGE_PROGRESS_FILE_WEIGHT + MERGE_PROGRESS_FINALIZE_WEIGHT // 2))))

            # Write to temporary file
            with open(temp_output_path, "wb") as f_out:
                merger.write(f_out)

            # Ensure merger is closed *before* renaming the file
            merger.close()
            self.logger.debug("Merge task: pypdf merger closed.")

            self.app.queue_task_result(("success", ("progress_update", (STATUS_MERGE_MOVING, MERGE_PROGRESS_FILE_WEIGHT + MERGE_PROGRESS_FINALIZE_WEIGHT - 5))))

            # Atomically replace the target file
            temp_output_path.replace(output_path_obj)
            self.logger.info(f"Merge task: Successful. Temporary file {temp_output_path} moved to {output_path}")
            temp_output_path = None # Clear path after successful move

            final_size_mb = output_path_obj.stat().st_size / (1024 * 1024)

            # On successful completion, queue the result
            self.app.queue_task_result(("success", ("merge_complete", (output_path, final_size_mb))))
            return # Task is complete

        except Exception as e:
            self.logger.error(f"Critical error during PDF merge task for output '{output_path}': {e}", exc_info=True)
            # Clean up temp file on error
            if temp_output_path and temp_output_path.exists():
                try:
                    self.logger.warning(f"Attempting to clean up temporary merge file {temp_output_path} after error.")
                    temp_output_path.unlink()
                    self.logger.info(f"Removed temporary merge file: {temp_output_path}")
                except OSError as e_rem:
                    self.logger.warning(f"Could not remove temporary merge file {temp_output_path} after error: {e_rem}")

            # Determine the type of merge failure
            failure_type = "unknown_merge_error"
            error_message = str(e)

            if isinstance(e, MergeError):
                 failure_type = "merge_append_failure"
                 # The specific file error was already queued by the loop
                 error_message = f"Merge failed during file appending. {error_message}"
            # Add checks for other specific error types during finalization if needed
            elif "encryption" in str(e).lower(): # Simple text check for encryption errors
                 failure_type = "merge_encryption_failure"
            elif "compression" in str(e).lower(): # Simple text check for compression errors
                 failure_type = "merge_compression_failure"

            # Queue the final merge failed status
            self.app.queue_task_result(("error", ("merge_failed", {"type": failure_type, "message": error_message, "output_file": output_path}))) # Report failure via queue

            # Do NOT re-raise here. The error is reported via the queue.
            # The BackgroundTask wrapper will see that no exception was re-raised
            # and will not put a generic "error" on the queue in addition to the one we just added.

        finally:
            # Ensure merger is closed if it was successfully created but an error occurred before closing
            try:
                # Check if merger object exists and is not already closed (_objects will be None after close)
                if 'merger' in locals() and merger._objects is not None:
                     merger.close()
                     self.logger.debug("Merge task finally: Ensured merger was closed.")
            except Exception as e_close:
                 self.logger.warning(f"Error ensuring merger closed in finally block: {e_close}")


    def _validate_files(self):
        """Initiates the file validation process."""
        self.logger.info("Initiating file validation.")

        # Get the list of documents from the main application
        pdf_documents = self.app.app_core.get_documents()
        if not pdf_documents:
            self.app.show_message("No Files", "There are no files to validate.", "info")
            self.logger.info("Validation requested, but list is empty.")
            return

        # Update UI status via main app
        self.app.set_status_busy(STATUS_VALIDATING_FILE.format("", 0, len(pdf_documents)), mode="determinate", maximum=len(pdf_documents))

        # Start validation in a background task via the main app's task manager
        self.app.start_background_task(self._perform_validation_task, args=(pdf_documents,))


    def _perform_validation_task(self, documents: List[PDFDocument]) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Background task to validate PDF documents.
        Checks existence, encryption, and page count/readability.
        Reports progress via the task queue.
        Returns ("validation_complete", list_of_issues).
        """
        self.logger.info(f"Background task: Starting validation for {len(documents)} documents.")
        issues: List[Dict[str, Any]] = [] # List of issue dictionaries
        total_docs = len(documents)

        for i, doc_obj in enumerate(documents):
            # Update progress for the current file via main app's queue
            progress = i + 1
            self.app.queue_task_result(("success", ("progress_update", (STATUS_VALIDATING_FILE.format(doc_obj.filename, progress, total_docs), progress))))

            # Check if file exists
            if not Path(doc_obj.filepath).exists():
                issue_message = f"File not found: {doc_obj.filename}"
                issues.append({
                    "filepath": doc_obj.filepath,
                    "filename": doc_obj.filename,
                    "type": "file_not_found",
                    "message": issue_message
                })
                self.logger.warning(issue_message)
                continue # Skip further checks if file doesn't exist

            pdf_validation_doc = None
            try:
                # Open the document with PyMuPDF for validation checks
                pdf_validation_doc = pymupdf.open(doc_obj.filepath)

                # Check for encryption
                if pdf_validation_doc.is_encrypted:
                    issue_message = f"Password protected/encrypted: {doc_obj.filename}"
                    issues.append({
                        "filepath": doc_obj.filepath,
                        "filename": doc_obj.filename,
                        "type": "encrypted",
                        "message": issue_message
                    })
                    self.logger.warning(issue_message)

                # Check page count
                if pdf_validation_doc.page_count == 0:
                    issue_message = f"File has no pages: {doc_obj.filename}"
                    issues.append({
                         "filepath": doc_obj.filepath,
                         "filename": doc_obj.filename,
                         "type": "no_pages",
                         "message": issue_message
                    })
                    self.logger.warning(issue_message)

                # Attempt to load the first page for basic readability check
                if pdf_validation_doc.page_count > 0:
                    try:
                        pdf_validation_doc.load_page(0)
                        self.logger.debug(f"Successfully validated first page of {doc_obj.filename}.")
                    except pymupdf.errors.MuPDFError as page_err:
                        issue_message = f"Error reading first page: {page_err}"
                        issues.append({
                             "filepath": doc_obj.filepath,
                             "filename": doc_obj.filename,
                             "type": "page_read_error",
                             "message": issue_message
                        })
                        self.logger.warning(issue_message)

            except pymupdf.errors.MuPDFError as e:
                 # Catch any other errors during opening or basic validation
                issue_message = f"Error opening/validating: {e}"
                issues.append({
                     "filepath": doc_obj.filepath,
                     "filename": doc_obj.filename,
                     "type": "open_validation_error",
                     "message": issue_message
                })
                self.logger.warning(issue_message)
            finally:
                if pdf_validation_doc:
                    pdf_validation_doc.close()

        self.logger.info(f"Background task: Validation complete. Found {len(issues)} issue(s).")
        # Return action type and the list of issues
        return "validation_complete", issues

    # --- Handlers for task completion (called by main app) ---

    def on_merge_completed(self, data: Tuple[str, float]):
        """Handler for when the background merge task finishes successfully."""
        output_path, final_size_mb = data

        # Update UI status and progress bar via main app
        self.app.status_bar.set_progress(100) # Ensure progress bar hits 100%
        self.app.set_status(STATUS_MERGE_SUCCESS.format(Path(output_path).name, final_size_mb))
        self.logger.info(STATUS_MERGE_SUCCESS.format(output_path, final_size_mb))

        # Show a success message box via main app
        self.app.show_message("Merge Complete", f"PDFs merged successfully to:\n{output_path}\n\nFile size: {final_size_mb:.2f} MB", "info")

        # Reset progress bar and re-enable the merge button via main app
        self.app.clear_progress()
        # Button state re-enabled by app's task check logic

        # Ask user if they want to open the merged file (delegated to app)
        if self.app.ask_yes_no("Open File", "Merge complete. Open the merged PDF file?"):
            self.logger.info(f"User chose to open merged file: {output_path}")
            self.app.open_file_in_default_app(output_path)
        else:
            self.logger.info("User chose not to open merged file.")


    def on_validation_complete(self, issues: List[str]):
        """Handler for when the background validation task finishes."""
        # Update UI status and progress bar via main app
        self.app.clear_progress()
        # Button state re-enabled by app's task check logic

        if issues:
            # Process the structured issues to create a user-friendly summary
            issue_counts: Dict[str, int] = {}
            issue_details_list: List[str] = []

            for issue in issues:
                issue_type = issue.get("type", "unknown")
                filename = issue.get("filename", "Unknown File")
                message = issue.get("message", "No details.")

                # Count issue types
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1

                # Add brief detail for the message box (limit total details shown)
                if len(issue_details_list) < VALIDATION_REPORT_MAX_ISSUES:
                    # Customize message based on issue type for clarity
                    display_message = f"{filename}: {message}"
                    issue_details_list.append(display_message)

            # Build the summary message
            summary_lines = [f"Validation found {len(issues)} issue(s) in {len(set(i.get('filepath') for i in issues if 'filepath' in i))} file(s):\n"]
            for issue_type, count in issue_counts.items():
                summary_lines.append(f"- {count} x {issue_type.replace('_', ' ')}")

            summary_lines.append("\nDetails:")
            summary_lines.extend(issue_details_list)

            if len(issues) > VALIDATION_REPORT_MAX_ISSUES:
                 summary_lines.append(f"\n... and {len(issues) - VALIDATION_REPORT_MAX_ISSUES} more issues (see log for full details)." )

            report_message = "\n".join(summary_lines)
            title = f"Validation Found {len(issues)} Issue(s)"

            self.logger.warning(f"{title}\nFull structured report:\n{json.dumps(issues, indent=2)}") # Log full structured data
            self.app.show_message(title, report_message, "warning")
            self.app.set_status(STATUS_VALIDATION_ISSUES.format(len(issues)))
        else:
            self.app.show_message("Validation Complete", "All files appear to be valid and readable.", "info")
            self.app.set_status(STATUS_VALIDATION_COMPLETE)
            self.logger.info("File validation complete. All files OK.")