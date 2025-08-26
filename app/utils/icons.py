"""
Icon Management System for PDF Merger Pro

This module provides a centralized system for managing UI icons using Unicode characters
and styled text. It ensures consistent iconography throughout the application.
"""

import tkinter as tk
from typing import Dict, Any, Optional

from .constants import (
    ICON_SIZE_SMALL, ICON_SIZE_MEDIUM, ICON_SIZE_LARGE,
    PRIMARY_COLOR, SECONDARY_COLOR, SUCCESS_COLOR, WARNING_COLOR, ERROR_COLOR,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DISABLED,
    FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_LG
)


class IconManager:
    """Manages icons and their styling for the application."""

    # Unicode icons for common actions
    ICONS = {
        # File Operations
        "add_file": "📄",
        "add_folder": "📁",
        "remove": "🗑️",
        "clear": "🧹",

        # Navigation and Movement
        "move_up": "⬆️",
        "move_down": "⬇️",
        "move_left": "⬅️",
        "move_right": "➡️",

        # Actions
        "merge": "🔗",
        "validate": "✅",
        "preview": "👁️",
        "save": "💾",
        "load": "📂",
        "export": "📤",

        # Settings and Configuration
        "settings": "⚙️",
        "page_range": "📄",
        "password": "🔒",
        "compress": "🗜️",

        # Status and Feedback
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "info": "ℹ️",
        "loading": "⏳",

        # File Types
        "pdf": "📕",
        "word": "📝",
        "epub": "📚",
        "archive": "📦",

        # UI Elements
        "search": "🔍",
        "filter": "🔽",
        "expand": "▶️",
        "collapse": "🔽",
        "menu": "☰",

        # Special Characters
        "bullet": "•",
        "arrow_right": "→",
        "arrow_left": "←",
        "check": "✓",
        "cross": "✗",
        "star": "★",
        "heart": "♥",
    }

    # Icon color mappings
    ICON_COLORS = {
        "primary": PRIMARY_COLOR,
        "secondary": SECONDARY_COLOR,
        "success": SUCCESS_COLOR,
        "warning": WARNING_COLOR,
        "error": ERROR_COLOR,
        "info": PRIMARY_COLOR,
        "text_primary": TEXT_PRIMARY,
        "text_secondary": TEXT_SECONDARY,
        "text_disabled": TEXT_DISABLED,
    }

    def __init__(self):
        """Initialize the icon manager."""
        self._icon_cache: Dict[str, Any] = {}

    def get_icon(self, name: str, size: str = "medium", color: str = "text_primary") -> str:
        """
        Get an icon by name with specified size and color.

        Args:
            name: Icon name from ICONS dictionary
            size: Size variant ("small", "medium", "large")
            color: Color variant from ICON_COLORS

        Returns:
            Unicode character for the icon
        """
        if name not in self.ICONS:
            return "❓"  # Question mark for unknown icons

        return self.ICONS[name]

    def create_icon_label(self, parent, icon_name: str, size: str = "medium",
                         color: str = "text_primary", **kwargs) -> tk.Label:
        """
        Create a Label widget with an icon.

        Args:
            parent: Parent widget
            icon_name: Name of the icon
            size: Size variant
            color: Color variant
            **kwargs: Additional arguments for Label

        Returns:
            Configured Label widget
        """
        icon_char = self.get_icon(icon_name, size, color)

        # Set font size based on icon size
        size_map = {
            "small": FONT_SIZE_SM,
            "medium": FONT_SIZE_MD,
            "large": FONT_SIZE_LG
        }
        font_size = size_map.get(size, FONT_SIZE_MD)

        # Create label with icon
        label = tk.Label(
            parent,
            text=icon_char,
            font=("Segoe UI", font_size),
            fg=self.ICON_COLORS.get(color, TEXT_PRIMARY),
            **kwargs
        )

        return label

    def create_icon_button(self, parent, icon_name: str, command=None,
                          size: str = "medium", color: str = "primary",
                          tooltip: str = "", **kwargs) -> tk.Button:
        """
        Create a Button widget with an icon.

        Args:
            parent: Parent widget
            icon_name: Name of the icon
            command: Button command function
            size: Size variant
            color: Color variant
            tooltip: Tooltip text
            **kwargs: Additional arguments for Button

        Returns:
            Configured Button widget
        """
        icon_char = self.get_icon(icon_name, size, color)

        # Set font size based on icon size
        size_map = {
            "small": FONT_SIZE_SM,
            "medium": FONT_SIZE_MD,
            "large": FONT_SIZE_LG
        }
        font_size = size_map.get(size, FONT_SIZE_MD)

        # Create button with icon
        button = tk.Button(
            parent,
            text=icon_char,
            command=command,
            font=("Segoe UI", font_size),
            fg=self.ICON_COLORS.get(color, PRIMARY_COLOR),
            **kwargs
        )

        # Add tooltip if provided
        if tooltip:
            from ..ui.tooltip import Tooltip
            Tooltip(button, tooltip)

        return button

    def get_colored_icon(self, name: str, color: str = "primary") -> str:
        """
        Get an icon with color information (for use with styling).

        Args:
            name: Icon name
            color: Color variant

        Returns:
            Icon character (color is applied via widget styling)
        """
        return self.get_icon(name, color=color)

    def get_file_type_icon(self, file_extension: str) -> str:
        """
        Get appropriate icon for file type based on extension.

        Args:
            file_extension: File extension (e.g., '.pdf', '.docx')

        Returns:
            Appropriate icon character
        """
        ext = file_extension.lower()

        if ext in ['.pdf']:
            return self.ICONS["pdf"]
        elif ext in ['.docx', '.doc']:
            return self.ICONS["word"]
        elif ext in ['.epub']:
            return self.ICONS["epub"]
        elif ext in ['.zip', '.rar']:
            return self.ICONS["archive"]
        else:
            return self.ICONS["add_file"]  # Default file icon


# Global icon manager instance
_icon_manager_instance: Optional[IconManager] = None


def get_icon_manager() -> IconManager:
    """Get the global icon manager instance."""
    global _icon_manager_instance
    if _icon_manager_instance is None:
        _icon_manager_instance = IconManager()
    return _icon_manager_instance


def get_icon(name: str, size: str = "medium", color: str = "text_primary") -> str:
    """Convenience function to get an icon."""
    return get_icon_manager().get_icon(name, size, color)


def create_icon_label(parent, icon_name: str, **kwargs) -> tk.Label:
    """Convenience function to create an icon label."""
    return get_icon_manager().create_icon_label(parent, icon_name, **kwargs)


def create_icon_button(parent, icon_name: str, **kwargs) -> tk.Button:
    """Convenience function to create an icon button."""
    return get_icon_manager().create_icon_button(parent, icon_name, **kwargs)
