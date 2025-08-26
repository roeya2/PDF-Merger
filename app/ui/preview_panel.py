import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, Tuple, Optional
import tkinter.simpledialog # Needed for potential future features? Not currently used.

# Core dependencies
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
import tkinterdnd2 as tkdnd

from ..utils.constants import (
    LOGGER_NAME, MIN_ZOOM, MAX_ZOOM, ZOOM_STEP_FACTOR, CANVAS_RESIZE_DELAY,
    PREVIEW_LOAD_DELAY, PREVIEW_NO_DOC_MSG, PREVIEW_NO_FILES_MSG,
    PREVIEW_LOADING_MSG, PREVIEW_NO_PAGES_MSG, PREVIEW_ERROR_MSG,
    PREVIEW_IMAGE_ERROR_MSG, PREVIEW_NO_PREVIEW_MSG
)
from .tooltip import Tooltip # Assuming Tooltip is in its own file
from ..core.pdf_document import PDFDocument # Assuming PDFDocument is in its own file
from ..core.background_task import BackgroundTask # Assuming BackgroundTask is in its own file


class PreviewPanel(ttk.LabelFrame):
    """Represents the Preview section of the UI."""
    def __init__(self, parent, app, preview_doc_index_var: tk.IntVar, preview_current_page_var: tk.IntVar, preview_max_pages_var: tk.IntVar, preview_current_zoom_factor_var: tk.DoubleVar, preview_is_fit_var: tk.BooleanVar, **kwargs):
        super().__init__(parent, text="Preview", padding=5, style="Preview.TFrame", **kwargs)
        self.logger = logging.getLogger(LOGGER_NAME)
        self.app = app # Reference to the main Application class

        self.preview_doc_index = preview_doc_index_var # Index in app's pdf_documents list
        self.preview_current_page = preview_current_page_var # 0-indexed page in current doc
        self.preview_max_pages = preview_max_pages_var # Max page index (page_count - 1)

        self.preview_current_zoom_display_factor = preview_current_zoom_factor_var # The actual zoom factor used
        self.preview_is_fit_to_window = preview_is_fit_var # BooleanVar

        self._resize_job: Optional[str] = None # To debounce canvas resize
        self._panning = False # Panning state
        self._pan_start_x, self._pan_start_y = 0, 0 # Pan start coordinates

        self._preview_image_tk: Optional[tk.PhotoImage] = None # Keep reference to the current PhotoImage

        self._create_widgets()
        self._bind_events()

        self.logger.debug("PreviewPanel initialized.")

    def _create_widgets(self):
        """Creates the widgets within the preview panel."""
        Tooltip(self, "Displays a preview of the selected page from the file list.")

        # Navigation and Zoom Controls
        preview_nav_tools = ttk.Frame(self)
        preview_nav_tools.pack(fill=tk.X, pady=(0, 2))

        self.prev_page_button = ttk.Button(preview_nav_tools, text="◀ Prev", width=7, command=self._prev_page)
        self.prev_page_button.pack(side=tk.LEFT, padx=2)
        Tooltip(self.prev_page_button, "Go to the previous page in the preview.")

        self.page_label = ttk.Label(preview_nav_tools, text="No document selected", width=20, anchor="center")
        self.page_label.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        Tooltip(self.page_label, "Shows current page number and total pages of the previewed document.")

        self.next_page_button = ttk.Button(preview_nav_tools, text="Next ▶", width=7, command=self._next_page)
        self.next_page_button.pack(side=tk.LEFT, padx=2)
        Tooltip(self.next_page_button, "Go to the next page in the preview.")

        # Zoom Controls
        zoom_controls_frame = ttk.Frame(self)
        zoom_controls_frame.pack(fill=tk.X, pady=(2,5))

        self.zoom_out_btn = ttk.Button(zoom_controls_frame, text="-", command=self._zoom_out, width=3)
        self.zoom_out_btn.pack(side=tk.LEFT, padx=(0,2))
        Tooltip(self.zoom_out_btn, f"Zoom out of the preview ({ZOOM_STEP_FACTOR}x step). Also supported via Mouse Wheel Down.")

        self.zoom_in_btn = ttk.Button(zoom_controls_frame, text="+", command=self._zoom_in, width=3)
        self.zoom_in_btn.pack(side=tk.LEFT, padx=2)
        Tooltip(self.zoom_in_btn, f"Zoom into the preview ({ZOOM_STEP_FACTOR}x step). Also supported via Mouse Wheel Up.")

        self.zoom_display_label = ttk.Label(zoom_controls_frame, text="---", width=10, anchor="center")
        self.zoom_display_label.pack(side=tk.LEFT, padx=(5,2))
        Tooltip(self.zoom_display_label, "Current zoom level or 'Fit' if fitting to window.")

        self.actual_size_btn = ttk.Button(zoom_controls_frame, text="Actual Size", command=self._zoom_actual_size)
        self.actual_size_btn.pack(side=tk.LEFT, padx=2)
        Tooltip(self.actual_size_btn, "View preview at 100% (actual size).")

        self.fit_to_window_cb = ttk.Checkbutton(zoom_controls_frame, text="Fit to Window", variable=self.preview_is_fit_to_window)
        self.fit_to_window_cb.pack(side=tk.LEFT, padx=5)
        Tooltip(self.fit_to_window_cb, "Check to automatically resize preview to fit the window. Uncheck for manual zoom control (including scroll wheel zoom and panning).")

        # Preview Canvas
        # Add scrollbars to the canvas
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.preview_canvas = tk.Canvas(canvas_frame, bg="#ffffff", highlightthickness=1, highlightbackground="gray") # Canvas background
        self.preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) # Pack canvas first

        self.canvas_vscroll = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.preview_canvas.yview)
        self.canvas_hscroll = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.preview_canvas.xview)
        self.preview_canvas.config(yscrollcommand=self.canvas_vscroll.set, xscrollcommand=self.canvas_hscroll.set)

        self.canvas_vscroll.pack(side=tk.RIGHT, fill=tk.Y) # Pack scrollbars after canvas
        self.canvas_hscroll.pack(side=tk.BOTTOM, fill=tk.X)

        Tooltip(self.preview_canvas, "Preview area. If not 'Fit to Window', use mouse wheel to zoom, click & drag to pan when zoomed. Use scrollbars to navigate.")


    def _bind_events(self):
        """Binds events for widgets in the preview panel."""
        self.preview_canvas.bind("<Configure>", self._redraw_preview_on_resize)
        self.preview_canvas.bind("<ButtonPress-1>", self._on_canvas_button_press)
        self.preview_canvas.bind("<B1-Motion>", self._on_canvas_motion)
        self.preview_canvas.bind("<ButtonRelease-1>", self._on_canvas_button_release)

        # Bind keyboard events for page navigation (Left/Right arrow keys)
        self.app.root.bind("<Left>", lambda event: self._prev_page())
        self.app.root.bind("<Right>", lambda event: self._next_page())

        # Bind mouse wheel events for zoom (cross-platform)
        self.preview_canvas.bind("<MouseWheel>", self._handle_preview_scroll_zoom, add="+") # Windows/macOS
        self.preview_canvas.bind("<Button-4>", self._handle_preview_scroll_zoom, add="+") # Linux (scroll up)
        self.preview_canvas.bind("<Button-5>", self._handle_preview_scroll_zoom, add="+") # Linux (scroll down)

        # Bind trace for 'Fit to Window' variable change
        self.preview_is_fit_to_window.trace_add("write", lambda *_: self._on_zoom_mode_change())


    # --- Public methods called by the main application or other panels ---

    def load_document_preview(self, doc_index: int, page_num: int = 0):
        """Loads a preview for a specific document and page index."""
        self.logger.debug(f"Request to load preview for doc {doc_index}, page {page_num}.")

        if 0 <= doc_index < len(self.app.app_core.get_documents()): # Check if the document still exists
            doc = self.app.app_core.get_documents()[doc_index]
            self.logger.debug(f"Preview panel: Loading preview for '{doc.filename}', page {page_num + 1}.")
            # Update the shared variables
            self.preview_doc_index.set(doc_index)
            self.preview_current_page.set(page_num)
            # load_preview() will be called next by the trace handler if index changed,
            # or needs to be called explicitly here if the index didn't change but page/settings did.
            # For now, load_preview handles clamping page number and re-loading.
            self.load_preview()
        else:
            self.logger.debug("Document index out of bounds. Load preview aborted.")


    def update_ui_state(self, total_file_count: int):
         """Updates UI elements based on overall application state."""
         # Update page label and zoom label based on current preview state
         doc_idx = self.preview_doc_index.get()
         if 0 <= doc_idx < len(self.app.app_core.get_documents()): # Check if the document still exists
            doc = self.app.app_core.get_documents()[doc_idx]
            current_page_display = self.preview_current_page.get() + 1
            # Only update page label if not currently showing "Loading..."
            if not self.page_label.cget("text").startswith("Loading"):
                 self.page_label.config(text=f"Page {current_page_display} of {doc.page_count}")

            # Update zoom display label
            if self.preview_is_fit_to_window.get():
                 actual_zoom_perc = int(self.preview_current_zoom_display_factor.get() * 100)
                 self.zoom_display_label.config(text=f"Fit ({actual_zoom_perc}%)")
            else:
                 manual_zoom_perc = int(self.preview_current_zoom_display_factor.get() * 100)
                 self.zoom_display_label.config(text=f"{manual_zoom_perc}%)")

         else:
             # No document selected for preview
             self.page_label.config(text="No document selected")
             self.zoom_display_label.config(text="---")
             # Clear canvas content if no doc is selected
             # This is also handled in load_preview if doc_index is invalid


    # --- Internal Preview Logic ---

    def load_preview(self):
        """Loads and displays the current page of the selected document in the canvas."""
        self.logger.debug("Preview panel: load_preview called.")

        # Get the current document index and page number from the app's shared variables
        current_doc_idx = self.preview_doc_index.get()
        current_page_num = self.preview_current_page.get()

        self.logger.debug(f"Preview panel: Current doc index {current_doc_idx}, page {current_page_num}.")

        # Check if a valid document is selected
        pdf_documents = self.app.app_core.get_documents() # Get list from main app
        if current_doc_idx < 0 or current_doc_idx >= len(pdf_documents):
            self.preview_canvas.delete("all") # Clear canvas
            # Draw default message if no doc selected
            canvas_width, canvas_height = self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height()
            if canvas_width > 1 and canvas_height > 1:
                text_to_show = PREVIEW_NO_DOC_MSG if len(pdf_documents) > 0 else PREVIEW_NO_FILES_MSG
                self.preview_canvas.create_text(
                    canvas_width // 2, canvas_height // 2,
                    text=text_to_show, fill="gray", font=("Segoe UI", 10)
                )
            self.page_label.config(text="No document selected")
            self.zoom_display_label.config(text="---")
            self.logger.debug("Load preview called but no valid document selected.")
            # Clear internal image reference
            self._preview_image_tk = None
            self.preview_canvas.config(scrollregion=(0,0,0,0)) # Reset scroll region
            return

        # Get the document
        doc = pdf_documents[current_doc_idx]

        # Check if the document has pages
        if doc.page_count == 0:
            self.page_label.config(text=PREVIEW_NO_PAGES_MSG)
            self.zoom_display_label.config(text="---")
            self.preview_canvas.delete("all")
            cw, ch = self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height()
            if cw > 1 and ch > 1:
                self.preview_canvas.create_text(cw // 2, ch // 2, text=PREVIEW_NO_PAGES_MSG, fill="red", font=("Segoe UI", 10))
            self._preview_image_tk = None
            self.preview_canvas.config(scrollregion=(0,0,0,0))
            self.logger.warning(f"Attempted to load preview for '{doc.filename}' but it has no pages.")
            return

        # Clamp the current page number
        page_num_to_load = max(0, min(self.preview_current_page.get(), doc.page_count - 1))
        self.preview_current_page.set(page_num_to_load) # Update the variable
        self.preview_max_pages.set(doc.page_count -1) # Update max pages variable

        self.logger.info(f"Loading preview for '{doc.filename}', page {page_num_to_load + 1}/{doc.page_count}.")
        # Update page label immediately to show loading state
        self.page_label.config(text=PREVIEW_LOADING_MSG.format(page_num_to_load + 1))
        # Force UI update to show loading text
        self.update_idletasks() # Update widgets in this panel
        self.app.root.update_idletasks() # Update main window

        # Determine canvas size for fitting or explicit zoom
        canvas_w, canvas_h = self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height()

        # If canvas size is invalid, reschedule
        if canvas_w <= 1 or canvas_h <= 1:
             self.logger.debug(f"Canvas size too small ({canvas_w}x{canvas_h}), rescheduling load_preview.")
             self.after(PREVIEW_LOAD_DELAY, self.load_preview) # Reschedule within this panel
             return

        self.logger.debug(f"Preview canvas size: {canvas_w}x{canvas_h}, fit mode: {self.preview_is_fit_to_window.get()}")

        # Determine target size and zoom mode
        zoom_factor = self.preview_current_zoom_display_factor.get()
        fit_size = (canvas_w - 20, canvas_h - 20) if self.preview_is_fit_to_window.get() else None # 20px margin
        if not self.preview_is_fit_to_window.get() and zoom_factor <= 0:
            zoom_factor = 1.0 # Default zoom if invalid

        # Start the background task to generate the preview image
        self.app.start_background_task(
            self._generate_preview_task,
            args=(current_doc_idx, page_num_to_load, zoom_factor, fit_size)
        )


    def _generate_preview_task(self, doc_idx: int, page_num: int, zoom_factor: float, fit_size: Optional[Tuple[int, int]]) -> Tuple[str, Optional[Tuple[int, int, bytes, float, bool]]]:
        """
        Background task to generate preview image data.
        Calls PDFDocument.get_preview.
        Returns ("preview_generated", (doc_idx, page_num, img_data, actual_zoom, was_fit_attempted) or None).
        """
        pdf_documents = self.app.app_core.get_documents() # Get list from main app

        # Re-check document validity in case the list changed while task was queued
        if not (0 <= doc_idx < len(pdf_documents)):
            self.logger.warning(f"Preview task: Document index {doc_idx} out of bounds during execution.")
            return "preview_generated", None

        doc = pdf_documents[doc_idx]
        if not (0 <= page_num < doc.page_count):
             self.logger.warning(f"Preview task: Page number {page_num} out of bounds for document '{doc.filename}' ({doc.page_count} pages).")
             return "preview_generated", None

        self.logger.debug(f"Preview task: Generating preview data for '{doc.filename}', page {page_num + 1}, zoom factor {zoom_factor:.2f}, fit_size {fit_size}.")

        # Call the PDFDocument method to get image data and actual zoom
        # doc.get_preview returns (img_data_bytes, actual_zoom_float) or None
        preview_result = doc.get_preview(page_num, zoom_factor=zoom_factor, fit_size=fit_size)

        if preview_result:
            img_data_bytes, actual_zoom_used = preview_result
            self.logger.debug(f"Preview task: Generated image data successfully. Actual zoom: {actual_zoom_used:.2f}")
            # Return original request params + result data
            return "preview_generated", (doc_idx, page_num, img_data_bytes, actual_zoom_used, bool(fit_size))
        else:
            self.logger.error(f"Preview task: Failed to generate preview data for '{doc.filename}', page {page_num}.")
            return "preview_generated", None


    # --- Handler for task completion (called by main app) ---

    def on_preview_generated(self, data: Optional[Tuple[int, int, bytes, float, bool]]):
        """Handler for when the background task finishes generating preview data."""
        canvas = self.preview_canvas
        # Check if the preview data is valid or indicates an error
        if data is None:
            self.logger.error("Preview generation failed in background task (data is None).")
            self.zoom_display_label.config(text=PREVIEW_ERROR_MSG)
            canvas.delete("all")
            canvas_width, canvas_height = canvas.winfo_width(), canvas.winfo_height()
            if canvas_width > 1 and canvas_height > 1:
                canvas.create_text(canvas_width//2, canvas_height//2, text=PREVIEW_ERROR_MSG, fill="red")
            self.page_label.config(text=PREVIEW_NO_PREVIEW_MSG)
            self._preview_image_tk = None
            self.preview_canvas.config(scrollregion=(0,0,0,0))
            self.app.update_ui() # Ensure status/labels update
            return

        # Unpack the data tuple
        doc_idx, page_num, img_data_bytes, actual_zoom_used, was_fit_attempted = data

        # Get document details for error reporting if needed
        doc_filename = "Unknown File"
        pdf_documents = self.app.app_core.get_documents()
        if 0 <= doc_idx < len(pdf_documents):
             doc_filename = pdf_documents[doc_idx].filename

        # Check if the generated preview is still relevant (user hasn't clicked another file/page)
        if doc_idx != self.preview_doc_index.get() or page_num != self.preview_current_page.get():
            self.logger.info("Preview generated is no longer current (doc or page changed in UI). Discarding.")
            # The PhotoImage created below won't be referenced by the UI, so Tkinter should clean it up.
            return # Do not update UI with stale data

        # Create the Tkinter PhotoImage object in the main thread
        try:
            new_preview_image_tk = tk.PhotoImage(data=img_data_bytes)
        except tk.TclError as e:
            self.logger.error(f"Error creating PhotoImage from data for doc {doc_idx}, page {page_num}: {e}", exc_info=True)
            error_text = f"Error: {PREVIEW_IMAGE_ERROR_MSG} for {doc_filename}, page {page_num + 1}"
            self.zoom_display_label.config(text="Image Error") # Shorter status
            canvas.delete("all")
            canvas_width, canvas_height = canvas.winfo_width(), canvas.winfo_height()
            if canvas_width > 1 and canvas_height > 1:
                canvas.create_text(canvas_width//2, canvas_height//2, text=error_text, fill="red", width=canvas_width * 0.8, justify=tk.CENTER) # Add filename/page, wrap text
            self.page_label.config(text=PREVIEW_NO_PREVIEW_MSG)
            self._preview_image_tk = None
            self.preview_canvas.config(scrollregion=(0,0,0,0))
            self.app.update_ui() # Ensure status/labels update
            return


        # Clear the canvas before drawing the new image
        canvas.delete("all")

        # Ensure canvas dimensions are valid before positioning the image
        canvas_width, canvas_height = canvas.winfo_width(), canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
             self.logger.debug(f"Canvas size too small ({canvas_width}x{canvas_height}) after preview generated, rescheduling handler.")
             # Reschedule this handler call with the same data
             self.after(PREVIEW_LOAD_DELAY, lambda d=data: self.on_preview_generated(d))
             return # Exit this handler instance

        # Keep a reference to the new PhotoImage object
        # Tkinter automatically cleans up the old image when the variable is reassigned
        self._preview_image_tk = new_preview_image_tk

        # Display the image centered on the canvas initially
        canvas.create_image(canvas_width // 2, canvas_height // 2, image=self._preview_image_tk, tags="pdf_image")

        # Update scrollable region of the canvas to match the image size
        img_bbox = canvas.bbox("pdf_image")
        if img_bbox:
            canvas.config(scrollregion=img_bbox)

            # Reset the canvas view (scroll position) to the top-left
            # This is needed whether fitting or not, as a new image is drawn
            canvas.xview_moveto(0)
            canvas.yview_moveto(0)


        self.logger.info(f"Preview displayed for doc index {doc_idx}, page {page_num + 1}. Actual zoom: {actual_zoom_used*100:.0f}%")

        # Update zoom display label
        if was_fit_attempted:
            self.zoom_display_label.config(text=f"Fit ({actual_zoom_used*100:.0f}%)")
        else:
            self.zoom_display_label.config(text=f"{actual_zoom_used*100:.0f}%)")

        # Store the actual zoom factor used (relevant even for fit mode)
        self.preview_current_zoom_display_factor.set(actual_zoom_used)

        # Update the page label to show the current page number again
        # Re-get doc in case list changed slightly while task was running
        pdf_documents = self.app.app_core.get_documents()
        if 0 <= doc_idx < len(pdf_documents):
             doc = pdf_documents[doc_idx]
             self.page_label.config(text=f"Page {self.preview_current_page.get() + 1} of {doc.page_count}")
        else:
             # If the doc was removed, reset label
             self.page_label.config(text="No document selected")


    # --- Internal UI Event Handlers ---

    def _on_canvas_button_press(self, event):
        """Handles mouse button press on the preview canvas for panning."""
        # Only start pan if "Fit to Window" is off and there's a preview image
        if not self.preview_is_fit_to_window.get() and self._preview_image_tk:
             # Check if the image is actually larger than the canvas (requires scrolling)
             canvas_width = self.preview_canvas.winfo_width()
             canvas_height = self.preview_canvas.winfo_height()
             img_bbox = self.preview_canvas.bbox("pdf_image") # Get bbox of the image item
             if img_bbox and (img_bbox[2] - img_bbox[0] > canvas_width or img_bbox[3] - img_bbox[1] > canvas_height):
                self.preview_canvas.scan_mark(event.x, event.y)
                self._panning = True
                # We don't need to store start_x/y for scan_dragto, but it's good practice
                # self._pan_start_x, self._pan_start_y = event.x, event.y # Store start pos
                self.preview_canvas.config(cursor="fleur") # Change cursor
                self.logger.debug("Panning started on preview canvas.")


    def _on_canvas_motion(self, event):
        """Handles mouse motion on the preview canvas during panning."""
        if self._panning:
            # Use scan_dragto to pan the canvas view
            self.preview_canvas.scan_dragto(event.x, event.y, gain=1)


    def _on_canvas_button_release(self, event):
        """Handles mouse button release on the preview canvas, ends panning."""
        if self._panning:
            self._panning = False
            self.preview_canvas.config(cursor="") # Restore default cursor
            self.logger.debug("Panning ended on preview canvas.")
            # No need to re-render or reposition, scan_dragto handles view update


    def _on_zoom_mode_change(self):
        """Handles changes to the 'Fit to Window' checkbox."""
        is_fit = self.preview_is_fit_to_window.get()
        self.logger.debug(f"Zoom mode changed. Fit to window: {is_fit}.")
        # When the mode changes, the preview needs to be re-rendered
        if self.preview_doc_index.get() != -1:
            self.load_preview() # Reload preview with the new fit setting


    def _zoom_in(self):
        """Increases the preview zoom level."""
        idx = self.preview_doc_index.get()
        if not (0 <= idx < len(self.app.app_core.get_documents())): return # No document selected

        self.logger.debug("Zoom In action initiated.")
        # Get current zoom factor, calculate new one within bounds, and set it.
        current_factor = self.preview_current_zoom_display_factor.get()
        new_factor = min(current_factor * ZOOM_STEP_FACTOR, MAX_ZOOM)
        self.preview_current_zoom_display_factor.set(new_factor)
        self.logger.debug(f"New zoom factor set to {new_factor:.2f}.")

        # If currently in Fit to Window mode, disable it. This will trigger load_preview via its trace.
        if self.preview_is_fit_to_window.get():
            self.preview_is_fit_to_window.set(False) # Trace listener calls load_preview
        else:
            # If not in Fit to Window mode, manually trigger load_preview with the new factor.
            self.load_preview()


    def _zoom_out(self):
        """Decreases the preview zoom level."""
        idx = self.preview_doc_index.get()
        if not (0 <= idx < len(self.app.app_core.get_documents())): return # No document selected

        self.logger.debug("Zoom Out action initiated.")
        # Get current zoom factor, calculate new one within bounds, and set it.
        current_factor = self.preview_current_zoom_display_factor.get()
        new_factor = max(current_factor / ZOOM_STEP_FACTOR, MIN_ZOOM)
        self.preview_current_zoom_display_factor.set(new_factor)
        self.logger.debug(f"New zoom factor set to {new_factor:.2f}.")

        # If currently in Fit to Window mode, disable it. This will trigger load_preview via its trace.
        if self.preview_is_fit_to_window.get():
            self.preview_is_fit_to_window.set(False) # Trace listener calls load_preview
        else:
            # If not in Fit to Window mode, manually trigger load_preview with the new factor.
            self.load_preview()


    def _zoom_actual_size(self):
        """Sets the preview zoom level to 100%."""
        idx = self.preview_doc_index.get()
        if not (0 <= idx < len(self.app.app_core.get_documents())): return # No document selected

        self.logger.debug("Zoom Actual Size action initiated (100%).")
        # Set the zoom factor to 100%.
        self.preview_current_zoom_display_factor.set(1.0)
        self.logger.debug("New zoom factor set to 1.00 (Actual Size).")

        # Disable fit mode first (this will trigger load_preview via trace)
        self.preview_is_fit_to_window.set(False) # Trace listener calls load_preview


    def _handle_preview_scroll_zoom(self, event):
        """Handles mouse wheel events for zooming in the preview canvas."""
        idx = self.preview_doc_index.get()
        if not (0 <= idx < len(self.app.app_core.get_documents())): return # No document selected

        # Only zoom with scroll wheel if "Fit to Window" is OFF
        if self.preview_is_fit_to_window.get():
            # Suggestion: Could implement vertical scrolling here if fit is on and page is larger than canvas height.
             self.logger.debug("Ignoring scroll zoom: 'Fit to Window' is enabled.")
             return

        self.logger.debug(f"Preview scroll zoom event: Delta={getattr(event, 'delta', 'N/A')}, Num={getattr(event, 'num', 'N/A')}")

        # Determine zoom direction
        zoom_in_direction = False
        if hasattr(event, 'delta'): # Windows/macOS MouseWheel
            if event.delta > 0: zoom_in_direction = True
        elif hasattr(event, 'num'): # Linux Button-4/5
            if event.num == 4: zoom_in_direction = True

        # Perform the zoom action
        if zoom_in_direction: self._zoom_in()
        else: self._zoom_out()


    def _redraw_preview_on_resize(self, event=None):
        """Handles canvas Configure events (resize)."""
        # Debounce resize events
        if self._resize_job:
             self.after_cancel(self._resize_job)

        # Only schedule a redraw/reload if a document is currently previewed
        if self.preview_doc_index.get() != -1:
            # If fit is active, we need to recalculate zoom and reload the preview
            if self.preview_is_fit_to_window.get():
                self.logger.debug("Resize event: 'Fit to Window' active, scheduling load_preview.")
                self._resize_job = self.after(CANVAS_RESIZE_DELAY, self.load_preview)
            # If not fitting, and an image exists, just recenter it visually and update scroll region
            elif self._preview_image_tk:
                self.logger.debug("Resize event: Not fitting, scheduling _recenter_current_preview_image.")
                self._resize_job = self.after(PREVIEW_LOAD_DELAY, self._recenter_current_preview_image)
            else:
                 # No preview image, just redraw the "No document selected" message if canvas size is valid
                 canvas_width, canvas_height = self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height()
                 if canvas_width > 1 and canvas_height > 1:
                      # This path is hit if preview_doc_index is -1 on resize, or if load_preview failed previously
                      self._resize_job = self.after(PREVIEW_LOAD_DELAY, self.load_preview) # Call load_preview to redraw message


    def _recenter_current_preview_image(self):
        """Recalculates image position to center it on the canvas after a resize."""
        canvas = self.preview_canvas
        # Check if there's a preview image to recenter
        if not self._preview_image_tk:
            self.logger.debug("Recenter called, but no preview image reference exists.")
            return

        # Get current canvas dimensions
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
             self.logger.debug(f"Recenter called, but canvas not ready ({canvas_width}x{canvas_height}).")
             return

        # Delete the old image item
        canvas.delete("pdf_image")

        # Recreate the image item centered on the canvas
        canvas.create_image(canvas_width // 2, canvas_height // 2, image=self._preview_image_tk, tags="pdf_image")
        self.logger.debug(f"Preview image recentered on canvas {canvas_width}x{canvas_height}.")

        # Update scroll region to match the image size for panning
        img_bbox = canvas.bbox("pdf_image")
        if img_bbox:
            canvas.config(scrollregion=img_bbox)
        else:
             # If image has no bbox (e.g. error), reset scrollregion
             canvas.config(scrollregion=(0,0,0,0))


    def _next_page(self):
        """Goes to the next page in the preview."""
        idx = self.preview_doc_index.get()
        pdf_documents = self.app.app_core.get_documents()

        if not (0 <= idx < len(pdf_documents)):
             self.logger.debug("Next page requested, but no document selected.")
             return

        doc = pdf_documents[idx]
        # Check if there's a next page
        if doc.page_count > 0 and self.preview_current_page.get() < doc.page_count - 1:
            # Increment page number variable
            self.preview_current_page.set(self.preview_current_page.get() + 1)
            self.logger.debug(f"Next Page: Now on page {self.preview_current_page.get() + 1} for '{doc.filename}'.")
            # Load the new preview
            self.load_preview()
        elif doc.page_count > 0:
             self.logger.debug(f"Next Page: Already on the last page ({self.preview_current_page.get() + 1}) for '{doc.filename}'.")
        else:
             self.logger.debug(f"Next Page: Document '{doc.filename}' has no pages.")


    def _prev_page(self):
        """Goes to the previous page in the preview."""
        idx = self.preview_doc_index.get()
        pdf_documents = self.app.app_core.get_documents()

        if not (0 <= idx < len(pdf_documents)):
             self.logger.debug("Prev page requested, but no document selected.")
             return

        doc = pdf_documents[idx]
        # Check if there's a previous page
        if doc.page_count > 0 and self.preview_current_page.get() > 0:
            # Decrement page number variable
            self.preview_current_page.set(self.preview_current_page.get() - 1)
            self.logger.debug(f"Prev Page: Now on page {self.preview_current_page.get() + 1} for '{doc.filename}'.")
            # Load the new preview
            self.load_preview()
        elif doc.page_count > 0:
             self.logger.debug(f"Prev Page: Already on the first page ({self.preview_current_page.get() + 1}) for '{doc.filename}'.")
        else:
             self.logger.debug(f"Prev Page: Document '{doc.filename}' has no pages.")

    def request_go_to_document(self, doc_index: int):
        """Navigates to a specific document in the list for preview."""
        if not (0 <= doc_index < len(self.app.app_core.get_documents())): return # No document selected
        self.logger.debug(f"Preview panel: Navigate to document {doc_index}.")
        self.app.request_preview_document(doc_index, 0) # Request document with first page

    def request_first_document(self):
        """Navigates to the first document in the list."""
        if len(self.app.app_core.get_documents()) == 0: return # No documents available
        self.request_go_to_document(0)

    def request_previous_document(self):
        """Navigates to the previous document in the list."""
        current_idx = self.preview_doc_index.get()
        if not (0 <= current_idx < len(self.app.app_core.get_documents())): return # No document selected
        if current_idx > 0:
            self.request_go_to_document(current_idx - 1)

    def request_next_document(self):
        """Navigates to the next document in the list."""
        current_idx = self.preview_doc_index.get()
        pdf_documents = self.app.app_core.get_documents()
        if not (0 <= current_idx < len(pdf_documents)): return # No document selected
        if current_idx < len(pdf_documents) - 1:
            self.request_go_to_document(current_idx + 1)

    def request_last_document(self):
        """Navigates to the last document in the list."""
        pdf_documents = self.app.app_core.get_documents()
        if len(pdf_documents) == 0: return # No documents available
        if pdf_documents:
            self.request_go_to_document(len(pdf_documents) - 1)
