"""
Advanced Compression Manager for PDF Merger Pro

This module provides advanced compression control with granular settings,
compression profiles, and quality vs file size optimization.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
import math

from ..utils.constants import (
    LOGGER_NAME, COMPRESSION_LEVELS, DEFAULT_COMPRESSION,
    STATUS_ADVANCED_COMPRESSION_SET
)


class CompressionProfile:
    """Represents a compression profile with specific settings."""

    def __init__(self, profile_id: str, config: Dict[str, Any]):
        """
        Initialize a compression profile.

        Args:
            profile_id: Unique identifier for the profile
            config: Configuration dictionary for the profile
        """
        self.profile_id = profile_id
        self.name = config.get('name', profile_id)
        self.description = config.get('description', '')
        self.pypdf_level = config.get('pypdf_level', 2)
        self.estimated_ratio = config.get('estimated_ratio', '70-85%')
        self.speed = config.get('speed', 'Medium')
        self.recommended_use = config.get('recommended_use', [])

        # Advanced settings
        self.image_compression = config.get('image_compression', 'auto')
        self.text_compression = config.get('text_compression', True)
        self.font_optimization = config.get('font_optimization', True)
        self.structure_optimization = config.get('structure_optimization', True)

    def get_settings(self) -> Dict[str, Any]:
        """Get the complete settings for this profile."""
        return {
            'compression_level': self.profile_id,
            'pypdf_level': self.pypdf_level,
            'image_compression': self.image_compression,
            'text_compression': self.text_compression,
            'font_optimization': self.font_optimization,
            'structure_optimization': self.structure_optimization
        }

    def get_display_info(self) -> Dict[str, Any]:
        """Get display information for UI."""
        return {
            'id': self.profile_id,
            'name': self.name,
            'description': self.description,
            'estimated_ratio': self.estimated_ratio,
            'speed': self.speed,
            'pypdf_level': self.pypdf_level
        }

    def estimate_file_size(self, original_size: int, page_count: int = 1) -> Tuple[int, str]:
        """
        Estimate compressed file size.

        Args:
            original_size: Original file size in bytes
            page_count: Number of pages

        Returns:
            Tuple of (estimated_size, description)
        """
        # Parse estimated ratio range
        ratio_str = self.estimated_ratio.replace('%', '')
        if '-' in ratio_str:
            min_ratio, max_ratio = map(float, ratio_str.split('-'))
            avg_ratio = (min_ratio + max_ratio) / 2 / 100
        else:
            avg_ratio = float(ratio_str) / 100

        estimated_size = int(original_size * avg_ratio)

        # Add page count factor (more pages = slightly better compression)
        if page_count > 10:
            page_factor = min(0.95, 1 - (page_count - 10) * 0.005)
            estimated_size = int(estimated_size * page_factor)

        return estimated_size, f"~{self.estimated_ratio} of original"


class AdvancedCompressionManager:
    """Manages advanced compression settings and profiles."""

    def __init__(self):
        """Initialize the advanced compression manager."""
        self.logger = logging.getLogger(LOGGER_NAME)
        self.profiles: Dict[str, CompressionProfile] = {}
        self.current_profile: Optional[str] = None
        self.custom_settings: Dict[str, Any] = {}

        self._load_profiles()

    def _load_profiles(self):
        """Load compression profiles from constants."""
        for profile_id, config in COMPRESSION_LEVELS.items():
            self.profiles[profile_id] = CompressionProfile(profile_id, config)

        self.logger.debug(f"Loaded {len(self.profiles)} compression profiles")

    def get_profile(self, profile_id: str) -> Optional[CompressionProfile]:
        """
        Get a compression profile by ID.

        Args:
            profile_id: The profile identifier

        Returns:
            CompressionProfile instance or None if not found
        """
        return self.profiles.get(profile_id)

    def get_all_profiles(self) -> List[CompressionProfile]:
        """Get all available profiles."""
        return list(self.profiles.values())

    def get_profile_ids(self) -> List[str]:
        """Get all profile IDs."""
        return list(self.profiles.keys())

    def set_current_profile(self, profile_id: str) -> bool:
        """
        Set the current compression profile.

        Args:
            profile_id: The profile identifier

        Returns:
            True if profile was set successfully
        """
        if profile_id not in self.profiles:
            self.logger.warning(f"Compression profile '{profile_id}' not found")
            return False

        self.current_profile = profile_id
        self.logger.info(f"Set compression profile to '{profile_id}'")
        return True

    def get_current_profile(self) -> Optional[CompressionProfile]:
        """Get the current compression profile."""
        if self.current_profile:
            return self.get_profile(self.current_profile)
        return None

    def get_settings_for_profile(self, profile_id: str) -> Dict[str, Any]:
        """
        Get complete settings for a profile.

        Args:
            profile_id: The profile identifier

        Returns:
            Settings dictionary
        """
        profile = self.get_profile(profile_id)
        if profile:
            settings = profile.get_settings()
            # Merge with custom settings
            settings.update(self.custom_settings)
            return settings

        # Return default settings if profile not found
        return self.get_default_settings()

    def get_current_settings(self) -> Dict[str, Any]:
        """Get current compression settings."""
        if self.current_profile:
            return self.get_settings_for_profile(self.current_profile)
        return self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        """Get default compression settings."""
        return self.get_settings_for_profile(DEFAULT_COMPRESSION)

    def update_custom_settings(self, settings: Dict[str, Any]):
        """
        Update custom compression settings.

        Args:
            settings: Dictionary of custom settings
        """
        valid_keys = [
            'image_compression', 'text_compression', 'font_optimization',
            'structure_optimization', 'image_quality', 'color_sampling'
        ]

        for key, value in settings.items():
            if key in valid_keys:
                self.custom_settings[key] = value
                self.logger.debug(f"Updated custom setting {key} = {value}")

    def reset_custom_settings(self):
        """Reset custom settings to defaults."""
        self.custom_settings.clear()
        self.logger.info("Custom compression settings reset")

    def get_compression_estimate(self, profile_id: str, original_size: int,
                               page_count: int = 1) -> Dict[str, Any]:
        """
        Get compression size estimate for a profile.

        Args:
            profile_id: The profile identifier
            original_size: Original file size in bytes
            page_count: Number of pages

        Returns:
            Estimation dictionary
        """
        profile = self.get_profile(profile_id)
        if not profile:
            return {}

        estimated_size, ratio_desc = profile.estimate_file_size(original_size, page_count)
        savings = original_size - estimated_size
        savings_percentage = (savings / original_size) * 100 if original_size > 0 else 0

        return {
            'profile_id': profile_id,
            'profile_name': profile.name,
            'original_size': original_size,
            'estimated_size': estimated_size,
            'savings_bytes': savings,
            'savings_percentage': savings_percentage,
            'ratio_description': ratio_desc,
            'page_count': page_count
        }

    def compare_profiles(self, profile_ids: List[str], original_size: int,
                        page_count: int = 1) -> List[Dict[str, Any]]:
        """
        Compare multiple compression profiles.

        Args:
            profile_ids: List of profile IDs to compare
            original_size: Original file size in bytes
            page_count: Number of pages

        Returns:
            List of comparison dictionaries
        """
        comparisons = []

        for profile_id in profile_ids:
            estimate = self.get_compression_estimate(profile_id, original_size, page_count)
            if estimate:
                comparisons.append(estimate)

        # Sort by estimated size (smallest first)
        comparisons.sort(key=lambda x: x.get('estimated_size', 0))

        return comparisons

    def get_recommended_profile(self, criteria: Dict[str, Any]) -> str:
        """
        Get recommended compression profile based on criteria.

        Args:
            criteria: Dictionary with criteria like 'speed', 'size', 'quality'

        Returns:
            Recommended profile ID
        """
        speed_priority = criteria.get('speed', 'medium')
        size_priority = criteria.get('size', 'medium')
        quality_priority = criteria.get('quality', 'medium')

        # Simple recommendation logic
        if speed_priority == 'high':
            return 'none'
        elif size_priority == 'high':
            return 'maximum'
        elif quality_priority == 'high':
            return 'fast'  # Best quality with reasonable speed
        else:
            return 'normal'  # Balanced default

    def validate_compression_settings(self, settings: Dict[str, Any]) -> List[str]:
        """
        Validate compression settings.

        Args:
            settings: Settings dictionary to validate

        Returns:
            List of validation error messages
        """
        errors = []

        # Validate compression level
        compression_level = settings.get('compression_level', 'normal')
        if compression_level not in COMPRESSION_LEVELS:
            errors.append(f"Invalid compression level: {compression_level}")

        # Validate image compression
        image_compression = settings.get('image_compression', 'auto')
        valid_image_options = ['auto', 'lossless', 'lossy', 'none']
        if image_compression not in valid_image_options:
            errors.append(f"Invalid image compression: {image_compression}")

        # Validate boolean settings
        boolean_settings = ['text_compression', 'font_optimization', 'structure_optimization']
        for setting in boolean_settings:
            value = settings.get(setting)
            if value is not None and not isinstance(value, bool):
                errors.append(f"Invalid {setting}: must be boolean")

        return errors

    def get_profile_statistics(self) -> Dict[str, Any]:
        """Get statistics about compression profiles."""
        return {
            'total_profiles': len(self.profiles),
            'available_profiles': list(self.profiles.keys()),
            'current_profile': self.current_profile,
            'custom_settings_count': len(self.custom_settings)
        }

    def export_profile_settings(self, profile_id: str, format_type: str = 'dict') -> Any:
        """
        Export profile settings in different formats.

        Args:
            profile_id: The profile identifier
            format_type: Format to export ('dict', 'json', 'list')

        Returns:
            Settings in the requested format
        """
        profile = self.get_profile(profile_id)
        if not profile:
            return None

        settings = profile.get_settings()

        if format_type == 'dict':
            return settings
        elif format_type == 'json':
            import json
            return json.dumps(settings, indent=2)
        elif format_type == 'list':
            return list(settings.items())
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def create_custom_profile(self, profile_id: str, name: str, description: str,
                            pypdf_level: int, settings: Dict[str, Any]) -> bool:
        """
        Create a custom compression profile.

        Args:
            profile_id: Unique identifier for the profile
            name: Display name for the profile
            description: Description of the profile
            pypdf_level: PyPDF compression level (0-4)
            settings: Additional settings dictionary

        Returns:
            True if profile was created successfully
        """
        if profile_id in self.profiles:
            self.logger.warning(f"Compression profile '{profile_id}' already exists")
            return False

        if not 0 <= pypdf_level <= 4:
            self.logger.warning(f"Invalid PyPDF level: {pypdf_level} (must be 0-4)")
            return False

        config = {
            'name': name,
            'description': description,
            'pypdf_level': pypdf_level,
            'estimated_ratio': settings.get('estimated_ratio', '70-85%'),
            'speed': settings.get('speed', 'Medium'),
            'recommended_use': settings.get('recommended_use', []),
            **settings
        }

        self.profiles[profile_id] = CompressionProfile(profile_id, config)
        self.logger.info(f"Created custom compression profile '{profile_id}': {name}")
        return True


# Global instance
_advanced_compression_manager: Optional[AdvancedCompressionManager] = None


def get_advanced_compression_manager() -> AdvancedCompressionManager:
    """Get the global advanced compression manager instance."""
    global _advanced_compression_manager
    if _advanced_compression_manager is None:
        _advanced_compression_manager = AdvancedCompressionManager()
    return _advanced_compression_manager


def initialize_advanced_compression_manager() -> AdvancedCompressionManager:
    """Initialize the global advanced compression manager."""
    global _advanced_compression_manager
    _advanced_compression_manager = AdvancedCompressionManager()
    return _advanced_compression_manager
