import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import font as tkfont
import tkinter.simpledialog # Needed for askstring dialog
import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from app.constants import (
    LOGGER_NAME, APP_VERSION, PROFILE_LIST_KEY, PDF_FILETYPE, ALL_FILES_FILETYPE,
    ZIP_FILETYPE, RAR_FILETYPE, ARCHIVE_FILETYPES, 
    DOCX_FILETYPE, DOC_FILETYPE, WORD_FILETYPES,
    EPUB_FILETYPE, EBOOK_FILETYPES,
    STATUS_ADDED_FILES,
    STATUS_NO_VALID_ADDED, STATUS_FILE_LIST_SAVED, STATUS_FILE_LIST_LOADED,
    STATUS_PROFILE_SAVED, STATUS_PROFILE_LOADED, STATUS_PROFILE_DELETED,
    VALIDATION_REPORT_MAX_ISSUES, STATUS_VALIDATION_ISSUES, STATUS_VALIDATION_COMPLETE
)
from app.tooltip import Tooltip
from app.pdf_document import PDFDocument
from app.config_manager import ConfigManager
# BackgroundTask is used by the main app to *start* tasks, not directly by panel methods

# Check RARFILE_AVAILABLE status from centralized imports
from app.common_imports import RARFILE_AVAILABLE

class FileListPanel(ttk.LabelFrame):
    """Represents the PDF Files list section of the UI."""
    def __init__(self, parent, app, search_term_var: tk.StringVar, **kwargs):
        super().__init__(parent, text="PDF Files", padding=5, **kwargs)
        self.logger = logging.getLogger(LOGGER_NAME)
        self.app = app # Reference to the main Application class

        self.search_term = search_term_var

        self._create_widgets()
        self._bind_events()
        self.logger.debug("FileListPanel initialized.")

    def _create_widgets(self):
        """Creates the widgets within the file list panel."""
        Tooltip(self, "List of PDF files to be merged. Double-click a file to preview its content.")

        # File Tools (Add, Remove, Move, Page Range)
        file_tools_frame = ttk.Frame(self)
        file_tools_frame.pack(fill=tk.X, pady=(0, 5))

        self.add_files_button = ttk.Button(file_tools_frame, text="Add Files", command=self.app.app_core.file_ops.add_files)
        self.add_files_button.pack(side=tk.LEFT, padx=1)
        Tooltip(self.add_files_button, "Add PDF files, Word documents (.docx, .doc), and EPUB e-books (.epub) to the list (Ctrl+O).")

        self.add_folder_button = ttk.Button(file_tools_frame, text="Add Folder", command=self.app.app_core.file_ops.add_folder)
        self.add_folder_button.pack(side=tk.LEFT, padx=1)
        Tooltip(self.add_folder_button, "Add all PDF files, Word documents, and EPUB e-books from a selected folder.")

        self.remove_button = ttk.Button(file_tools_frame, text="Remove", command=self._remove_selected)
        self.remove_button.pack(side=tk.LEFT, padx=1)
        Tooltip(self.remove_button, "Remove selected file(s) from the list (Delete key).")

        self.page_range_button = ttk.Button(file_tools_frame, text="Set Page Range...", command=self._configure_page_ranges_dialog_for_selected, state=tk.DISABLED)
        self.page_range_button.pack(side=tk.LEFT, padx=1)
        Tooltip(self.page_range_button, "Set specific pages to include from the selected PDF. Only active if one file is selected.")

        # Move buttons on the right
        self.move_down_button = ttk.Button(file_tools_frame, text="↓", width=3, command=lambda: self._move_item(1))
        self.move_down_button.pack(side=tk.RIGHT, padx=1)
        Tooltip(self.move_down_button, "Move selected file down in the list (Alt+Down).")

        self.move_up_button = ttk.Button(file_tools_frame, text="↑", width=3, command=lambda: self._move_item(-1))
        self.move_up_button.pack(side=tk.RIGHT, padx=1)
        Tooltip(self.move_up_button, "Move selected file up in the list (Alt+Up).")

        # File Treeview and Scrollbars
        file_container = ttk.Frame(self)
        file_container.pack(fill=tk.BOTH, expand=True)
        self.file_tree = ttk.Treeview(file_container, columns=("Pages", "Size", "Range"), selectmode="extended", show="headings tree")
        self.file_tree.heading("#0", text="Filename")
        self.file_tree.heading("Pages", text="Pages")
        self.file_tree.heading("Size", text="Size")
        self.file_tree.heading("Range", text="Page Range")
        self.file_tree.column("#0", width=250, stretch=tk.YES)
        self.file_tree.column("Pages", width=60, anchor="center", stretch=tk.NO)
        self.file_tree.column("Size", width=80, anchor="center", stretch=tk.NO)
        self.file_tree.column("Range", width=100, anchor="center", stretch=tk.NO)

        file_vscroll = ttk.Scrollbar(file_container, orient="vertical", command=self.file_tree.yview)
        file_hscroll = ttk.Scrollbar(file_container, orient="horizontal", command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=file_vscroll.set, xscrollcommand=file_hscroll.set)
        file_vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        file_hscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        Tooltip(self.file_tree, "Displays added PDF files, Word documents, and EPUB e-books. Word and EPUB files are automatically converted to PDF during merging. Columns: Filename, Total Pages, File Size, Selected Page Range for merging.\\nDrag & drop files or folders here. Double-click to preview.")


    def _bind_events(self):
        """Binds events for widgets in the file list panel."""
        self.file_tree.bind("<Double-1>", self._on_file_tree_double_click)
        self.file_tree.bind("<Return>", self._on_file_tree_double_click) # Bind Enter key to preview
        self.file_tree.bind("<<TreeviewSelect>>", lambda *_: self._on_file_tree_select()) # Use lambda to ignore args
        # Keyboard shortcuts like Delete, Alt+Up/Down are handled by the main app binding to methods here

        # Bind trace for search term variable change
        self.search_term.trace_add("write", lambda *_: self._filter_file_list())


    # --- Public methods called by the main application or other panels ---

    def update_ui_state(self):
        """Updates UI elements based on the current list state."""
        selected_items = self.file_tree.selection()
        # Enable "Set Page Range" only if exactly one item is selected
        self.page_range_button.config(state=tk.NORMAL if len(selected_items) == 1 else tk.DISABLED)
        # Move buttons could also be disabled if only one item exists or selection is at start/end
        pdf_documents = self.app.app_core.get_documents()
        can_move_up = False
        can_move_down = False
        if len(selected_items) == 1:
            try:
                current_idx = int(self.file_tree.item(selected_items[0], "tags")[0])
                if current_idx > 0:
                    can_move_up = True
                if current_idx < len(pdf_documents) - 1:
                    can_move_down = True
            except (ValueError, IndexError, tk.TclError):
                pass # Item tag invalid

        self.move_up_button.config(state=tk.NORMAL if can_move_up else tk.DISABLED)
        self.move_down_button.config(state=tk.NORMAL if can_move_down else tk.DISABLED)


    def update_file_list_display(self):
        """Refreshes the Treeview display with the current contents of the document list."""
        self.logger.debug("Updating file list display (Treeview).")
        # Store paths of selected items to restore selection after refresh
        # Need to handle potential IndexErrors if the selected item's tag is invalid or list is empty
        selected_file_paths = set()
        pdf_documents = self.app.app_core.get_documents()
        if pdf_documents: # Only try to get selected paths if there are documents
            for item_id in self.file_tree.selection():
                if self.file_tree.exists(item_id):
                    try:
                        doc_index = int(self.file_tree.item(item_id, "tags")[0])
                        if 0 <= doc_index < len(pdf_documents):
                            selected_file_paths.add(pdf_documents[doc_index].filepath)
                    except (ValueError, IndexError, tk.TclError):
                        self.logger.warning(f"Could not get valid document index from tree item tag: {item_id}")


        self.file_tree.delete(*self.file_tree.get_children()) # Clear current items

        search_query = self.search_term.get().lower()
        items_added_to_tree = 0
        # Map original document index to the new Treeview item IID for selection restoration
        new_item_iids_by_original_index: Dict[int, str] = {}
        newly_added_item_iids: List[str] = [] # To store IIDs of items that were previously selected

        for i, doc in enumerate(pdf_documents):
            # Apply filter based on search term
            if search_query and search_query not in doc.filename.lower():
                continue # Skip this item if it doesn't match the filter

            size_str = doc.get_file_size_str() # Get formatted size string

            # Format page range string
            page_range_str = "All" # Default assumes all pages
            # Check if doc.selected_pages is None or not a list before trying to process
            if doc.selected_pages is not None and isinstance(doc.selected_pages, list) and doc.page_count > 0 and (not doc.selected_pages or len(doc.selected_pages) != doc.page_count or sorted(doc.selected_pages) != list(range(doc.page_count))):
                 # Only generate complex range string if selected pages is not None and not "all pages"
                 if not doc.selected_pages:
                      page_range_str = "None"
                 else:
                    ranges = []
                    # Ensure selected pages are valid indices within the doc's page count and sorted
                    valid_selected_pages_indices = sorted([p for p in doc.selected_pages if isinstance(p, int) and 0 <= p < doc.page_count])

                    if not valid_selected_pages_indices:
                         page_range_str = "None"
                    else:
                        # Group consecutive pages into ranges (1-5)
                        start_idx = valid_selected_pages_indices[0]
                        current_idx = valid_selected_pages_indices[0]
                        for page_idx in valid_selected_pages_indices[1:]:
                            if page_idx == current_idx + 1:
                                current_idx = page_idx
                            else:
                                ranges.append(f"{start_idx+1}-{current_idx+1}" if start_idx != current_idx else str(start_idx+1))
                                start_idx = current_idx = page_idx
                        # Add the last range/single page
                        ranges.append(f"{start_idx+1}-{current_idx+1}" if start_idx != current_idx else str(start_idx+1))
                        page_range_str = ", ".join(ranges)
            # If selected_pages is None or not a list, default "All" or handle as error
            elif doc.selected_pages is None or not isinstance(doc.selected_pages, list):
                 page_range_str = "Error/None" # Indicate invalid state
                 self.logger.warning(f"Document {doc.filename} has invalid selected_pages state: {doc.selected_pages}")


            # Insert into the Treeview. Use the document's current index 'i' as a tag.
            # This tag is crucial for mapping Treeview items back to the self.app.pdf_documents list.
            item_iid = self.file_tree.insert("", "end", text=doc.filename,
                                    values=(doc.page_count, size_str, page_range_str),
                                    tags=(str(i),)) # Store the current index 'i' as a tag
            items_added_to_tree +=1
            new_item_iids_by_original_index[i] = item_iid # Map index to IID

            # If this file was previously selected (based on path), add its new IID to the list to re-select
            if doc.filepath in selected_file_paths:
                 newly_added_item_iids.append(item_iid)


        self.logger.debug(f"Rebuilt file tree with {items_added_to_tree} items (after filter). Total documents: {len(pdf_documents)}")

        # Restore previous selection based on file paths
        if newly_added_item_iids:
            self.file_tree.selection_set(newly_added_item_iids)
            # Try to set focus to the first re-selected item
            if newly_added_item_iids[0]:
                 self.file_tree.focus(newly_added_item_iids[0])
                 self.file_tree.see(newly_added_item_iids[0])
        else:
            # If nothing was re-selected, clear the selection
            self.file_tree.selection_remove(self.file_tree.selection())


        # After updating the tree and potentially changing selection, update the UI state
        self.update_ui_state()


    # --- Internal File Management Actions ---

    def _paste_files(self):
        """Requests the app to add file paths from the clipboard."""
        self.logger.info("Paste files action initiated.")
        self.app.app_core.file_ops.paste_files()


    def _remove_selected(self):
        """Removes selected files from the list."""
        self.logger.debug("Remove selected files action initiated.")
        selected_items = self.file_tree.selection()
        if not selected_items:
            self.logger.debug("No items selected for removal.")
            return

        # Get the indices of the selected items based on their tags
        # Use original index tags to map back to the app's document list
        # Ensure item still exists in the Treeview before trying to get its tag
        indices_to_remove = [
            int(self.file_tree.item(item_id, "tags")[0])
            for item_id in selected_items if self.file_tree.exists(item_id)
        ] # No need to sort here, the app method handles removal by index list

        if not indices_to_remove:
            self.logger.debug("No valid items found for removal despite selection.")
            return

        # Request the main app to remove documents by their indices
        # Passing the list of indices directly is efficient
        self.app.request_remove_documents_by_index(indices_to_remove)

        # The main app will handle updating the UI and clearing preview if necessary


    def _clear_files(self):
        """Removes all files from the list."""
        self.logger.debug("Clear all files action initiated.")
        if not self.app.app_core.get_documents():
            self.logger.debug("File list is already empty.")
            return

        if self.app.ask_yes_no("Confirm Clear", "Remove all files from the list? This cannot be undone."):
            self.logger.info("User confirmed to clear all files.")
            # Request the main app to clear the list
            self.app.request_clear_documents()
        else:
            self.logger.info("User cancelled clearing all files.")


    def _move_item(self, direction: int):
        """Requests the app to move the selected item(s) up (-1) or down (1)."""
        self.logger.debug(f"Move item action initiated: direction {direction}.")
        selected_items = self.file_tree.selection()

        if not selected_items:
            self.logger.debug("No item selected to move.")
            return
        if len(selected_items) != 1:
            self.app.show_message("Move Item", "Please select a single file to move.", "info")
            self.logger.debug("More than one item selected for move.")
            return

        item_id = selected_items[0]
        try:
            # Get the current index of the selected item from its tag
            current_idx = int(self.file_tree.item(item_id, "tags")[0])
        except (ValueError, IndexError, tk.TclError):
            self.logger.error(f"Could not determine current index for selected item '{item_id}' to move.")
            return

        # Request the main app to move the document at this index
        self.app.request_move_document(current_idx, direction)

        # The main app will handle updating the list and re-selecting the item


    def _filter_file_list(self):
        """Triggers a refresh of the list display based on the current search term."""
        self.logger.debug(f"Filtering file list with search term: '{self.search_term.get()}'")
        self.update_file_list_display() # Rebuilds the list applying the filter


    def _on_file_tree_double_click(self, event=None):
        """Handles a double-click event on the Treeview to show a file preview."""
        # Get the item that was double-clicked - event.widget is the treeview
        # event.x, event.y are relative to the treeview
        try:
            item_id = self.file_tree.identify_row(event.y)
            if not item_id or item_id not in self.file_tree.selection():
                 self.logger.debug("Double-click did not land on a selected item.")
                 return # Ignore double-clicks outside selected items or on headers etc.
        except tk.TclError:
             self.logger.warning("TclError identifying treeview row from double-click event.")
             return # Handle cases where identify_row might fail

        try:
            # Get the document index from the Treeview item's tag
            doc_idx = int(self.file_tree.item(item_id, "tags")[0])
            # Request the main app to load the preview for this document (page 0)
            self.app.request_preview_document(doc_idx, page_num=0) # Start preview from page 0

        except (IndexError, ValueError, tk.TclError) as e:
            self.logger.error(f"Error getting document index for preview from double-click event on item '{item_id}': {e}")
            self.app.set_preview_document(-1) # Ensure preview state is cleared


    def _on_file_tree_select(self):
        """Handles selection changes in the Treeview."""
        # This handler is primarily used to update the state of the "Set Page Range" and Move buttons
        self.update_ui_state()

        # Optional: Automatically load preview on single-click selection?
        # The current behavior (double-click to preview) is preserved.
        # If single-click preview is desired, the logic from _on_file_tree_double_click
        # would be moved here, or call a dedicated method.


    def _configure_page_ranges_dialog_for_selected(self):
        """Opens the page range configuration dialog for the currently selected document."""
        selected_items = self.file_tree.selection()
        if not selected_items or len(selected_items) != 1:
             self.app.show_message("Select File", "Please select exactly one file from the list to configure its page range.", "info")
             return

        item_id = selected_items[0]
        try:
            # Get the document index from the Treeview item's tag
            doc_idx = int(self.file_tree.item(item_id, "tags")[0])
            pdf_documents = self.app.app_core.get_documents() # Get latest documents list
            if 0 <= doc_idx < len(pdf_documents):
                doc = pdf_documents[doc_idx]
                self.logger.info(f"Opening configure page range dialog for '{doc.filename}'.")
                # Open the page range dialog for this specific document instance
                self._open_page_range_dialog(doc)
            else:
                self.logger.error(f"Invalid document index {doc_idx} from tree tag for item {item_id} when trying to configure page range.")
                self.app.show_message("Error", "Could not identify the selected document.", "error")
        except (IndexError, ValueError, tk.TclError) as e:
            self.logger.error(f"Could not get document for page range dialog from item {item_id}: {e}")
            self.app.show_message("Error", "Could not identify the selected document.", "error")


    def _open_page_range_dialog(self, doc: PDFDocument):
        """Creates and displays the page range configuration dialog."""
        dialog = tk.Toplevel(self.app.root) # Parent dialog to the main app root
        dialog.title(f"Page Range for {doc.filename}")
        dialog.transient(self.app.root)
        dialog.grab_set()
        # Calculate position to center it relative to the root window
        root_x = self.app.root.winfo_x()
        root_y = self.app.root.winfo_y()
        root_width = self.app.root.winfo_width()
        root_height = self.app.root.winfo_height()
        dialog_width = 400
        dialog_height = 200
        dialog.geometry(f"{dialog_width}x{dialog_height}+{root_x + (root_width - dialog_width) // 2}+{root_y + (root_height - dialog_height) // 2}")


        ttk.Label(dialog, text=f"Total pages: {doc.page_count}. Enter pages or ranges (e.g., 1-5, 7, 9-12):").pack(pady=5, padx=10)

        # Prepare the initial value for the entry field from the current selected pages
        current_ranges_str = ""
        if doc.selected_pages is not None and isinstance(doc.selected_pages, list) and doc.page_count > 0:
            ranges = []
            # Ensure selected pages are valid indices and sorted
            valid_selected_pages_indices = sorted([p for p in doc.selected_pages if isinstance(p, int) and 0 <= p < doc.page_count])

            if valid_selected_pages_indices:
                # Group consecutive pages into ranges (1-5)
                start_idx = valid_selected_pages_indices[0]
                current_idx = valid_selected_pages_indices[0]
                for page_idx in valid_selected_pages_indices[1:]:
                    if page_idx == current_idx + 1:
                        current_idx = page_idx
                    else:
                        ranges.append(f"{start_idx+1}-{current_idx+1}" if start_idx != current_idx else str(start_idx+1))
                        start_idx = current_idx = page_idx
                # Add the last range/single page
                ranges.append(f"{start_idx+1}-{current_idx+1}" if start_idx != current_idx else str(start_idx+1))
                current_ranges_str = ", ".join(ranges)
            # If selected_pages is [] or contains no valid indices, current_ranges_str remains ""

        range_var = tk.StringVar(value=current_ranges_str)
        range_entry = ttk.Entry(dialog, textvariable=range_var)
        range_entry.pack(pady=5, padx=10, fill=tk.X)
        range_entry.focus() # Set focus to the entry field

        status_label = ttk.Label(dialog, text="", foreground="red")
        status_label.pack(pady=2, padx=10, anchor="w")

        # Preview label to show which pages will be selected
        preview_label = ttk.Label(dialog, text="", foreground="blue", wraplength=350)
        preview_label.pack(pady=2, padx=10, anchor="w")

        def parse_page_range_string(range_str: str, max_page_count: int) -> Optional[List[int]]:
            """Helper function to parse a page range string into a list of 0-indexed page indices."""
            selected_indices = set()
            range_str = range_str.strip()

            if not range_str:
                # Empty string means select all pages (default behavior for this tool)
                return list(range(max_page_count))

            parts = range_str.split(',')
            for part in parts:
                part = part.strip()
                if not part: 
                    continue # Skip empty parts resulting from extra commas

                if '-' in part:
                    # Handle range (e.g., 1-5)
                    range_parts = part.split('-')
                    if len(range_parts) != 2:
                        status_label.config(text=f"Error: Invalid range format '{part}'. Expected start-end.", foreground="red")
                        preview_label.config(text="")
                        return None # Indicate parsing error
                    try:
                        start_page_str, end_page_str = range_parts
                        start_page = int(start_page_str)
                        end_page = int(end_page_str)
                    except ValueError:
                        status_label.config(text=f"Error: Invalid number in range '{part}'.", foreground="red")
                        preview_label.config(text="")
                        return None # Indicate parsing error

                    # Validate page numbers and range order (1-based)
                    if not (1 <= start_page <= max_page_count) or not (1 <= end_page <= max_page_count):
                        status_label.config(text=f"Error: Page number out of bounds in '{part}'. Pages are 1-{max_page_count}.", foreground="red")
                        preview_label.config(text="")
                        return None
                    if start_page > end_page:
                        status_label.config(text=f"Error: Invalid range '{part}'. Start page must be less than or equal to end page.", foreground="red")
                        preview_label.config(text="")
                        return None

                    # Add pages from the range (convert 1-based to 0-indexed)
                    selected_indices.update(range(start_page - 1, end_page)) # range is exclusive of end index

                else:
                    # Handle single page number (e.g., 7)
                    try:
                        page = int(part)
                    except ValueError:
                        status_label.config(text=f"Error: Invalid page number '{part}'.", foreground="red")
                        preview_label.config(text="")
                        return None # Indicate parsing error

                    # Validate page number (1-based)
                    if not (1 <= page <= max_page_count):
                        status_label.config(text=f"Error: Page '{part}' out of bounds. Pages are 1-{max_page_count}.", foreground="red")
                        preview_label.config(text="")
                        return None

                    selected_indices.add(page - 1)

            status_label.config(text="") # Clear any previous error message
            parsed_indices = sorted(list(selected_indices))
            
            # Show preview of selected pages
            if parsed_indices:
                if len(parsed_indices) == max_page_count:
                    preview_label.config(text="Preview: All pages selected", foreground="blue")
                elif len(parsed_indices) <= 10:
                    # Show individual pages for small selections
                    page_nums = [str(i + 1) for i in parsed_indices]
                    preview_label.config(text=f"Preview: Pages {', '.join(page_nums)} selected ({len(parsed_indices)} total)", foreground="blue")
                else:
                    # Show summary for large selections
                    preview_label.config(text=f"Preview: {len(parsed_indices)} pages selected", foreground="blue")
            else:
                preview_label.config(text="Preview: No pages selected", foreground="orange")
            
            return parsed_indices

        def validate_input(*args):
            """Real-time validation as user types."""
            current_text = range_var.get()
            parse_page_range_string(current_text, doc.page_count)

        # Bind validation to text changes
        range_var.trace_add("write", validate_input)
        
        # Initial validation
        validate_input()

        def apply_range():
            """Applies the parsed page range to the document and closes the dialog."""
            new_range_str = range_var.get()
            parsed_page_indices = parse_page_range_string(new_range_str, doc.page_count)

            if parsed_page_indices is not None: # parse_page_range_string returns None on error
                # Update the selected_pages list for the document
                old_selection_count = len(doc.selected_pages) if doc.selected_pages else 0
                doc.selected_pages = parsed_page_indices
                new_selection_count = len(parsed_page_indices)
                
                self.logger.info(f"Applied page range '{new_range_str}' (parsed as {parsed_page_indices}) to '{doc.filename}'.")

                # Update the file list display to show the new page range string
                self.update_file_list_display()
                
                # Provide user feedback
                if new_selection_count == doc.page_count:
                    feedback_msg = f"Page range updated for '{doc.filename}': All {doc.page_count} pages selected"
                else:
                    feedback_msg = f"Page range updated for '{doc.filename}': {new_selection_count} of {doc.page_count} pages selected"
                
                self.app.set_status(feedback_msg)
                self.app.show_message("Page Range Updated", feedback_msg, "info")
                
                dialog.destroy()
            else:
                # Don't close dialog if there are validation errors
                self.logger.warning(f"Could not apply invalid page range '{new_range_str}' to '{doc.filename}'.")

        def cancel_range():
            """Cancels the dialog without applying changes."""
            self.logger.info(f"Page range dialog cancelled for '{doc.filename}'.")
            dialog.destroy()

        # Button frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10, padx=10, fill=tk.X)

        # Add buttons
        apply_button = ttk.Button(button_frame, text="Apply", command=apply_range)
        apply_button.pack(side=tk.RIGHT, padx=5)
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=cancel_range)
        cancel_button.pack(side=tk.RIGHT, padx=5)
        
        # Add some helpful buttons
        select_all_button = ttk.Button(button_frame, text="Select All", 
                                     command=lambda: range_var.set(""))
        select_all_button.pack(side=tk.LEFT, padx=5)
        
        # Keyboard shortcuts
        dialog.bind('<Return>', lambda e: apply_range())
        dialog.bind('<Escape>', lambda e: cancel_range())
        
        # Make Apply button the default
        apply_button.focus()

    def get_file_list_details_for_save(self) -> List[Dict[str, Any]]:
        """
        Returns file details for saving to profiles or file lists.
        Each dict contains: filepath, filename, page_count, selected_pages
        """
        file_details = []
        
        for doc in self.app.app_core.get_documents():
            detail = {
                'filepath': doc.filepath,
                'filename': doc.filename,
                'page_count': doc.page_count,
                'selected_pages': list(doc.selected_pages) if doc.selected_pages else list(range(doc.page_count))
            }
            file_details.append(detail)
            
        self.logger.debug(f"Prepared {len(file_details)} file details for saving.")
        return file_details