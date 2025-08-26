import logging
import tkinter as tk
from typing import Dict, Callable, Optional

from ..utils.constants import LOGGER_NAME


class KeyboardManager:
    """Manages application-wide keyboard shortcuts and key bindings."""
    
    def __init__(self, app):
        """Initialize with reference to main app instance."""
        self.app = app
        self.root = app.root
        self.logger = logging.getLogger(LOGGER_NAME)
        
        # Dictionary to store registered shortcuts for reference
        self.shortcuts: Dict[str, Callable] = {}
        
    def setup_keyboard_shortcuts(self):
        """Sets up all application-wide keyboard shortcuts."""
        self.logger.debug("Setting up keyboard shortcuts.")
        
        # File operations
        self.register_shortcut("<Control-o>", self._add_files, "Add PDF Files")
        self.register_shortcut("<Control-s>", self._save_file_list, "Save File List")
        self.register_shortcut("<Control-l>", self._load_file_list, "Load File List")
        
        # Edit operations
        self.register_shortcut("<Control-v>", self._paste_files, "Paste Files")
        self.register_shortcut("<Delete>", self._remove_selected, "Remove Selected")
        
        # Move operations
        self.register_shortcut("<Alt-Up>", self._move_item_up, "Move Up")
        self.register_shortcut("<Alt-Down>", self._move_item_down, "Move Down")
        
        # Action operations
        self.register_shortcut("<Control-m>", self._start_merge, "Start Merge")
        
        # UI operations
        self.register_shortcut("<F5>", self._refresh_ui, "Refresh UI")
        self.register_shortcut("<Escape>", self._escape_handler, "Cancel/Clear Focus")
        
        # Development/Debug shortcuts (can be removed in production)
        self.register_shortcut("<F12>", self._debug_info, "Show Debug Info")
        
        self.logger.info(f"Registered {len(self.shortcuts)} keyboard shortcuts.")

    def register_shortcut(self, key_sequence: str, callback: Callable, description: str = ""):
        """
        Registers a keyboard shortcut.
        
        Args:
            key_sequence: Tkinter key sequence (e.g., "<Control-o>")
            callback: Function to call when shortcut is triggered
            description: Human-readable description of the shortcut
        """
        try:
            # Wrap callback to handle event parameter
            wrapped_callback = lambda event: callback()
            
            # Bind to root window
            self.root.bind(key_sequence, wrapped_callback)
            
            # Store for reference
            self.shortcuts[key_sequence] = {
                'callback': callback,
                'description': description,
                'enabled': True
            }
            
            self.logger.debug(f"Registered shortcut: {key_sequence} -> {description}")
            
        except Exception as e:
            self.logger.error(f"Failed to register shortcut {key_sequence}: {e}")

    def unregister_shortcut(self, key_sequence: str):
        """
        Unregisters a keyboard shortcut.
        
        Args:
            key_sequence: Tkinter key sequence to unregister
        """
        try:
            self.root.unbind(key_sequence)
            if key_sequence in self.shortcuts:
                del self.shortcuts[key_sequence]
            self.logger.debug(f"Unregistered shortcut: {key_sequence}")
        except Exception as e:
            self.logger.error(f"Failed to unregister shortcut {key_sequence}: {e}")

    def enable_shortcut(self, key_sequence: str):
        """
        Enables a previously disabled shortcut.
        
        Args:
            key_sequence: Tkinter key sequence to enable
        """
        if key_sequence in self.shortcuts:
            shortcut_info = self.shortcuts[key_sequence]
            if not shortcut_info['enabled']:
                wrapped_callback = lambda event: shortcut_info['callback']()
                self.root.bind(key_sequence, wrapped_callback)
                shortcut_info['enabled'] = True
                self.logger.debug(f"Enabled shortcut: {key_sequence}")

    def disable_shortcut(self, key_sequence: str):
        """
        Temporarily disables a shortcut without unregistering it.
        
        Args:
            key_sequence: Tkinter key sequence to disable
        """
        if key_sequence in self.shortcuts:
            self.root.unbind(key_sequence)
            self.shortcuts[key_sequence]['enabled'] = False
            self.logger.debug(f"Disabled shortcut: {key_sequence}")

    def get_shortcuts_info(self) -> Dict[str, Dict]:
        """
        Returns information about all registered shortcuts.
        
        Returns:
            Dictionary with shortcut info
        """
        return self.shortcuts.copy()

    # --- Shortcut Handler Methods ---
    # These methods delegate to the appropriate components
    
    def _add_files(self):
        """Handler for Ctrl+O - Add Files."""
        try:
            if hasattr(self.app, 'file_list_panel'):
                self.app.file_list_panel._add_files()
        except Exception as e:
            self.logger.error(f"Error in add files shortcut handler: {e}")

    def _save_file_list(self):
        """Handler for Ctrl+S - Save File List."""
        try:
            self.app._save_file_list()
        except Exception as e:
            self.logger.error(f"Error in save file list shortcut handler: {e}")

    def _load_file_list(self):
        """Handler for Ctrl+L - Load File List."""
        try:
            self.app._load_file_list()
        except Exception as e:
            self.logger.error(f"Error in load file list shortcut handler: {e}")

    def _paste_files(self):
        """Handler for Ctrl+V - Paste Files."""
        try:
            if hasattr(self.app, 'file_list_panel'):
                self.app.file_list_panel._paste_files()
        except Exception as e:
            self.logger.error(f"Error in paste files shortcut handler: {e}")

    def _remove_selected(self):
        """Handler for Delete - Remove Selected."""
        try:
            if hasattr(self.app, 'file_list_panel'):
                self.app.file_list_panel._remove_selected()
        except Exception as e:
            self.logger.error(f"Error in remove selected shortcut handler: {e}")

    def _move_item_up(self):
        """Handler for Alt+Up - Move Item Up."""
        try:
            if hasattr(self.app, 'file_list_panel'):
                self.app.file_list_panel._move_item(-1)
        except Exception as e:
            self.logger.error(f"Error in move item up shortcut handler: {e}")

    def _move_item_down(self):
        """Handler for Alt+Down - Move Item Down."""
        try:
            if hasattr(self.app, 'file_list_panel'):
                self.app.file_list_panel._move_item(1)
        except Exception as e:
            self.logger.error(f"Error in move item down shortcut handler: {e}")

    def _start_merge(self):
        """Handler for Ctrl+M - Start Merge."""
        try:
            if hasattr(self.app, 'action_panel'):
                self.app.action_panel._start_merge_process()
        except Exception as e:
            self.logger.error(f"Error in start merge shortcut handler: {e}")

    def _refresh_ui(self):
        """Handler for F5 - Refresh UI."""
        try:
            self.app.update_ui()
        except Exception as e:
            self.logger.error(f"Error in refresh UI shortcut handler: {e}")

    def _escape_handler(self):
        """Handler for Escape - Cancel/Clear Focus."""
        try:
            # Clear focus from any focused widget
            focused_widget = self.root.focus_get()
            if focused_widget:
                self.root.focus_set()
                
            # Clear any selection in file list if it exists
            if (hasattr(self.app, 'file_list_panel') and 
                hasattr(self.app.file_list_panel, 'file_tree')):
                self.app.file_list_panel.file_tree.selection_remove(
                    self.app.file_list_panel.file_tree.selection()
                )
                
        except Exception as e:
            self.logger.error(f"Error in escape handler: {e}")

    def _debug_info(self):
        """Handler for F12 - Show Debug Info (development only)."""
        try:
            # This is a development helper - can be removed in production
            info = []
            info.append("=== Document List ===")
            info.append(f"Documents loaded: {len(self.app.app_core.get_documents())}")
            info.append(f"Current preview doc: {self.app.preview_doc_index.get()}")
            info.append(f"Current preview page: {self.app.preview_current_page.get()}")
            info.append("")
            
            debug_message = "\n".join(info)
            self.app.show_message("Debug Info", debug_message, "info")
            
        except Exception as e:
            self.logger.error(f"Error in debug info handler: {e}")

    def bind_widget_shortcuts(self, widget: tk.Widget, shortcuts: Dict[str, Callable]):
        """
        Binds shortcuts to a specific widget.
        
        Args:
            widget: The widget to bind shortcuts to
            shortcuts: Dictionary of key_sequence -> callback mappings
        """
        for key_sequence, callback in shortcuts.items():
            try:
                widget.bind(key_sequence, lambda event, cb=callback: cb())
                self.logger.debug(f"Bound widget shortcut: {key_sequence} to {widget}")
            except Exception as e:
                self.logger.error(f"Failed to bind widget shortcut {key_sequence}: {e}")

    def setup_context_sensitive_shortcuts(self):
        """
        Sets up shortcuts that change based on context (e.g., when certain panels have focus).
        This is a placeholder for future enhancement.
        """
        # Placeholder for context-sensitive shortcut management
        # Could be implemented to enable/disable certain shortcuts based on:
        # - Which panel has focus
        # - Current application state
        # - Whether certain dialogs are open
        pass 
