import tkinter as tk
from tkinter import ttk
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Core dependencies
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
import tkinterdnd2 as tkdnd

from ..utils.constants import (
    LOGGER_NAME, DEFAULT_OUTPUT_FILENAME, DEFAULT_COMPRESSION, DEFAULT_PRESERVE_BOOKMARKS,
    DEFAULT_PASSWORD_PROTECT, DEFAULT_COLOR_MODE, DEFAULT_DPI, PDF_FILETYPE, ALL_FILES_FILETYPE,
    # New feature constants
    QUALITY_PRESET_DIALOG_WIDTH, QUALITY_PRESET_DIALOG_HEIGHT,
    METADATA_DIALOG_WIDTH, METADATA_DIALOG_HEIGHT,
    COMPRESSION_DIALOG_WIDTH, COMPRESSION_DIALOG_HEIGHT,
    STATUS_QUALITY_PRESET_APPLIED, STATUS_METADATA_SAVED,
    STATUS_ADVANCED_COMPRESSION_SET
)
from ..managers.config_manager import ConfigManager
from ..managers.quality_presets_manager import get_quality_presets_manager
from ..managers.metadata_manager import get_metadata_manager
from ..managers.advanced_compression_manager import get_advanced_compression_manager
from .tooltip import Tooltip

class OutputPanel(ttk.LabelFrame):
    """Represents the Output Options section of the UI."""
    def __init__(self, parent, config_manager: ConfigManager, output_path_var: tk.StringVar, compression_level_var: tk.StringVar, preserve_bookmarks_var: tk.BooleanVar, password_protect_var: tk.BooleanVar, password_var: tk.StringVar, color_mode_var: tk.StringVar, dpi_var: tk.StringVar, **kwargs):
        super().__init__(parent, text="Output Options", padding=10, **kwargs)
        self.logger = logging.getLogger(LOGGER_NAME)

        self.config_manager = config_manager
        self.output_path = output_path_var
        self.compression_level = compression_level_var
        self.preserve_bookmarks = preserve_bookmarks_var
        self.output_password_protect = password_protect_var
        self.output_password = password_var
        self.output_color_mode = color_mode_var
        self.output_dpi = dpi_var

        # Initialize managers
        self.quality_presets_manager = get_quality_presets_manager(config_manager)
        self.metadata_manager = get_metadata_manager()
        self.advanced_compression_manager = get_advanced_compression_manager()

        # Load saved metadata
        self.metadata_manager.load_from_config(config_manager)

        self._create_widgets()
        self._bind_events()
        self.toggle_password_entry_state() # Set initial state of password entry

        self.logger.debug("OutputPanel initialized.")

    def _create_widgets(self):
        """Creates the widgets within the output options panel."""
        Tooltip(self, "Settings for the final merged PDF file.")

        # Layout in two columns
        col1_frame = ttk.Frame(self)
        col1_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,10))

        # Output File Path
        path_frame = ttk.Frame(col1_frame)
        path_frame.pack(fill=tk.X, pady=2, anchor="w")
        ttk.Label(path_frame, text="Output File:").pack(side=tk.LEFT, padx=(0, 5))
        self.output_entry = ttk.Entry(path_frame, textvariable=self.output_path)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        Tooltip(self.output_entry, "Path and filename for the merged PDF file.")

        self.choose_output_btn = ttk.Button(path_frame, text="Choose...", command=self._choose_output_file)
        self.choose_output_btn.pack(side=tk.LEFT)
        Tooltip(self.choose_output_btn, "Browse to select an output file location and name.")

        # Quality Presets and Compression
        quality_frame = ttk.Frame(col1_frame)
        quality_frame.pack(fill=tk.X, pady=2, anchor="w")

        ttk.Label(quality_frame, text="Quality Preset:").pack(side=tk.LEFT, padx=(0, 5))
        preset_names = [preset.name for preset in self.quality_presets_manager.get_builtin_presets()]
        self.preset_dropdown = ttk.Combobox(quality_frame, values=preset_names, width=15, state="readonly")
        self.preset_dropdown.pack(side=tk.LEFT, padx=(0, 5))
        self.preset_dropdown.set("Normal Compression")  # Default preset name
        Tooltip(self.preset_dropdown, "Choose a quality preset optimized for your use case.")

        self.apply_preset_btn = ttk.Button(quality_frame, text="Apply", command=self._apply_quality_preset, width=6)
        self.apply_preset_btn.pack(side=tk.LEFT, padx=(0, 10))
        Tooltip(self.apply_preset_btn, "Apply the selected quality preset settings.")

        # Advanced options in a collapsible frame
        self.advanced_frame = ttk.LabelFrame(col1_frame, text="Advanced Settings", padding=5)
        self.advanced_frame.pack(fill=tk.X, pady=2, anchor="w")

        # Compression controls
        comp_frame = ttk.Frame(self.advanced_frame)
        comp_frame.pack(fill=tk.X, pady=1, anchor="w")
        ttk.Label(comp_frame, text="Compression:").pack(side=tk.LEFT, padx=(0, 5))
        comp_dropdown_values = ["none", "fast", "normal", "high", "maximum"]
        self.comp_dropdown = ttk.Combobox(comp_frame, textvariable=self.compression_level,
                                        values=comp_dropdown_values, width=10, state="readonly")
        self.comp_dropdown.pack(side=tk.LEFT, padx=(0, 5))
        self.comp_dropdown.set(self.config_manager.config.get("compression_level", DEFAULT_COMPRESSION))
        Tooltip(self.comp_dropdown, "Set compression level for the output PDF. 'None' is fastest; 'Maximum' yields smallest files.")

        self.advanced_comp_btn = ttk.Button(comp_frame, text="⚙️", width=3, command=self._open_advanced_compression_dialog)
        self.advanced_comp_btn.pack(side=tk.LEFT, padx=(0, 10))
        Tooltip(self.advanced_comp_btn, "Open advanced compression settings dialog.")

        # Metadata and Bookmarks
        meta_frame = ttk.Frame(self.advanced_frame)
        meta_frame.pack(fill=tk.X, pady=1, anchor="w")

        self.bookmark_check = ttk.Checkbutton(meta_frame, text="Preserve Bookmarks", variable=self.preserve_bookmarks)
        self.bookmark_check.pack(side=tk.LEFT, padx=(0, 10))
        Tooltip(self.bookmark_check, "If checked, bookmarks (outlines) from the source PDFs will be included in the merged file.")

        self.metadata_btn = ttk.Button(meta_frame, text="📝 Edit Metadata", command=self._open_metadata_dialog)
        self.metadata_btn.pack(side=tk.LEFT)
        Tooltip(self.metadata_btn, "Edit PDF metadata (title, author, subject, keywords).")


        col2_frame = ttk.Frame(self)
        col2_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10,0))

        # Password Protection
        pass_protect_frame = ttk.Frame(col2_frame)
        pass_protect_frame.pack(fill=tk.X, pady=2, anchor="w")
        self.pass_protect_cb = ttk.Checkbutton(pass_protect_frame, text="Protect with password:", variable=self.output_password_protect)
        self.pass_protect_cb.pack(side=tk.LEFT)
        Tooltip(self.pass_protect_cb, "Check to encrypt the output PDF with a password.")

        self.password_entry = ttk.Entry(pass_protect_frame, textvariable=self.output_password, show="*", width=15)
        self.password_entry.pack(side=tk.LEFT, padx=5)
        Tooltip(self.password_entry, "Enter the password to be used for encrypting the output PDF if 'Protect' is checked.")

        # Color Mode (Experimental)
        color_mode_frame = ttk.Frame(col2_frame)
        color_mode_frame.pack(fill=tk.X, pady=2, anchor="w")
        ttk.Label(color_mode_frame, text="Color Mode:").pack(side=tk.LEFT, padx=(0,5))
        color_modes = ["Colorful (Original)", "Grayscale (Experimental)", "B&W (Experimental)"]
        self.color_mode_combo = ttk.Combobox(color_mode_frame, textvariable=self.output_color_mode, values=color_modes, width=20, state="readonly")
        self.color_mode_combo.pack(side=tk.LEFT)
        self.color_mode_combo.set(self.config_manager.config.get("output_color_mode", DEFAULT_COLOR_MODE))
        Tooltip(self.color_mode_combo, "Select output color mode (Note: This feature requires advanced PDF processing and is not yet functional).")
        ttk.Label(color_mode_frame, text="(Experimental, not yet functional)", foreground="gray").pack(side=tk.LEFT, padx=5)


        # DPI (Experimental)
        dpi_frame = ttk.Frame(col2_frame)
        dpi_frame.pack(fill=tk.X, pady=2, anchor="w")
        ttk.Label(dpi_frame, text="DPI:").pack(side=tk.LEFT, padx=(0,5))
        dpi_options = ["Original", "72", "96", "150", "300", "600"]
        self.dpi_combo = ttk.Combobox(dpi_frame, textvariable=self.output_dpi, values=dpi_options, width=10, state="readonly")
        self.dpi_combo.pack(side=tk.LEFT)
        self.dpi_combo.set(self.config_manager.config.get("output_dpi", DEFAULT_DPI))
        Tooltip(self.dpi_combo, "Select output DPI (dots per inch) (Note: This feature requires advanced PDF processing and is not yet functional).")
        ttk.Label(dpi_frame, text="(Experimental, not yet functional)", foreground="gray").pack(side=tk.LEFT, padx=5)


    def _bind_events(self):
        """Binds events for UI elements in this panel."""
        self.output_password_protect.trace_add("write", lambda *_: self.toggle_password_entry_state())

    def toggle_password_entry_state(self):
        """Enables/disables the password entry based on the checkbox state."""
        if self.output_password_protect.get():
            self.password_entry.config(state=tk.NORMAL)
        else:
            self.password_entry.config(state=tk.DISABLED)
            self.output_password.set("") # Clear password when protection is disabled

    def _choose_output_file(self):
        """Opens a save file dialog for the output PDF."""
        self.logger.debug("Choose output file dialog initiated.")
        current_output_path = self.output_path.get()
        initial_dir = os.path.dirname(current_output_path) or self.config_manager.config.get("default_output_dir", str(Path.home()))
        initial_file = os.path.basename(current_output_path) or DEFAULT_OUTPUT_FILENAME

        path = filedialog.asksaveasfilename(
            title="Save Merged PDF As",
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".pdf",
            filetypes=[PDF_FILETYPE, ALL_FILES_FILETYPE],
            parent=self # Parent should be the main window or top-level, but self works for basic dialogs
        )
        if path:
            self.output_path.set(path)
            try:
                 # Save the directory as the default output directory
                 self.config_manager.config["default_output_dir"] = os.path.dirname(path)
                 # config_manager.save_config() # Config save happens on app close now
            except Exception as e:
                 self.logger.warning(f"Failed to set default output directory {os.path.dirname(path)}: {e}")

            self.logger.info(f"Output file set to: {path}")
            # Update status bar - This should be done by the main app class or a shared status object
            # self.status_text.set(f"Output file set to: {os.path.basename(path)}") # Removed direct status update


    def get_output_settings(self) -> Dict[str, Any]:
        """Retrieves the current output settings from the UI."""
        settings = {
            "output_path": self.output_path.get().strip(),
            "compression_level": self.compression_level.get(),
            "preserve_bookmarks": self.preserve_bookmarks.get(),
            "password_protect": self.output_password_protect.get(),
            "password": self.output_password.get(), # Get password only when needed
            "color_mode": self.output_color_mode.get(),
            "dpi": self.output_dpi.get()
        }
        self.logger.debug(f"Retrieved output settings: {settings}")
        return settings

    def apply_settings_from_profile(self, profile_data: Dict[str, Any]):
        """Applies relevant settings from a loaded profile."""
        self.compression_level.set(profile_data.get("compression_level", DEFAULT_COMPRESSION))
        self.preserve_bookmarks.set(profile_data.get("preserve_bookmarks", DEFAULT_PRESERVE_BOOKMARKS))
        self.output_password_protect.set(profile_data.get("output_password_protect", DEFAULT_PASSWORD_PROTECT))
        self.output_color_mode.set(profile_data.get("output_color_mode", DEFAULT_COLOR_MODE))
        self.output_dpi.set(profile_data.get("output_dpi", DEFAULT_DPI))
        # Do NOT set password from profile data
        self.toggle_password_entry_state() # Ensure password entry state is correct

        self.logger.debug(f"Applied settings from profile.")

    def _apply_quality_preset(self):
        """Apply the selected quality preset."""
        selected_name = self.preset_dropdown.get()
        if not selected_name:
            return

        # Find preset by name
        selected_preset = None
        for preset in self.quality_presets_manager.get_builtin_presets():
            if preset.name == selected_name:
                selected_preset = preset
                break

        if not selected_preset:
            self.logger.warning(f"Quality preset not found: {selected_name}")
            return

        # Apply preset settings
        preset_settings = selected_preset.get_settings()

        # Update UI variables
        self.compression_level.set(preset_settings.get('compression', DEFAULT_COMPRESSION))
        self.output_color_mode.set(preset_settings.get('color_mode', DEFAULT_COLOR_MODE))
        self.output_dpi.set(preset_settings.get('dpi', DEFAULT_DPI))
        self.preserve_bookmarks.set(preset_settings.get('preserve_bookmarks', DEFAULT_PRESERVE_BOOKMARKS))

        self.logger.info(f"Applied quality preset '{selected_preset.name}'")
        # Update status if available
        if hasattr(self, 'status_text'):
            self.status_text.set(STATUS_QUALITY_PRESET_APPLIED.format(selected_preset.name))

    def _open_advanced_compression_dialog(self):
        """Open the advanced compression settings dialog."""
        dialog = AdvancedCompressionDialog(self, self.advanced_compression_manager)
        self.wait_window(dialog)

    def _open_metadata_dialog(self):
        """Open the metadata editing dialog."""
        dialog = MetadataDialog(self, self.metadata_manager, self.config_manager)
        self.wait_window(dialog)


class QualityPresetsDialog(tk.Toplevel):
    """Dialog for selecting and managing quality presets."""

    def __init__(self, parent, quality_presets_manager):
        super().__init__(parent)
        self.quality_presets_manager = quality_presets_manager
        self.selected_preset = None
        self.title("Quality Presets")
        self.geometry(f"{QUALITY_PRESET_DIALOG_WIDTH}x{QUALITY_PRESET_DIALOG_HEIGHT}")
        self.resizable(False, False)

        self._create_widgets()
        self._center_window()

    def _create_widgets(self):
        """Create dialog widgets."""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(main_frame, text="Choose Quality Preset",
                 font=("Segoe UI", 12, "bold")).pack(pady=(0, 10))

        # Presets list
        self.preset_var = tk.StringVar()
        presets_frame = ttk.Frame(main_frame)
        presets_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create radio buttons for each preset
        for preset in self.quality_presets_manager.get_builtin_presets():
            rb = ttk.Radiobutton(
                presets_frame,
                text=f"{preset.icon} {preset.name}",
                variable=self.preset_var,
                value=preset.preset_id,
                command=self._on_preset_selected
            )
            rb.pack(anchor=tk.W, pady=2)

        # Description area
        self.description_text = tk.Text(main_frame, height=4, wrap=tk.WORD, state=tk.DISABLED)
        self.description_text.pack(fill=tk.X, pady=(0, 10))

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="Apply", command=self._apply_preset).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def _on_preset_selected(self):
        """Handle preset selection."""
        preset_id = self.preset_var.get()
        preset = self.quality_presets_manager.get_preset(preset_id)
        if preset:
            self.selected_preset = preset
            self.description_text.config(state=tk.NORMAL)
            self.description_text.delete(1.0, tk.END)
            self.description_text.insert(1.0, preset.description)
            self.description_text.config(state=tk.DISABLED)

    def _apply_preset(self):
        """Apply the selected preset."""
        if self.selected_preset:
            self.quality_presets_manager.apply_preset(self.selected_preset.preset_id, {})
        self.destroy()

    def _center_window(self):
        """Center the window on the screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")


class AdvancedCompressionDialog(tk.Toplevel):
    """Dialog for advanced compression settings."""

    def __init__(self, parent, compression_manager):
        super().__init__(parent)
        self.compression_manager = compression_manager
        self.title("Advanced Compression Settings")
        self.geometry(f"{COMPRESSION_DIALOG_WIDTH}x{COMPRESSION_DIALOG_HEIGHT}")
        self.resizable(False, False)

        self._create_widgets()
        self._center_window()

    def _create_widgets(self):
        """Create dialog widgets."""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(main_frame, text="Advanced Compression Settings",
                 font=("Segoe UI", 12, "bold")).pack(pady=(0, 10))

        # Compression profiles
        profiles_frame = ttk.LabelFrame(main_frame, text="Compression Profiles", padding=5)
        profiles_frame.pack(fill=tk.X, pady=(0, 10))

        self.profile_var = tk.StringVar()
        for profile in self.compression_manager.get_all_profiles():
            rb = ttk.Radiobutton(
                profiles_frame,
                text=f"{profile.name} ({profile.estimated_ratio})",
                variable=self.profile_var,
                value=profile.profile_id
            )
            rb.pack(anchor=tk.W, pady=1)

        # Advanced settings
        settings_frame = ttk.LabelFrame(main_frame, text="Advanced Options", padding=5)
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        self.image_comp_var = tk.StringVar(value="auto")
        ttk.Label(settings_frame, text="Image Compression:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(settings_frame, textvariable=self.image_comp_var,
                    values=["auto", "lossless", "lossy", "none"], width=15,
                    state="readonly").grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)

        self.text_comp_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Text Compression",
                       variable=self.text_comp_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="Apply", command=self._apply_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def _apply_settings(self):
        """Apply the compression settings."""
        profile_id = self.profile_var.get()
        if profile_id:
            self.compression_manager.set_current_profile(profile_id)

        # Apply custom settings
        custom_settings = {
            'image_compression': self.image_comp_var.get(),
            'text_compression': self.text_comp_var.get()
        }
        self.compression_manager.update_custom_settings(custom_settings)

        self.destroy()

    def _center_window(self):
        """Center the window on the screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")


class MetadataDialog(tk.Toplevel):
    """Dialog for editing PDF metadata."""

    def __init__(self, parent, metadata_manager, config_manager):
        super().__init__(parent)
        self.metadata_manager = metadata_manager
        self.config_manager = config_manager
        self.title("Edit PDF Metadata")
        self.geometry(f"{METADATA_DIALOG_WIDTH}x{METADATA_DIALOG_HEIGHT}")
        self.resizable(True, True)

        self._create_widgets()
        self._load_metadata()
        self._center_window()

    def _create_widgets(self):
        """Create dialog widgets."""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(main_frame, text="Edit PDF Metadata",
                 font=("Segoe UI", 12, "bold")).pack(pady=(0, 10))

        # Create entry fields
        self.entries = {}
        field_info = self.metadata_manager.get_all_field_info()

        for field_name, info in field_info.items():
            frame = ttk.Frame(main_frame)
            frame.pack(fill=tk.X, pady=2)

            ttk.Label(frame, text=f"{info['label']}:",
                     width=12, anchor=tk.W).pack(side=tk.LEFT)

            if info.get('multiline', False):
                text = tk.Text(frame, height=3, width=50)
                text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
                self.entries[field_name] = text
            else:
                entry = ttk.Entry(frame)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
                if info.get('readonly', False):
                    entry.config(state='readonly')
                self.entries[field_name] = entry

            # Tooltip
            if hasattr(self, 'Tooltip'):
                Tooltip(frame, info.get('description', ''))

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        ttk.Button(btn_frame, text="Load from PDF",
                  command=self._load_from_pdf).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Clear All",
                  command=self._clear_all).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(btn_frame, text="Save", command=self._save_metadata).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def _load_metadata(self):
        """Load current metadata into the form."""
        metadata = self.metadata_manager.get_metadata()
        for field, value in metadata.items():
            if field in self.entries:
                widget = self.entries[field]

                # Check widget type more robustly
                widget_class_name = widget.__class__.__name__
                if widget_class_name == 'Text':  # Text widget
                    widget.delete(1.0, tk.END)
                    widget.insert(1.0, str(value) if value is not None else "")
                else:  # Entry widget (including ttk.Entry)
                    widget.delete(0, tk.END)
                    widget.insert(0, str(value) if value is not None else "")

    def _get_form_data(self):
        """Get data from the form."""
        data = {}
        for field, widget in self.entries.items():
            widget_class_name = widget.__class__.__name__
            if widget_class_name == 'Text':  # Text widget
                data[field] = widget.get(1.0, tk.END).strip()
            else:  # Entry widget
                data[field] = widget.get()
        return data

    def _save_metadata(self):
        """Save metadata from the form."""
        form_data = self._get_form_data()

        if self.metadata_manager.set_metadata(form_data):
            self.metadata_manager.save_to_config(self.config_manager)
            messagebox.showinfo("Success", "Metadata saved successfully!")
            self.destroy()
        else:
            validation_errors = self.metadata_manager.get_validation_errors()
            error_messages = []
            for field, errors in validation_errors.items():
                if errors:
                    error_messages.extend([f"{field}: {error}" for error in errors])

            messagebox.showerror("Validation Error",
                               f"Please fix the following errors:\n\n{chr(10).join(error_messages)}")

    def _load_from_pdf(self):
        """Load metadata from a PDF file."""
        file_path = filedialog.askopenfilename(
            title="Select PDF file",
            filetypes=[("PDF Files", "*.pdf")],
            parent=self
        )

        if file_path:
            success = self.metadata_manager.load_from_pdf(file_path)
            if success:
                self._load_metadata()
                messagebox.showinfo("Success", "Metadata loaded from PDF file!")
            else:
                messagebox.showerror("Error", "Failed to load metadata from PDF file.")

    def _clear_all(self):
        """Clear all metadata fields."""
        self.metadata_manager.clear_all()
        self._load_metadata()

    def _center_window(self):
        """Center the window on the screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")
