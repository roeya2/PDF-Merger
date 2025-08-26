import os
import sys
import logging
import shutil
import tempfile
import zipfile
import time
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import tkinterdnd2 as tkdnd

# PDF processing libraries - use centralized imports
from ..utils.common_imports import pymupdf, PdfWriter, PdfReader, RARFILE_AVAILABLE

from ..utils.constants import (
    LOGGER_NAME, STATUS_READY, STATUS_NO_FILES, STATUS_FILES_LOADED,
    STATUS_ADDED_FILES, STATUS_NO_VALID_ADDED, STATUS_REMOVED_FILES,
    STATUS_LIST_CLEARED, STATUS_EXTRACTION_STARTING, STATUS_ARCHIVE_PROCESSED_NO_PDFS,
    VALIDATION_REPORT_MAX_ISSUES, TASK_QUEUE_CHECK_INTERVAL
)
from .pdf_document import PDFDocument
from ..utils.file_operations import FileOperations
from ..managers.profile_manager import ProfileManager


class AppCore:
    """Core application logic for document management, background tasks, and file operations."""
    
    def __init__(self, app):
        """Initialize with reference to main app instance."""
        self.app = app
        self.logger = logging.getLogger(LOGGER_NAME)
        self.file_ops = FileOperations(self)
        self.profile_manager = ProfileManager(self)
    
    # --- Document Management ---
    
    def get_documents(self) -> List[PDFDocument]:
        """Provides access to the central list of PDFDocument objects."""
        return self.app.pdf_documents

    def add_documents_from_details(self, new_docs_data: List[Dict]):
        """Adds new PDFDocument objects to the central list from task details."""
        if not new_docs_data:
            self.logger.debug("No document details provided to add_documents_from_details.")
            self.app.set_status(STATUS_NO_VALID_ADDED)
            self.app.update_ui()
            return

        self.logger.info(f"Adding {len(new_docs_data)} documents to central list.")
        added_count = 0
        for data in new_docs_data:
            resolved_path_str = str(Path(data['filepath']).resolve())
            if any(doc.filepath == resolved_path_str for doc in self.app.pdf_documents):
                self.logger.info(f"Skipping duplicate file already in list: {resolved_path_str}")
                continue

            try:
                doc = PDFDocument(data['filepath'])
                doc.selected_pages = data.get('selected_pages', list(range(doc.page_count)))
                self.app.pdf_documents.append(doc)
                added_count += 1
            except Exception as e:
                self.logger.error(f"Error adding document to central list from details {data['filepath']}: {e}", exc_info=True)

        self.logger.info(f"Added {added_count} new documents to the central list. Total: {len(self.app.pdf_documents)}")
        if added_count > 0:
            self.app.set_status(STATUS_ADDED_FILES.format(added_count))
        else:
            self.app.set_status(STATUS_NO_VALID_ADDED)
        self.app.update_ui()

    def remove_documents_by_index(self, indices_to_remove: List[int]):
        """Removes documents from the central list by their original indices."""
        if not indices_to_remove: 
            return

        removed_filenames = []
        current_preview_idx = self.app.preview_doc_index.get()
        preview_doc_removed = False

        # Sort indices in reverse order to remove from the end first
        indices_to_remove_sorted = sorted(indices_to_remove, reverse=True)

        for idx in indices_to_remove_sorted:
            if 0 <= idx < len(self.app.pdf_documents):
                doc_to_remove = self.app.pdf_documents.pop(idx)
                removed_filenames.append(doc_to_remove.filename)
                doc_to_remove.close_document()
                self.logger.debug(f"Removed '{doc_to_remove.filename}' (original index {idx}).")

                if idx == current_preview_idx:
                    preview_doc_removed = True
                elif idx < current_preview_idx:
                    current_preview_idx -= 1

            else:
                self.logger.warning(f"Attempted to remove item with invalid index {idx}.")

        if removed_filenames:
            self.logger.info(f"Removed {len(removed_filenames)} files: {', '.join(removed_filenames)}")
            self.app.set_status(STATUS_REMOVED_FILES.format(len(removed_filenames)))

            if preview_doc_removed or not self.app.pdf_documents:
                self.set_preview_document(-1)
                self.app.preview_current_page.set(0)
                self.logger.debug("Preview cleared due to removed item or empty list.")
            else:
                new_preview_idx = max(-1, current_preview_idx)
                if new_preview_idx != self.app.preview_doc_index.get():
                    self.set_preview_document(new_preview_idx)
                    self.logger.debug(f"Preview index adjusted to {new_preview_idx}.")

            self.app.update_ui()

    def clear_documents(self):
        """Clears all documents from the central list."""
        if not self.app.pdf_documents:
            self.logger.debug("File list is already empty when clear requested.")
            return

        # Close all document handles before clearing the list
        for doc in self.app.pdf_documents:
            doc.close_document()
        self.app.pdf_documents = []

        # Clear any active preview
        self.set_preview_document(-1)
        self.app.preview_current_page.set(0)
        self.logger.debug("Preview cleared after clearing all files.")

        self.app.update_ui()
        self.app.set_status(STATUS_LIST_CLEARED)

    def move_document(self, current_idx: int, direction: int):
        """Moves a document in the central list and updates the UI."""
        if not (0 <= current_idx < len(self.app.pdf_documents)):
            self.logger.error(f"Attempted to move item with invalid index {current_idx}.")
            return

        new_idx = current_idx + direction

        if 0 <= new_idx < len(self.app.pdf_documents):
            doc_filename = self.app.pdf_documents[current_idx].filename
            self.logger.info(f"Moving '{doc_filename}' from index {current_idx} to {new_idx}.")

            # Perform the move in the central list
            doc = self.app.pdf_documents.pop(current_idx)
            self.app.pdf_documents.insert(new_idx, doc)

            # Update preview index if needed
            current_preview_idx = self.app.preview_doc_index.get()
            if current_preview_idx == current_idx:
                self.set_preview_document(new_idx)
                self.logger.debug(f"Preview index updated from {current_idx} to {new_idx}.")
            elif current_preview_idx == new_idx:
                self.set_preview_document(current_idx)
                self.logger.debug(f"Preview index updated from {new_idx} to {current_idx} (due to insertion).")

            self.app.update_ui()

            # Find and select the item in its new position
            new_item_iid_to_select = None
            for child_iid in self.app.file_list_panel.file_tree.get_children():
                try:
                    if int(self.app.file_list_panel.file_tree.item(child_iid, "tags")[0]) == new_idx:
                        new_item_iid_to_select = child_iid
                        break
                except (ValueError, IndexError): 
                    continue

            if new_item_iid_to_select:
                self.app.file_list_panel.file_tree.selection_set(new_item_iid_to_select)
                self.app.file_list_panel.file_tree.focus(new_item_iid_to_select)
                self.app.file_list_panel.file_tree.see(new_item_iid_to_select)

        else:
            self.logger.debug(f"Move item action: target index {new_idx} is out of bounds.")

    # --- Preview Management ---
    
    def request_preview_document(self, doc_index: int, page_num: int = 0):
        """Requests the PreviewPanel to load a preview for a specific document/page."""
        self.logger.debug(f"App requested preview for doc index {doc_index}, page {page_num + 1}.")
        self.app.preview_doc_index.set(doc_index)
        self.app.preview_current_page.set(page_num)
        self.app.preview_panel.load_document_preview(doc_index, page_num)

    def set_preview_document(self, doc_index: int):
        """Sets the index of the document currently selected for preview."""
        if self.app.preview_doc_index.get() != doc_index:
            self.logger.debug(f"App setting preview document index to {doc_index}.")
            self.app.preview_doc_index.set(doc_index)
            self.app.preview_current_page.set(0)
        elif doc_index == -1:
            self.logger.debug("App setting preview document index to -1 (already -1). Updating UI.")
            self.app.preview_doc_index.set(-1)
            self.app.preview_current_page.set(0)
            self.app.preview_panel.load_preview()

    # --- Background Task Management ---
    
    def start_background_task(self, target, args=(), kwargs=None):
        """Starts a new background task via the app's task manager."""
        return self.app.background_task.start(target, args, kwargs)

    def queue_task_result(self, result: Tuple[str, Any]):
        """Allows background tasks to queue results for the main thread."""
        self.app.task_queue.put(result)

    def check_task_queue(self):
        """Periodically checks the background task queue for results."""
        try:
            while not self.app.task_queue.empty():
                status, result = self.app.task_queue.get_nowait()
                self.logger.debug(f"Processing task queue result: status={status}, result_type={type(result)}")

                if status == "success":
                    self._handle_task_success(result)
                elif status == "error":
                    self._handle_task_error(result)

                # Reset busy state if task is no longer running
                if not self.app.background_task.is_running():
                    self.app.status_bar.clear_progress()
                    self.app.update_ui()

        except Exception as e:
            self.logger.error(f"Error processing task queue: {e}", exc_info=True)
            self.app.status_bar.set_status("Internal UI error processing task results.")
            if not self.app.background_task.is_running():
                self.app.action_panel.merge_button.config(state=tk.NORMAL if self.app.pdf_documents else tk.DISABLED)

        finally:
            self.app.root.after(TASK_QUEUE_CHECK_INTERVAL, self.check_task_queue)

    def _handle_task_success(self, result):
        """Handle successful task results."""
        if isinstance(result, tuple) and len(result) >= 1:
            action = result[0]
            data = result[1] if len(result) > 1 else None
            self.logger.debug(f"Task success action: {action}, data type: {type(data)}")

            if action == "files_added":
                if isinstance(data, tuple) and len(data) == 3:
                    new_docs_data, problematic_files, temp_dir_to_clean_path_str = data
                    self.add_documents_from_details(new_docs_data)

                    # Clean up temporary directory
                    if temp_dir_to_clean_path_str:
                        temp_dir_path = Path(temp_dir_to_clean_path_str)
                        if temp_dir_path.exists():
                            try:
                                # Determine if this is a conversion or extraction directory
                                is_conversion_dir = "wordconv" in temp_dir_path.name
                                is_extraction_dir = "extract" in temp_dir_path.name
                                
                                if is_conversion_dir:
                                    self.logger.info(f"Cleaning up temporary Word conversion directory: {temp_dir_path}")
                                elif is_extraction_dir:
                                    self.logger.info(f"Cleaning up temporary extraction directory: {temp_dir_path}")
                                else:
                                    self.logger.info(f"Cleaning up temporary directory: {temp_dir_path}")
                                
                                # Actually clean up the directory
                                shutil.rmtree(temp_dir_path, ignore_errors=True)
                                
                                # Remove from tracking lists after successful cleanup
                                if is_conversion_dir and temp_dir_path in self.app.temp_conversion_dirs:
                                    self.app.temp_conversion_dirs.remove(temp_dir_path)
                                elif is_extraction_dir and temp_dir_path in self.app.temp_extraction_dirs:
                                    self.app.temp_extraction_dirs.remove(temp_dir_path)
                                    
                            except Exception as e_clean:
                                self.logger.error(f"Failed to remove temporary directory {temp_dir_path}: {e_clean}", exc_info=True)

                    # Report problematic files
                    if problematic_files:
                        problem_summary = "\n".join([f"- {os.path.basename(p)}: {reason}" for p, reason in problematic_files[:VALIDATION_REPORT_MAX_ISSUES]])
                        if len(problematic_files) > VALIDATION_REPORT_MAX_ISSUES:
                            problem_summary += f"\n... and {len(problematic_files) - VALIDATION_REPORT_MAX_ISSUES} more."
                        self.app.show_message("Issues Adding Files",
                                            f"The following file(s) could not be added due to issues:\n\n{problem_summary}",
                                            "warning")

            elif action == "archive_extracted":
                self._on_archive_extracted(data)
            elif action == "merge_complete":
                self.app.action_panel.on_merge_completed(data)
            elif action == "validation_complete":
                self.app.action_panel.on_validation_complete(issues=data)
            elif action == "preview_generated":
                self.app.preview_panel.on_preview_generated(data)
            elif action == "progress_update":
                if isinstance(data, tuple) and len(data) == 2:
                    message, value = data
                    self.app.status_bar.set_status(message)
                    if self.app.status_bar.progress_bar.cget('mode') == 'determinate':
                        self.app.status_bar.set_progress(value)
                else:
                    self.logger.warning(f"Received malformed progress_update data: {data}")
            else:
                self.logger.warning(f"Received unhandled success action '{action}' from background task.")

        else:
            self.logger.warning(f"Received malformed success result from background task: {result}")
            self.app.status_bar.set_status("Background task completed with unexpected result.")

    def _handle_task_error(self, result):
        """Handle task error results."""
        if isinstance(result, tuple) and len(result) == 2:
            error_type, error_message = result
            self.logger.error(f"Background task reported error type '{error_type}': {error_message}")

            # Display user-friendly message based on error type
            if error_type == "runtime_error":
                self.app.show_message("Operation Failed", f"A critical error occurred during the operation:\n\n{error_message}", "error")
            elif error_type == "value_error":
                self.app.show_message("Operation Issue", f"A configuration or input issue prevented the operation:\n\n{error_message}", "warning")
            elif error_type == "generic_exception":
                self.app.show_message("Unexpected Error", f"An unexpected error occurred:\n\n{error_message}\n\nPlease check logs for details.", "error")
            elif error_type == "merge_failed":
                if isinstance(error_message, dict):
                    failure_details = error_message
                    message = failure_details.get("message", "No details available.")
                    output_file = failure_details.get("output_file", "[Unknown File]")
                    display_message = f"Merge operation failed.\nOutput file: {output_file}\n\nDetails: {message}"
                    self.app.show_message("Merge Failed", display_message, "error")
                else:
                    self.logger.warning(f"Received malformed 'merge_failed' data: {error_message}")
                    self.app.show_message("Merge Failed", "The merge operation failed with unexpected error details.\nPlease check logs for details.", "error")
            else:
                self.app.show_message("Background Task Error", f"An operation failed with an unrecognized error type:\n\n{error_message}", "error")

            # Update status bar
            status_snippet = error_message.split('\n')[0][:80] if isinstance(error_message, str) else str(error_message)[:80]
            self.app.status_bar.set_status(f"Error: {status_snippet}...")

        else:
            self.logger.error(f"Received malformed error result from background task: {result}")
            self.app.show_message("Background Task Error", "An unexpected error occurred while processing task results.\nPlease check logs for details.", "error")
            self.app.status_bar.set_status("Error processing task results.")

    def _on_archive_extracted(self, data: Optional[Tuple[List[str], Optional[str]]]):
        """Handler for when the archive extraction task completes."""
        self.app.status_bar.clear_progress()
        if data is None:
            self.logger.error("Archive extraction completed with None data.")
            self.app.show_message("Extraction Error", "An unexpected error occurred during archive extraction.", "error")
            self.app.update_ui()
            return

        extracted_pdfs, temp_dir_path_str = data
        if temp_dir_path_str:
            temp_dir_path = Path(temp_dir_path_str)
            if temp_dir_path.exists() and temp_dir_path not in self.app.temp_extraction_dirs:
                self.app.temp_extraction_dirs.append(temp_dir_path)
                self.logger.info(f"Tracking temporary extraction directory: {temp_dir_path}")

        if extracted_pdfs:
            self.logger.info(f"Adding {len(extracted_pdfs)} extracted PDFs to the list.")
            self.app.set_status_busy(f"Adding {len(extracted_pdfs)} extracted files...", mode="indeterminate")
            # Call the task processing method now located in FileOperations
            self.start_background_task(self.file_ops.process_add_files_task, args=(extracted_pdfs, temp_dir_path_str))
        else:
            self.logger.info("Archive extracted, but no valid PDF files were found.")
            self.app.show_message("No PDFs Found", "No valid PDF files were found in the selected archive.", "info")
            self.app.set_status(STATUS_ARCHIVE_PROCESSED_NO_PDFS)
            self.app.update_ui()

    # --- File Operations (delegated to FileOperations) ---

    def request_add_files(self, file_paths: List[str]):
        self.file_ops.request_add_files(file_paths)

    def request_add_folder(self, folder_path: str):
        self.file_ops.request_add_folder(folder_path)

    def request_add_from_archive(self, archive_path: str):
        self.file_ops.request_add_from_archive(archive_path)

    def request_paste_files(self):
        self.file_ops.request_paste_files()

    def handle_drop(self, event):
        self.file_ops.handle_drop(event)
    
    # Internal task processing methods are called by FileOperations, so they need to be accessible
    # or FileOperations needs a way to register them. For now, keep them here if FileOps calls them.
    # OR, if FileOperations defines them, AppCore calls file_ops.process_..._task

    def _process_add_files_task(self, file_paths: List[str], temp_dir_to_clean_path_str: Optional[str] = None):
        return self.file_ops.process_add_files_task(file_paths, temp_dir_to_clean_path_str)

    def _process_load_list_task(self, file_details: List[Dict]):
        return self.file_ops.process_load_list_task(file_details)

    def _process_extract_from_archive_task(self, archive_path: str):
        return self.file_ops.process_extract_from_archive_task(archive_path)

    # --- Profile Operations (DELEGATED to ProfileManager) ---
    def save_current_as_profile(self):
        """Delegates saving the current list and settings as a profile."""
        self.logger.debug("AppCore: Delegating save_current_as_profile to ProfileManager.")
        self.profile_manager.save_current_as_profile()

    def load_profile(self, profile_name: str):
        """Delegates loading a selected profile."""
        self.logger.debug(f"AppCore: Delegating load_profile '{profile_name}' to ProfileManager.")
        self.profile_manager.load_profile(profile_name)

    def delete_profile_dialog(self):
        """Delegates opening the delete profile dialog."""
        self.logger.debug("AppCore: Delegating delete_profile_dialog to ProfileManager.")
        self.profile_manager.delete_profile_dialog()

    # _update_profiles_menu is primarily a UI concern handled by MenuManager,
    # but ProfileManager might provide the list of names.
    # MenuManager can call app_core.profile_manager.get_profile_names()

    # ... (other AppCore methods like background task handling, preview management, etc.) 