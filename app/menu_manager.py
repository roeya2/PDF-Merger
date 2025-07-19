import logging
import tkinter as tk
from tkinter import ttk
from typing import Optional

from app.constants import LOGGER_NAME


class MenuManager:
    """Manages application menu bar creation and dynamic updates."""
    
    def __init__(self, app):
        """Initialize with reference to main app instance."""
        self.app = app
        self.root = app.root
        self.logger = logging.getLogger(LOGGER_NAME)
        
        # References to menus that need dynamic updates
        self.profiles_menu = None
        self.menubar = None
        
    def create_menu_bar(self):
        """Creates the complete application menu bar."""
        self.logger.debug("Creating menus.")
        self.menubar = tk.Menu(self.root)

        # Create all menu sections
        self._create_file_menu()
        self._create_edit_menu()
        self._create_profiles_menu()
        self._create_tools_menu()
        self._create_help_menu()

        # Configure the menu bar
        self.root.config(menu=self.menubar)
        self.logger.debug("Menus created and configured.")

    def _create_file_menu(self):
        """Creates the File menu."""
        file_menu = tk.Menu(self.menubar, tearoff=0)
        
        # Delegate menu actions to the appropriate panel methods
        file_menu.add_command(
            label="Add PDF Files...",
            command=self.app.app_core.file_ops.add_files,
            accelerator="Ctrl+O"
        )
        file_menu.add_command(
            label="Add Folder...",
            command=self.app.app_core.file_ops.add_folder
        )
        file_menu.add_command(
            label="Add from Archive (ZIP, RAR)...",
            command=self.app.app_core.file_ops.add_from_archive
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Save File List...", 
            command=self.app._save_file_list, 
            accelerator="Ctrl+S"
        )
        file_menu.add_command(
            label="Load File List...", 
            command=self.app._load_file_list, 
            accelerator="Ctrl+L"
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.app._on_closing)
        
        self.menubar.add_cascade(label="File", menu=file_menu)

    def _create_edit_menu(self):
        """Creates the Edit menu."""
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        
        edit_menu.add_command(
            label="Clear All", 
            command=self.app.file_list_panel._clear_files
        )
        edit_menu.add_command(
            label="Remove Selected", 
            command=self.app.file_list_panel._remove_selected, 
            accelerator="Delete"
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label="Move Up", 
            command=lambda: self.app.file_list_panel._move_item(-1), 
            accelerator="Alt+Up"
        )
        edit_menu.add_command(
            label="Move Down", 
            command=lambda: self.app.file_list_panel._move_item(1), 
            accelerator="Alt+Down"
        )
        
        self.menubar.add_cascade(label="Edit", menu=edit_menu)

    def _create_profiles_menu(self):
        """Creates the Profiles menu with dynamic profile list."""
        self.profiles_menu = tk.Menu(self.menubar, tearoff=0)
        
        self.profiles_menu.add_command(
            label="Save Current as Profile...", 
            command=self.app._save_current_as_profile
        )
        
        # Populate dynamic profile list
        self.update_profiles_menu()
        
        self.menubar.add_cascade(label="Profiles", menu=self.profiles_menu)

    def _create_tools_menu(self):
        """Creates the Tools menu."""
        tools_menu = tk.Menu(self.menubar, tearoff=0)
        
        tools_menu.add_command(
            label="Edit Metadata...", 
            command=self.app._edit_metadata_dialog, 
            state=tk.DISABLED  # Placeholder
        )
        tools_menu.add_command(
            label="Page Range Settings...", 
            command=self.app.file_list_panel._configure_page_ranges_dialog_for_selected
        )
        tools_menu.add_separator()
        tools_menu.add_command(
            label="Preferences...", 
            command=self.app._show_preferences_dialog, 
            state=tk.DISABLED  # Placeholder
        )
        
        self.menubar.add_cascade(label="Tools", menu=tools_menu)

    def _create_help_menu(self):
        """Creates the Help menu."""
        help_menu = tk.Menu(self.menubar, tearoff=0)
        
        help_menu.add_command(label="Help", command=self.app._show_help_dialog)
        help_menu.add_command(label="About", command=self.app._show_about_dialog)
        help_menu.add_command(
            label="Check for Updates...", 
            command=self.app._check_updates, 
            state=tk.DISABLED  # Placeholder
        )
        
        self.menubar.add_cascade(label="Help", menu=help_menu)

    def update_profiles_menu(self):
        """Updates the dynamic list of profiles in the Profiles menu."""
        self.logger.debug("Updating profiles menu.")
        
        if not self.profiles_menu:
            self.logger.warning("Profiles menu not initialized.")
            return
            
        menu = self.profiles_menu

        # Clear existing dynamic profile entries
        try:
            save_index = -1
            for i in range(menu.index(tk.END) + 1):
                try:
                    if (menu.type(i) == 'command' and 
                        menu.entrycget(i, 'label') == 'Save Current as Profile...'):
                        save_index = i
                        break
                except tk.TclError:
                    pass # Item might have been deleted or is a separator

            if save_index != -1:
                # Delete everything after "Save Current as Profile..."
                # This includes separators and old profile entries
                # menu.index(tk.END) can be None if menu is empty after save_index
                end_idx = menu.index(tk.END)
                if end_idx is not None and end_idx > save_index:
                    menu.delete(save_index + 1, tk.END)
            else:
                # Fallback: If "Save Current..." isn't found (should not happen with correct init),
                # attempt to clear all but the first item, assuming it might be "Save Current..."
                self.logger.warning("'Save Current as Profile...' command not found in Profiles menu during update.")
                end_idx = menu.index(tk.END)
                if end_idx is not None and end_idx >= 0: # Check if there's at least one item
                     # Be cautious, only delete if there are items beyond a potential first one.
                     if end_idx > 0: # If there are items after the first one
                        menu.delete(1, tk.END)
                     # If only one item and it wasn't "Save Current...", this doesn't clear, which is safer.

        except tk.TclError as e:
            self.logger.error(f"Error clearing profiles menu: {e}", exc_info=True)
            # As a last resort, try to delete all entries if the menu is in an unexpected state
            # This is risky as it might delete "Save Current as Profile..."
            # A better approach might be to rebuild the menu from scratch if this occurs.
            # For now, just log and proceed, potentially leaving old entries or a messy menu.

        # Get profile names from ProfileManager via AppCore
        profile_names = []
        if hasattr(self.app, 'app_core') and hasattr(self.app.app_core, 'profile_manager'):
            profile_names = self.app.app_core.profile_manager.get_profile_names()
        else:
            self.logger.error("ProfileManager not accessible via app.app_core.profile_manager to update profiles menu.")

        if profile_names:
            menu.add_separator()
            for name in sorted(profile_names):
                menu.add_command(
                    label=name, 
                    command=lambda n=name: self.app._load_profile(n)
                )
            menu.add_separator()
            menu.add_command(
                label="Delete Profile...", 
                command=self.app._delete_profile_dialog
            )
        else:
            # Ensure no "Delete Profile..." or separators if no profiles exist
            # The clearing logic above should handle this, but as a safeguard:
            # Check if the last item is "Delete Profile..." or a separator and remove if no profiles.
            # This is complex due to menu indices. The current clearing should suffice.
            pass
            
    def _find_menu_item_index(self, menu_widget: tk.Menu, item_label: str) -> Optional[int]:
        """
        Finds the index of a menu item with the given label in the menu widget.
        
        Args:
            menu_widget: The menu widget to search within
            item_label: The label of the menu item to find
        
        Returns:
            The index of the menu item if found, or None if not found
        """
        try:
            for i in range(menu_widget.index(tk.END) + 1):
                if (menu_widget.type(i) == 'command' and 
                    menu_widget.entrycget(i, 'label') == item_label):
                    return i
        except tk.TclError:
            return None

    def enable_menu_item(self, menu_path: str, item_label: str):
        """
        Enables a menu item.
        
        Args:
            menu_path: Path to the menu (e.g., "Tools")
            item_label: Label of the menu item to enable
        """
        try:
            # This is a placeholder for future implementation
            # Would need to track menu references for dynamic enabling/disabling
            self.logger.debug(f"Enable menu item requested: {menu_path} -> {item_label}")
        except Exception as e:
            self.logger.warning(f"Failed to enable menu item {menu_path} -> {item_label}: {e}")

    def disable_menu_item(self, menu_path: str, item_label: str):
        """
        Disables a menu item.
        
        Args:
            menu_path: Path to the menu (e.g., "Tools")
            item_label: Label of the menu item to disable
        """
        try:
            # This is a placeholder for future implementation
            # Would need to track menu references for dynamic enabling/disabling
            self.logger.debug(f"Disable menu item requested: {menu_path} -> {item_label}")
        except Exception as e:
            self.logger.warning(f"Failed to disable menu item {menu_path} -> {item_label}: {e}") 