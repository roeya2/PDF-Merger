import logging
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, Tuple

from app.constants import (
    APP_NAME, APP_VERSION, LOGGER_NAME, MAIN_FRAME_PADDING, HEADER_BOTTOM_PADDING,
    LOWER_FRAME_TOP_PADDING, FILE_LIST_RIGHT_PADDING, PREVIEW_LEFT_PADDING,
    OUTPUT_PANEL_RIGHT_PADDING, ACTION_PANEL_LEFT_PADDING, STATUS_BAR_TOP_PADDING,
    SEARCH_LABEL_RIGHT_PADDING, VERSION_LABEL_LEFT_PADDING, VERSION_LABEL_TOP_PADDING,
    VERSION_LABEL_COLOR, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT
)
from app.tooltip import Tooltip
from app.status_bar import StatusBar
from app.output_panel import OutputPanel
from app.action_panel import ActionPanel
from app.preview_panel import PreviewPanel
from app.file_list_panel import FileListPanel


class LayoutManager:
    """Manages UI layout creation, panel initialization, and window geometry."""
    
    def __init__(self, app):
        """Initialize with reference to main app instance."""
        self.app = app
        self.root = app.root
        self.logger = logging.getLogger(LOGGER_NAME)
        
        # References to created UI components
        self.main_frame: Optional[ttk.Frame] = None
        self.header_frame: Optional[ttk.Frame] = None
        self.lower_frame: Optional[ttk.Frame] = None
        
        # Store references for geometry management
        self._saved_geometry: Optional[str] = None
        self._saved_sash_positions: Dict[str, Any] = {}

    def setup_window_geometry(self, saved_geometry: Optional[str] = None, 
                             saved_sash_positions: Optional[Dict[str, Any]] = None):
        """
        Sets up initial window geometry and stores saved state for later application.
        
        Args:
            saved_geometry: Previously saved window geometry string
            saved_sash_positions: Previously saved sash positions
        """
        self._saved_geometry = saved_geometry
        self._saved_sash_positions = saved_sash_positions or {}
        
        self.apply_window_geometry()

    def apply_window_geometry(self):
        """Applies window geometry and sets minimum size."""
        if self._saved_geometry:
            try:
                self.root.geometry(self._saved_geometry)
                self.logger.debug(f"Applied saved window geometry: {self._saved_geometry}")
            except tk.TclError:
                self.logger.warning(f"Invalid saved window geometry: '{self._saved_geometry}'. Using default.")
                self._apply_default_geometry()
        else:
            self._apply_default_geometry()

        # Set minimum window size
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

    def _apply_default_geometry(self):
        """Applies default window geometry."""
        default_geometry = f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}"
        self.root.geometry(default_geometry)
        self.logger.debug(f"Applied default window geometry: {default_geometry}")

    def apply_saved_sash_positions(self):
        """Applies sash positions loaded from configuration to paned windows."""
        if not hasattr(self.app, 'upper_panedwindow') or not self.app.upper_panedwindow.winfo_exists():
            self.logger.debug("Upper paned window not available for sash position application.")
            return
            
        sash_positions = self._saved_sash_positions.get('upper_panedwindow')
        if sash_positions and isinstance(sash_positions, (list, tuple)) and len(sash_positions) > 0:
            try:
                # panedwindow.sashpos(index, position)
                self.app.upper_panedwindow.sashpos(0, sash_positions[0])
                self.logger.debug(f"Applied saved sash position: {sash_positions[0]}")
            except tk.TclError as e:
                self.logger.warning(f"Failed to apply saved sash positions {sash_positions}: {e}")
            except IndexError:
                self.logger.warning(f"Saved sash positions {sash_positions} has unexpected format.")
        elif sash_positions:
            self.logger.warning(f"Saved sash positions {sash_positions} has unexpected format. Expected list/tuple.")

        # Clear the stored positions after attempting to apply
        self._saved_sash_positions = {}

    def get_current_window_state(self) -> Tuple[str, Dict[str, Any]]:
        """
        Gets the current window geometry and sash positions.
        
        Returns:
            Tuple of (geometry_string, sash_positions_dict)
        """
        try:
            geometry = self.root.geometry()
            sash_positions = {
                'upper_panedwindow': (
                    self.app.upper_panedwindow.sashpos() 
                    if hasattr(self.app, 'upper_panedwindow') and self.app.upper_panedwindow.winfo_exists() 
                    else ()
                )
            }
            return geometry, sash_positions
        except Exception as e:
            self.logger.warning(f"Failed to get current window state: {e}")
            return "", {}

    def center_window(self, width: Optional[int] = None, height: Optional[int] = None):
        """
        Centers the window on the screen.
        
        Args:
            width: Window width (uses current if not specified)
            height: Window height (uses current if not specified)
        """
        try:
            # Get screen dimensions
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Use provided dimensions or current window size
            if width is None or height is None:
                self.root.update_idletasks()  # Ensure geometry is updated
                current_width = self.root.winfo_width()
                current_height = self.root.winfo_height()
                width = width or current_width
                height = height or current_height
            
            # Calculate centered position
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            
            # Apply geometry
            self.root.geometry(f"{width}x{height}+{x}+{y}")
            self.logger.debug(f"Centered window at {width}x{height}+{x}+{y}")
            
        except Exception as e:
            self.logger.error(f"Failed to center window: {e}")

    def create_panels(self):
        """Creates and lays out the application's UI panels."""
        self.logger.debug("Creating UI panels.")
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding=MAIN_FRAME_PADDING)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create all panel sections
        self._create_header_frame()
        self._create_main_paned_window()
        self._create_lower_frame()
        self._create_status_bar()

        self.logger.debug("UI panels created.")

    def _create_header_frame(self):
        """Creates the header frame with title and search."""
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, HEADER_BOTTOM_PADDING))
        
        # Title and version
        ttk.Label(self.header_frame, text=APP_NAME, style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Label(
            self.header_frame, 
            text=f"v{APP_VERSION}", 
            foreground=VERSION_LABEL_COLOR
        ).pack(side=tk.LEFT, padx=VERSION_LABEL_LEFT_PADDING, pady=(VERSION_LABEL_TOP_PADDING, 0))
        
        # Search frame
        search_frame = ttk.Frame(self.header_frame)
        search_frame.pack(side=tk.RIGHT)
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, SEARCH_LABEL_RIGHT_PADDING))
        search_entry = ttk.Entry(search_frame, textvariable=self.app.search_term, width=20)
        search_entry.pack(side=tk.LEFT)
        Tooltip(search_entry, "Filter files in the list by filename. Type to search.")

    def _create_main_paned_window(self):
        """Creates the main paned window with file list and preview panels."""
        self.app.upper_panedwindow = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.app.upper_panedwindow.pack(fill=tk.BOTH, expand=True)

        # File List Panel Container and Instance
        files_frame_container = ttk.Frame(self.app.upper_panedwindow, width=450)
        self.app.file_list_panel = FileListPanel(files_frame_container, self.app, self.app.search_term)
        self.app.file_list_panel.pack(fill=tk.BOTH, expand=True, padx=(0, FILE_LIST_RIGHT_PADDING))
        self.app.upper_panedwindow.add(files_frame_container, weight=1)

        # Preview Panel Container and Instance
        preview_frame_container = ttk.Frame(self.app.upper_panedwindow, width=550)
        self.app.preview_panel = PreviewPanel(
            preview_frame_container, self.app,
            self.app.preview_doc_index, self.app.preview_current_page, self.app.preview_max_pages,
            self.app.preview_current_zoom_display_factor, self.app.preview_is_fit_to_window
        )
        self.app.preview_panel.pack(fill=tk.BOTH, expand=True, padx=(PREVIEW_LEFT_PADDING, 0))
        self.app.upper_panedwindow.add(preview_frame_container, weight=1)

    def _create_lower_frame(self):
        """Creates the lower frame with output options and action panels."""
        self.lower_frame = ttk.Frame(self.main_frame, padding=(0, LOWER_FRAME_TOP_PADDING, 0, 0))
        self.lower_frame.pack(fill=tk.X, pady=(LOWER_FRAME_TOP_PADDING, 0))

        # Output Options Panel Instance
        self.app.output_panel = OutputPanel(
            self.lower_frame, self.app.config_manager,
            self.app.output_path, self.app.compression_level, self.app.preserve_bookmarks,
            self.app.output_password_protect, self.app.output_password,
            self.app.output_color_mode, self.app.output_dpi
        )
        self.app.output_panel.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, OUTPUT_PANEL_RIGHT_PADDING))

        # Action Panel Instance
        self.app.action_panel = ActionPanel(self.lower_frame, self.app)
        self.app.action_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(ACTION_PANEL_LEFT_PADDING, 0))

    def _create_status_bar(self):
        """Creates the status bar at the bottom."""
        self.app.status_bar = StatusBar(self.main_frame, self.app.status_text, self.app.progress_value)
        self.app.status_bar.pack(fill=tk.X, pady=(STATUS_BAR_TOP_PADDING, 0), side=tk.BOTTOM)

    def update_layout(self):
        """Updates the layout after changes (if needed)."""
        try:
            if self.main_frame and self.main_frame.winfo_exists():
                self.main_frame.update_idletasks()
            self.logger.debug("Layout updated.")
        except Exception as e:
            self.logger.error(f"Error updating layout: {e}")

    def destroy_panels(self):
        """Cleans up and destroys all panels (called during app shutdown)."""
        try:
            # This would be called during application shutdown if needed
            # For now, just log the action
            self.logger.debug("Layout manager cleanup requested.")
        except Exception as e:
            self.logger.error(f"Error during layout cleanup: {e}")

    def get_panel_references(self) -> Dict[str, Any]:
        """
        Returns references to all created panels for external access.
        
        Returns:
            Dictionary containing panel references
        """
        return {
            'main_frame': self.main_frame,
            'header_frame': self.header_frame,
            'lower_frame': self.lower_frame,
            'file_list_panel': getattr(self.app, 'file_list_panel', None),
            'preview_panel': getattr(self.app, 'preview_panel', None),
            'output_panel': getattr(self.app, 'output_panel', None),
            'action_panel': getattr(self.app, 'action_panel', None),
            'status_bar': getattr(self.app, 'status_bar', None),
        } 