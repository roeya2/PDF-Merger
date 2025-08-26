"""
Recent Folders Manager for PDF Merger Pro

This module manages recently accessed folders to provide quick access
for users who frequently work with files from the same directories.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from ..utils.constants import MAX_RECENT_FOLDERS, RECENT_FOLDERS_KEY
from ..managers.config_manager import ConfigManager


class RecentFolder:
    """Represents a recently accessed folder."""

    def __init__(self, path: str, name: Optional[str] = None,
                 last_accessed: Optional[datetime] = None):
        """
        Initialize a recent folder entry.

        Args:
            path: Full path to the folder
            name: Display name (optional, will use folder name if not provided)
            last_accessed: Last access timestamp
        """
        self.path = str(Path(path).resolve())
        self.name = name or Path(path).name
        self.last_accessed = last_accessed or datetime.now()
        self.access_count = 1
        self.is_favorite = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'path': self.path,
            'name': self.name,
            'last_accessed': self.last_accessed.isoformat(),
            'access_count': self.access_count,
            'is_favorite': self.is_favorite
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecentFolder':
        """Create instance from dictionary."""
        folder = cls(
            path=data['path'],
            name=data.get('name'),
            last_accessed=datetime.fromisoformat(data['last_accessed'])
        )
        folder.access_count = data.get('access_count', 1)
        folder.is_favorite = data.get('is_favorite', False)
        return folder

    def exists(self) -> bool:
        """Check if the folder still exists."""
        return Path(self.path).exists() and Path(self.path).is_dir()

    def get_display_name(self) -> str:
        """Get a user-friendly display name."""
        if self.name != Path(self.path).name:
            return f"{self.name} ({Path(self.path).name})"
        return self.name

    def get_short_path(self, max_length: int = 50) -> str:
        """Get a shortened version of the path for display."""
        path_str = self.path
        if len(path_str) <= max_length:
            return path_str

        # Try to show the end of the path with ellipsis
        parts = Path(path_str).parts
        if len(parts) <= 2:
            return path_str

        # Show last 2 parts with ellipsis
        return f"...{os.sep}{os.sep.join(parts[-2:])}"


class RecentFoldersManager:
    """Manages recently accessed folders with persistence."""

    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the recent folders manager.

        Args:
            config_manager: ConfigManager instance for persistence
        """
        self.config_manager = config_manager
        self.recent_folders: List[RecentFolder] = []
        self._load_recent_folders()

    def _load_recent_folders(self):
        """Load recent folders from configuration."""
        try:
            folders_data = self.config_manager.config.get(RECENT_FOLDERS_KEY, [])
            self.recent_folders = [
                RecentFolder.from_dict(data) for data in folders_data
                if Path(data.get('path', '')).exists()
            ]
            # Sort by last accessed (most recent first)
            self.recent_folders.sort(key=lambda x: x.last_accessed, reverse=True)
        except Exception as e:
            print(f"Error loading recent folders: {e}")
            self.recent_folders = []

    def _save_recent_folders(self):
        """Save recent folders to configuration."""
        try:
            folders_data = [folder.to_dict() for folder in self.recent_folders]
            self.config_manager.update_config({RECENT_FOLDERS_KEY: folders_data})
        except Exception as e:
            print(f"Error saving recent folders: {e}")

    def add_folder(self, folder_path: str):
        """
        Add a folder to the recent folders list.

        Args:
            folder_path: Path to the folder to add
        """
        folder_path = str(Path(folder_path).resolve())

        # Check if folder exists
        if not Path(folder_path).exists() or not Path(folder_path).is_dir():
            return

        # Check if already exists
        for i, folder in enumerate(self.recent_folders):
            if folder.path == folder_path:
                # Update existing entry
                folder.last_accessed = datetime.now()
                folder.access_count += 1
                # Move to front
                self.recent_folders.insert(0, self.recent_folders.pop(i))
                self._save_recent_folders()
                return

        # Add new entry
        new_folder = RecentFolder(folder_path)
        self.recent_folders.insert(0, new_folder)

        # Trim to max size
        if len(self.recent_folders) > MAX_RECENT_FOLDERS:
            self.recent_folders = self.recent_folders[:MAX_RECENT_FOLDERS]

        self._save_recent_folders()

    def remove_folder(self, folder_path: str):
        """
        Remove a folder from the recent folders list.

        Args:
            folder_path: Path to the folder to remove
        """
        folder_path = str(Path(folder_path).resolve())
        self.recent_folders = [
            folder for folder in self.recent_folders
            if folder.path != folder_path
        ]
        self._save_recent_folders()

    def clear_all(self):
        """Clear all recent folders."""
        self.recent_folders = []
        self._save_recent_folders()

    def get_recent_folders(self, include_invalid: bool = False) -> List[RecentFolder]:
        """
        Get the list of recent folders.

        Args:
            include_invalid: Whether to include folders that no longer exist

        Returns:
            List of recent folders
        """
        if include_invalid:
            return self.recent_folders.copy()

        return [folder for folder in self.recent_folders if folder.exists()]

    def get_favorite_folders(self) -> List[RecentFolder]:
        """Get the list of favorite folders."""
        return [folder for folder in self.recent_folders if folder.is_favorite]

    def toggle_favorite(self, folder_path: str):
        """
        Toggle favorite status of a folder.

        Args:
            folder_path: Path to the folder
        """
        folder_path = str(Path(folder_path).resolve())
        for folder in self.recent_folders:
            if folder.path == folder_path:
                folder.is_favorite = not folder.is_favorite
                self._save_recent_folders()
                return

    def get_quick_access_folders(self) -> List[Dict[str, Any]]:
        """
        Get folders for quick access (favorites + most recent).

        Returns:
            List of folder dictionaries with metadata
        """
        valid_folders = self.get_recent_folders()

        # Get favorites first
        favorites = [f for f in valid_folders if f.is_favorite]
        non_favorites = [f for f in valid_folders if not f.is_favorite]

        # Combine: favorites first, then most recent non-favorites
        quick_access = favorites + non_favorites[:5]  # Max 5 quick access items

        result = []
        for folder in quick_access:
            result.append({
                'path': folder.path,
                'display_name': folder.get_display_name(),
                'short_path': folder.get_short_path(),
                'last_accessed': folder.last_accessed,
                'access_count': folder.access_count,
                'is_favorite': folder.is_favorite,
                'exists': folder.exists()
            })

        return result

    def cleanup_invalid_folders(self):
        """Remove folders that no longer exist."""
        original_count = len(self.recent_folders)
        self.recent_folders = [f for f in self.recent_folders if f.exists()]

        if len(self.recent_folders) != original_count:
            self._save_recent_folders()

    def get_folder_stats(self) -> Dict[str, Any]:
        """Get statistics about recent folders."""
        valid_folders = self.get_recent_folders()
        favorites = [f for f in valid_folders if f.is_favorite]

        return {
            'total_folders': len(self.recent_folders),
            'valid_folders': len(valid_folders),
            'favorite_folders': len(favorites),
            'most_accessed': max((f.access_count for f in valid_folders), default=0),
            'oldest_access': min((f.last_accessed for f in valid_folders), default=None),
            'newest_access': max((f.last_accessed for f in valid_folders), default=None),
        }


# Convenience functions for easy access
_recent_folders_manager: Optional[RecentFoldersManager] = None


def initialize_recent_folders_manager(config_manager: ConfigManager) -> RecentFoldersManager:
    """Initialize the global recent folders manager."""
    global _recent_folders_manager
    _recent_folders_manager = RecentFoldersManager(config_manager)
    return _recent_folders_manager


def get_recent_folders_manager() -> Optional[RecentFoldersManager]:
    """Get the global recent folders manager instance."""
    return _recent_folders_manager


def add_recent_folder(folder_path: str):
    """Add a folder to recent folders (convenience function)."""
    manager = get_recent_folders_manager()
    if manager:
        manager.add_folder(folder_path)


def get_quick_access_folders() -> List[Dict[str, Any]]:
    """Get quick access folders (convenience function)."""
    manager = get_recent_folders_manager()
    if manager:
        return manager.get_quick_access_folders()
    return []
