import logging
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from typing import List, Dict, Any, Optional

from ..utils.constants import LOGGER_NAME, PROFILE_LIST_KEY, STATUS_PROFILE_SAVED, STATUS_PROFILE_LOADED, STATUS_PROFILE_DELETED, APP_NAME
# We might need ConfigManager if profile storage is directly handled here,
# or it might be passed from AppCore/PDFMergerApp.

class ProfileManager:
    """Manages creation, loading, deletion, and validation of user profiles."""

    def __init__(self, app_context):
        """
        Initializes the ProfileManager.
        Args:
            app_context: The AppCore instance, providing access to ConfigManager,
                         FileListPanel, OutputPanel, MenuManager, and UI methods (show_message, etc.)
        """
        self.app_core = app_context
        self.logger = logging.getLogger(LOGGER_NAME)
        self.config_manager = self.app_core.app.config_manager # Direct access from AppCore's app reference
        self.app_root = self.app_core.app.root # For dialog parenting

    def get_profile_names(self) -> List[str]:
        """Returns a list of saved profile names."""
        return list(self.config_manager.config.get("profiles", {}).keys())

    def save_current_as_profile(self):
        """Prompts user for a profile name and saves the current list and settings."""
        if not self.app_core.get_documents():
            self.app_core.app.show_message("No Files", "Add files to the list before saving as a profile.", "info")
            return

        profile_name = simpledialog.askstring("Save Profile", "Enter a name for this profile:", parent=self.app_root)
        if not profile_name:
            return

        profile_name = profile_name.strip()
        if not profile_name:
            self.app_core.app.show_message("Invalid Name", "Profile name cannot be empty.", "warning")
            return

        if profile_name in self.get_profile_names():
            if not self.app_core.app.ask_yes_no("Overwrite Profile", f"Profile '{profile_name}' already exists. Overwrite?", parent=self.app_root):
                return

        try:
            file_list_details = self.app_core.app.file_list_panel.get_file_list_details_for_save()
            # Potentially add output settings from output_panel here too
            # output_settings = self.app_core.app.output_panel.get_output_settings_for_profile()
            # profile_data_to_save = {PROFILE_LIST_KEY: file_list_details, **output_settings}
            self.config_manager.save_profile(profile_name, file_list_details) # Modify to save complete profile_data
            self.app_core.app.show_message("Profile Saved", f"Profile '{profile_name}' saved successfully.", "info")
            self.app_core.app.set_status(STATUS_PROFILE_SAVED.format(profile_name))
            # Trigger menu update via MenuManager, which can call get_profile_names
            if hasattr(self.app_core.app, 'menu_manager'):
                 self.app_core.app.menu_manager.update_profiles_menu()
        except Exception as e:
            self.logger.error(f"Error saving profile '{profile_name}': {e}", exc_info=True)
            self.app_core.app.show_message("Profile Save Error", f"Could not save profile '{profile_name}': {e}", "error")

    def load_profile(self, profile_name: str):
        """Loads a selected profile."""
        profile_data = self.config_manager.get_profile(profile_name)
        if not profile_data:
            self.app_core.app.show_message("Error", f"Profile '{profile_name}' not found or is empty.", "error")
            return

        if self.app_core.get_documents() and not self.app_core.app.ask_yes_no("Load Profile", f"Clear current list and load profile '{profile_name}'?", parent=self.app_root):
            return

        self.app_core.clear_documents()
        # Apply output settings from profile data (TODO: OutputPanel needs apply_settings_from_profile)
        # self.app_core.app.output_panel.apply_settings_from_profile(profile_data) 

        file_details_from_profile = profile_data.get(PROFILE_LIST_KEY, [])
        if not file_details_from_profile:
            self.app_core.app.show_message("No Files in Profile", f"Profile '{profile_name}' has no files.", "info")
            self.app_core.app.set_status(f"Profile '{profile_name}' loaded (no files).")
            self.app_core.app.update_ui()
            return

        # Use AppCore's FileOperations to process loading the list
        self.app_core.app.set_status_busy(f"Loading profile '{profile_name}'...", mode="indeterminate")
        # The task itself is in FileOperations, AppCore provides the start_background_task method
        self.app_core.start_background_task(self.app_core.file_ops.process_load_list_task, args=(file_details_from_profile,))
        self.app_core.app.set_status(STATUS_PROFILE_LOADED.format(profile_name)) # Set status after task initiation

    def delete_profile_dialog(self):
        """Opens a dialog to select and delete a profile."""
        profiles = self.get_profile_names()
        if not profiles:
            self.app_core.app.show_message("No Profiles", "There are no profiles to delete.", "info")
            return

        dialog = tk.Toplevel(self.app_root)
        dialog.title("Delete Profile")
        # ... (rest of dialog setup from pdf_merger_app.py) ...
        ttk.Label(dialog, text="Select profile to delete:").pack(pady=5)
        profile_var = tk.StringVar()
        profile_combo = ttk.Combobox(dialog, textvariable=profile_var, values=profiles, state="readonly")
        if profiles: profile_combo.current(0)
        profile_combo.pack(pady=5, padx=10, fill=tk.X)

        def do_delete():
            name_to_delete = profile_var.get().strip()
            if not name_to_delete:
                self.app_core.app.show_message("No Selection", "Please select a profile.", "warning", parent=dialog)
                return
            if self.app_core.app.ask_yes_no("Confirm Delete", f"Delete profile '{name_to_delete}'?", parent=dialog):
                try:
                    if self.config_manager.delete_profile(name_to_delete):
                        self.app_core.app.show_message("Success", f"Profile '{name_to_delete}' deleted.", "info", parent=self.app_root)
                        self.app_core.app.set_status(STATUS_PROFILE_DELETED.format(name_to_delete))
                        if hasattr(self.app_core.app, 'menu_manager'):
                            self.app_core.app.menu_manager.update_profiles_menu()
                        dialog.destroy()
                    else:
                        self.app_core.app.show_message("Error", f"Could not find profile '{name_to_delete}'.", "error", parent=dialog)
                except Exception as e:
                    self.logger.error(f"Error deleting profile '{name_to_delete}': {e}", exc_info=True)
                    self.app_core.app.show_message("Deletion Error", f"Error: {e}", "error", parent=dialog)
        
        btn_frame = ttk.Frame(dialog); btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Delete", command=do_delete).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        dialog.transient(self.app_root)
        dialog.grab_set()
        # Centering logic can be added here if desired 