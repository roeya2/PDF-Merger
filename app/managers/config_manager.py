import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from ..utils.constants import (
    LOGGER_NAME, DEFAULT_CONFIG_PATH, MAX_RECENT_DIRS, DEFAULT_COMPRESSION,
    DEFAULT_PRESERVE_BOOKMARKS, DEFAULT_PASSWORD_PROTECT, DEFAULT_COLOR_MODE,
    DEFAULT_DPI, DEFAULT_LOG_OUTPUT, DEFAULT_LOG_LEVEL, DEFAULT_LOG_FILE_PATH,
    PROFILE_LIST_KEY, WINDOW_GEOMETRY_KEY, PANEDWINDOW_SASH_KEY
)

class ConfigManager:
    """Manages application configuration including recent files/dirs, profiles, and window state."""
    def __init__(self, config_path: Path = DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self.logger = logging.getLogger(LOGGER_NAME)
        # Define default configuration structure
        self.config: Dict[str, Any] = self._get_default_config()
        self.load_config() # Load config immediately upon initialization

    def _get_default_config(self) -> Dict[str, Any]:
        """Returns the default configuration structure."""
        return {
            "base_directory": str(Path.home()),  # Default base to user home
            "recent_directories": [],
            "default_output_dir": str(Path.home()),  # Default output to user home
            "compression_level": DEFAULT_COMPRESSION,
            "preserve_bookmarks": DEFAULT_PRESERVE_BOOKMARKS,
            "profiles": {},
            "output_password_protect": DEFAULT_PASSWORD_PROTECT,
            "output_color_mode": DEFAULT_COLOR_MODE,
            "output_dpi": DEFAULT_DPI,
            "log_output": DEFAULT_LOG_OUTPUT,
            "log_level": DEFAULT_LOG_LEVEL,
            "log_file_path": DEFAULT_LOG_FILE_PATH,
            WINDOW_GEOMETRY_KEY: "",
            PANEDWINDOW_SASH_KEY: {}
        }

    def load_config(self):
        """Loads configuration from the JSON file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge loaded config into defaults, prioritizing loaded values
                    # Create a new dict with defaults, then update with loaded values
                    temp_config = self.config.copy()
                    temp_config.update(loaded_config)
                    self.config = temp_config
                self.logger.info(f"Configuration successfully loaded from {self.config_path}")
        except FileNotFoundError:
             self.logger.info(f"Configuration file not found at {self.config_path}. Using default configuration.")
             # Defaults are already in self.config, so nothing more to do
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON from configuration file {self.config_path}: {e}. Using default configuration.", exc_info=True)
            # Reset config to defaults if load fails
            self.config = self._get_default_config()
        except Exception as e:
            self.logger.error(f"Unexpected error loading configuration from {self.config_path}: {e}. Using default configuration.", exc_info=True)
            # Ensure config is reset to defaults on unexpected error
            self.config = self._get_default_config()


    def save_config(self):
        """Saves the current configuration to the JSON file."""
        try:
            # Ensure the directory exists
            config_dir = self.config_path.parent
            config_dir.mkdir(parents=True, exist_ok=True) # Create dir if it doesn't exist

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Configuration successfully saved to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Error saving configuration to {self.config_path}: {e}", exc_info=True)

    def add_recent_directory(self, directory: str):
        """Adds a directory to the list of recent directories."""
        if not isinstance(directory, str) or not directory or not os.path.isdir(directory):
            self.logger.debug(f"Skipping invalid or non-existent directory for recent list: {directory}")
            return

        try:
            cleaned_dir = str(Path(directory).resolve()) # Canonicalize path
        except Exception as e:
            self.logger.warning(f"Could not resolve directory path {directory} for recent list: {e}")
            cleaned_dir = directory # Use original if resolve fails

        if cleaned_dir in self.config["recent_directories"]:
            self.config["recent_directories"].remove(cleaned_dir)
        self.config["recent_directories"].insert(0, cleaned_dir)
        self.config["recent_directories"] = self.config["recent_directories"][:MAX_RECENT_DIRS]
        self.logger.debug(f"Added '{cleaned_dir}' to recent directories. List size: {len(self.config['recent_directories'])}")

    def save_profile(self, name: str, file_list_details: List[Dict]):
        """Saves the current file list and relevant settings as a profile."""
        if not name or not isinstance(name, str) or not name.strip():
             self.logger.warning("Attempted to save profile with invalid name.")
             raise ValueError("Profile name cannot be empty.")

        profile_data = {
            PROFILE_LIST_KEY: file_list_details,
            "compression_level": self.config.get("compression_level", DEFAULT_COMPRESSION),
            "preserve_bookmarks": self.config.get("preserve_bookmarks", DEFAULT_PRESERVE_BOOKMARKS),
            "output_password_protect": self.config.get("output_password_protect", DEFAULT_PASSWORD_PROTECT),
            # Password is NOT saved for security
            "output_color_mode": self.config.get("output_color_mode", DEFAULT_COLOR_MODE),
            "output_dpi": self.config.get("output_dpi", DEFAULT_DPI),
            "created": datetime.now().isoformat()
        }
        self.config["profiles"][name.strip()] = profile_data # Use stripped name as key
        self.save_config()
        self.logger.info(f"Profile '{name.strip()}' saved.")

    def get_profile(self, name: str) -> Optional[Dict]:
        """Retrieves a profile's configuration."""
        return self.config["profiles"].get(name)

    def delete_profile(self, name: str) -> bool:
        """Deletes a saved profile."""
        if name in self.config["profiles"]:
            del self.config["profiles"][name]
            self.save_config()
            self.logger.info(f"Profile '{name}' successfully deleted.")
            return True
        self.logger.warning(f"Profile '{name}' not found for deletion.")
        return False

    def save_window_state(self, geometry: str, sash_positions: Dict[str, Tuple[int, ...]]):
        """Saves window geometry and panedwindow sash positions."""
        self.config[WINDOW_GEOMETRY_KEY] = geometry
        self.config[PANEDWINDOW_SASH_KEY] = sash_positions
        self.logger.debug(f"Saving window state: geometry='{geometry}', sash_positions={sash_positions}")
        # Note: Config save should happen after calling this method, e.g., on app close.
        # self.save_config() # Don't save here to avoid excessive writes

    def load_window_state(self) -> Tuple[str, Dict[str, Tuple[int, ...]]]:
        """Loads window geometry and panedwindow sash positions."""
        geometry = self.config.get(WINDOW_GEOMETRY_KEY, "")
        sash_positions = self.config.get(PANEDWINDOW_SASH_KEY, {})
        self.logger.debug(f"Loaded window state: geometry='{geometry}', sash_positions={sash_positions}")
        return geometry, sash_positions