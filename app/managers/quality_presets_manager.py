"""
Quality Presets Manager for PDF Merger Pro

This module manages quality presets for different use cases (web, print, archive, etc.)
providing quick access to optimized settings combinations.
"""

from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

from ..utils.constants import (
    LOGGER_NAME, QUALITY_PRESETS, COMPRESSION_LEVELS,
    STATUS_QUALITY_PRESET_APPLIED
)
from ..managers.config_manager import ConfigManager


class QualityPreset:
    """Represents a quality preset with specific settings."""

    def __init__(self, preset_id: str, config: Dict[str, Any]):
        """
        Initialize a quality preset.

        Args:
            preset_id: Unique identifier for the preset
            config: Configuration dictionary for the preset
        """
        self.preset_id = preset_id
        self.name = config.get('name', preset_id)
        self.description = config.get('description', '')
        self.icon = config.get('icon', '⚙️')
        self.settings = {
            'compression': config.get('compression', 'normal'),
            'color_mode': config.get('color_mode', 'Colorful (Original)'),
            'dpi': config.get('dpi', 'Original'),
            'preserve_bookmarks': config.get('preserve_bookmarks', True)
        }

    def get_settings(self) -> Dict[str, Any]:
        """Get the settings for this preset."""
        return self.settings.copy()

    def get_display_info(self) -> Dict[str, str]:
        """Get display information for UI."""
        return {
            'id': self.preset_id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon
        }

    def get_compression_info(self) -> Dict[str, Any]:
        """Get compression information for this preset."""
        compression = self.settings.get('compression', 'normal')
        return COMPRESSION_LEVELS.get(compression, COMPRESSION_LEVELS['normal'])


class QualityPresetsManager:
    """Manages quality presets for the application."""

    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the quality presets manager.

        Args:
            config_manager: ConfigManager instance for persistence
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(LOGGER_NAME)
        self.presets: Dict[str, QualityPreset] = {}
        self._load_presets()

    def _load_presets(self):
        """Load quality presets from constants and configuration."""
        # Load built-in presets
        for preset_id, config in QUALITY_PRESETS.items():
            self.presets[preset_id] = QualityPreset(preset_id, config)

        # Load custom presets from config (future feature)
        custom_presets = self.config_manager.config.get('custom_quality_presets', {})
        for preset_id, config in custom_presets.items():
            if preset_id not in self.presets:  # Don't override built-in
                self.presets[preset_id] = QualityPreset(preset_id, config)

        self.logger.debug(f"Loaded {len(self.presets)} quality presets")

    def get_preset(self, preset_id: str) -> Optional[QualityPreset]:
        """
        Get a quality preset by ID.

        Args:
            preset_id: The preset identifier

        Returns:
            QualityPreset instance or None if not found
        """
        return self.presets.get(preset_id)

    def get_all_presets(self) -> List[QualityPreset]:
        """Get all available presets."""
        return list(self.presets.values())

    def get_preset_ids(self) -> List[str]:
        """Get all preset IDs."""
        return list(self.presets.keys())

    def get_builtin_presets(self) -> List[QualityPreset]:
        """Get built-in presets (not custom ones)."""
        return [preset for preset_id, preset in self.presets.items()
                if preset_id in QUALITY_PRESETS]

    def apply_preset(self, preset_id: str, output_settings: Dict[str, Any]) -> bool:
        """
        Apply a quality preset to output settings.

        Args:
            preset_id: The preset identifier
            output_settings: Dictionary to update with preset settings

        Returns:
            True if preset was applied successfully, False otherwise
        """
        preset = self.get_preset(preset_id)
        if not preset:
            self.logger.warning(f"Quality preset '{preset_id}' not found")
            return False

        preset_settings = preset.get_settings()
        output_settings.update(preset_settings)

        self.logger.info(f"Applied quality preset '{preset_id}': {preset.name}")
        return True

    def create_custom_preset(self, preset_id: str, name: str, description: str,
                           settings: Dict[str, Any]) -> bool:
        """
        Create a custom quality preset.

        Args:
            preset_id: Unique identifier for the preset
            name: Display name for the preset
            description: Description of the preset
            settings: Settings dictionary for the preset

        Returns:
            True if preset was created successfully, False otherwise
        """
        if preset_id in self.presets:
            self.logger.warning(f"Quality preset '{preset_id}' already exists")
            return False

        config = {
            'name': name,
            'description': description,
            'icon': '⭐',  # Custom preset icon
            **settings
        }

        self.presets[preset_id] = QualityPreset(preset_id, config)

        # Save to config
        custom_presets = self.config_manager.config.get('custom_quality_presets', {})
        custom_presets[preset_id] = config
        self.config_manager.update_config({'custom_quality_presets': custom_presets})

        self.logger.info(f"Created custom quality preset '{preset_id}': {name}")
        return True

    def delete_custom_preset(self, preset_id: str) -> bool:
        """
        Delete a custom quality preset.

        Args:
            preset_id: The preset identifier to delete

        Returns:
            True if preset was deleted successfully, False otherwise
        """
        if preset_id not in self.presets:
            self.logger.warning(f"Quality preset '{preset_id}' not found")
            return False

        # Check if it's a built-in preset (can't delete)
        if preset_id in QUALITY_PRESETS:
            self.logger.warning(f"Cannot delete built-in preset '{preset_id}'")
            return False

        # Remove from presets
        del self.presets[preset_id]

        # Remove from config
        custom_presets = self.config_manager.config.get('custom_quality_presets', {})
        if preset_id in custom_presets:
            del custom_presets[preset_id]
            self.config_manager.update_config({'custom_quality_presets': custom_presets})

        self.logger.info(f"Deleted custom quality preset '{preset_id}'")
        return True

    def get_recommended_preset(self, use_case: str = "general") -> Optional[str]:
        """
        Get recommended preset for a specific use case.

        Args:
            use_case: The intended use case

        Returns:
            Preset ID or None if no recommendation
        """
        recommendations = {
            'web': 'web',
            'print': 'print',
            'archive': 'archive',
            'screen': 'screen',
            'mobile': 'screen',
            'ebook': 'ebook',
            'fast': 'draft',
            'draft': 'draft'
        }

        return recommendations.get(use_case, 'normal')

    def get_preset_comparison(self, preset_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple presets.

        Args:
            preset_ids: List of preset IDs to compare

        Returns:
            Comparison dictionary
        """
        comparison = {}
        for preset_id in preset_ids:
            preset = self.get_preset(preset_id)
            if preset:
                comparison[preset_id] = {
                    'name': preset.name,
                    'settings': preset.get_settings(),
                    'compression_info': preset.get_compression_info()
                }

        return comparison

    def validate_preset_settings(self, settings: Dict[str, Any]) -> List[str]:
        """
        Validate preset settings.

        Args:
            settings: Settings dictionary to validate

        Returns:
            List of validation error messages
        """
        errors = []

        # Validate compression level
        compression = settings.get('compression', 'normal')
        if compression not in COMPRESSION_LEVELS:
            errors.append(f"Invalid compression level: {compression}")

        # Validate color mode (basic validation)
        color_mode = settings.get('color_mode', 'Colorful (Original)')
        valid_color_modes = ['Colorful (Original)', 'Grayscale (Experimental)', 'B&W (Experimental)']
        if color_mode not in valid_color_modes:
            errors.append(f"Invalid color mode: {color_mode}")

        # Validate DPI
        dpi = settings.get('dpi', 'Original')
        valid_dpi = ['Original', '72', '96', '150', '300', '600']
        if dpi not in valid_dpi:
            errors.append(f"Invalid DPI: {dpi}")

        return errors

    def get_preset_statistics(self) -> Dict[str, Any]:
        """Get statistics about preset usage."""
        builtin_count = len([p for p in self.presets.values() if p.preset_id in QUALITY_PRESETS])
        custom_count = len(self.presets) - builtin_count

        return {
            'total_presets': len(self.presets),
            'builtin_presets': builtin_count,
            'custom_presets': custom_count,
            'available_presets': list(self.presets.keys())
        }


# Global instance
_quality_presets_manager: Optional[QualityPresetsManager] = None


def get_quality_presets_manager(config_manager: Optional[ConfigManager] = None) -> QualityPresetsManager:
    """Get the global quality presets manager instance."""
    global _quality_presets_manager
    if _quality_presets_manager is None and config_manager is not None:
        _quality_presets_manager = QualityPresetsManager(config_manager)
    return _quality_presets_manager


def initialize_quality_presets_manager(config_manager: ConfigManager) -> QualityPresetsManager:
    """Initialize the global quality presets manager."""
    global _quality_presets_manager
    _quality_presets_manager = QualityPresetsManager(config_manager)
    return _quality_presets_manager
