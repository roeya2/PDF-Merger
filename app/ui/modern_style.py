"""
Modern Styling System for PDF Merger Pro

This module provides modern styling capabilities using ttk styles and custom widget enhancements.
It implements the design system with consistent colors, typography, and modern visual elements.
"""

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from typing import Dict, Any, Optional

from ..utils.constants import (
    # Colors
    PRIMARY_COLOR, PRIMARY_HOVER, PRIMARY_LIGHT, PRIMARY_DARK,
    SECONDARY_COLOR, SECONDARY_HOVER, SECONDARY_LIGHT,
    SUCCESS_COLOR, SUCCESS_LIGHT, SUCCESS_DARK,
    WARNING_COLOR, WARNING_LIGHT, WARNING_DARK,
    ERROR_COLOR, ERROR_LIGHT, ERROR_DARK,
    INFO_COLOR, INFO_LIGHT, INFO_DARK,
    BACKGROUND_COLOR, SURFACE_COLOR, SURFACE_VARIANT,
    BORDER_COLOR, BORDER_DARK,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DISABLED,
    SHADOW_LIGHT, SHADOW_MEDIUM, SHADOW_DARK,
    ACCENT_COLOR, ACCENT_LIGHT,

    # Typography
    PRIMARY_FONT, HEADING_FONT, MONOSPACE_FONT,
    FONT_SIZE_XS, FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_LG,
    FONT_SIZE_XL, FONT_SIZE_2XL, FONT_SIZE_3XL,
    FONT_WEIGHT_NORMAL, FONT_WEIGHT_MEDIUM, FONT_WEIGHT_SEMIBOLD, FONT_WEIGHT_BOLD,

    # Spacing
    SPACE_1, SPACE_2, SPACE_3, SPACE_4, SPACE_5, SPACE_6,

    # UI Constants
    BUTTON_CORNER_RADIUS, FRAME_CORNER_RADIUS, BORDER_WIDTH,
)


class ModernStyle:
    """Provides modern styling capabilities for the application."""

    def __init__(self, root: tk.Tk):
        """
        Initialize the modern styling system.

        Args:
            root: The root Tkinter window
        """
        self.root = root
        self.style = ttk.Style()

        # Configure modern fonts
        self._setup_fonts()
        self._configure_styles()
        self._setup_color_variables()

    def _setup_fonts(self):
        """Set up custom fonts for the application."""
        try:
            # Try to use modern fonts if available
            self.fonts = {
                'primary': tkfont.Font(family=PRIMARY_FONT, size=FONT_SIZE_MD, weight=FONT_WEIGHT_NORMAL),
                'heading': tkfont.Font(family=HEADING_FONT, size=FONT_SIZE_LG, weight=FONT_WEIGHT_SEMIBOLD),
                'button': tkfont.Font(family=PRIMARY_FONT, size=FONT_SIZE_SM, weight=FONT_WEIGHT_MEDIUM),
                'small': tkfont.Font(family=PRIMARY_FONT, size=FONT_SIZE_SM, weight=FONT_WEIGHT_NORMAL),
                'large': tkfont.Font(family=PRIMARY_FONT, size=FONT_SIZE_LG, weight=FONT_WEIGHT_NORMAL),
                'monospace': tkfont.Font(family=MONOSPACE_FONT, size=FONT_SIZE_SM, weight=FONT_WEIGHT_NORMAL),
            }
        except:
            # Fallback to system fonts
            self.fonts = {
                'primary': tkfont.Font(family="TkDefaultFont", size=FONT_SIZE_MD),
                'heading': tkfont.Font(family="TkDefaultFont", size=FONT_SIZE_LG, weight="bold"),
                'button': tkfont.Font(family="TkDefaultFont", size=FONT_SIZE_SM),
                'small': tkfont.Font(family="TkDefaultFont", size=FONT_SIZE_SM),
                'large': tkfont.Font(family="TkDefaultFont", size=FONT_SIZE_LG),
                'monospace': tkfont.Font(family="TkFixedFont", size=FONT_SIZE_SM),
            }

    def _setup_color_variables(self):
        """Set up Tkinter color variables for dynamic theming."""
        self.color_vars = {
            'primary': tk.StringVar(value=PRIMARY_COLOR),
            'primary_hover': tk.StringVar(value=PRIMARY_HOVER),
            'primary_light': tk.StringVar(value=PRIMARY_LIGHT),
            'secondary': tk.StringVar(value=SECONDARY_COLOR),
            'background': tk.StringVar(value=BACKGROUND_COLOR),
            'surface': tk.StringVar(value=SURFACE_COLOR),
            'text_primary': tk.StringVar(value=TEXT_PRIMARY),
            'text_secondary': tk.StringVar(value=TEXT_SECONDARY),
            'border': tk.StringVar(value=BORDER_COLOR),
        }

    def _configure_styles(self):
        """Configure ttk styles for modern appearance."""
        # Configure root window background
        self.root.configure(bg=BACKGROUND_COLOR)

        # Modern Frame Styles
        self.style.configure(
            'Modern.TFrame',
            background=SURFACE_COLOR,
            borderwidth=BORDER_WIDTH,
            relief='flat'
        )

        self.style.configure(
            'Card.TFrame',
            background=BACKGROUND_COLOR,
            borderwidth=1,
            relief='solid',
            bordercolor=BORDER_COLOR
        )

        # Modern Label Styles
        self.style.configure(
            'Modern.TLabel',
            background=SURFACE_COLOR,
            foreground=TEXT_PRIMARY,
            font=self.fonts['primary']
        )

        self.style.configure(
            'Heading.TLabel',
            background=SURFACE_COLOR,
            foreground=TEXT_PRIMARY,
            font=self.fonts['heading']
        )

        self.style.configure(
            'Secondary.TLabel',
            background=SURFACE_COLOR,
            foreground=TEXT_SECONDARY,
            font=self.fonts['small']
        )

        # Modern Button Styles
        self.style.configure(
            'Modern.TButton',
            background=PRIMARY_COLOR,
            foreground=BACKGROUND_COLOR,
            borderwidth=BORDER_WIDTH,
            relief='flat',
            font=self.fonts['button'],
            padding=(SPACE_3, SPACE_2)
        )

        self.style.map(
            'Modern.TButton',
            background=[('active', PRIMARY_HOVER), ('pressed', PRIMARY_DARK)],
            foreground=[('active', BACKGROUND_COLOR), ('pressed', BACKGROUND_COLOR)]
        )

        # Secondary Button
        self.style.configure(
            'Secondary.TButton',
            background=SURFACE_VARIANT,
            foreground=TEXT_PRIMARY,
            borderwidth=BORDER_WIDTH,
            relief='flat',
            font=self.fonts['button'],
            padding=(SPACE_3, SPACE_2)
        )

        self.style.map(
            'Secondary.TButton',
            background=[('active', SECONDARY_LIGHT), ('pressed', BORDER_COLOR)],
            foreground=[('active', TEXT_PRIMARY), ('pressed', TEXT_SECONDARY)]
        )

        # Success Button
        self.style.configure(
            'Success.TButton',
            background=SUCCESS_COLOR,
            foreground=BACKGROUND_COLOR,
            borderwidth=BORDER_WIDTH,
            relief='flat',
            font=self.fonts['button'],
            padding=(SPACE_3, SPACE_2)
        )

        # Warning Button
        self.style.configure(
            'Warning.TButton',
            background=WARNING_COLOR,
            foreground=BACKGROUND_COLOR,
            borderwidth=BORDER_WIDTH,
            relief='flat',
            font=self.fonts['button'],
            padding=(SPACE_3, SPACE_2)
        )

        # Error Button
        self.style.configure(
            'Error.TButton',
            background=ERROR_COLOR,
            foreground=BACKGROUND_COLOR,
            borderwidth=BORDER_WIDTH,
            relief='flat',
            font=self.fonts['button'],
            padding=(SPACE_3, SPACE_2)
        )

        # Modern Entry Styles
        self.style.configure(
            'Modern.TEntry',
            borderwidth=BORDER_WIDTH,
            relief='flat',
            font=self.fonts['primary'],
            padding=(SPACE_2, SPACE_1)
        )

        # Modern Treeview Styles
        self.style.configure(
            'Modern.Treeview',
            background=BACKGROUND_COLOR,
            foreground=TEXT_PRIMARY,
            fieldbackground=BACKGROUND_COLOR,
            borderwidth=0,
            font=self.fonts['small']
        )

        self.style.configure(
            'Modern.Treeview.Heading',
            background=SURFACE_VARIANT,
            foreground=TEXT_PRIMARY,
            font=self.fonts['small'],
            borderwidth=0,
            relief='flat'
        )

        # Status Bar Style
        self.style.configure(
            'Status.TLabel',
            background=SURFACE_VARIANT,
            foreground=TEXT_SECONDARY,
            font=self.fonts['small'],
            padding=(SPACE_2, SPACE_1)
        )

        # Progress Bar Styles
        self.style.configure(
            'Modern.Horizontal.TProgressbar',
            background=PRIMARY_LIGHT,
            troughcolor=SURFACE_VARIANT,
            borderwidth=0,
            lightcolor=PRIMARY_COLOR,
            darkcolor=PRIMARY_DARK
        )

        # Panel Styles
        self.style.configure(
            'Panel.TLabelframe',
            background=SURFACE_COLOR,
            foreground=TEXT_PRIMARY,
            borderwidth=BORDER_WIDTH,
            bordercolor=BORDER_COLOR,
            font=self.fonts['heading']
        )

        self.style.configure(
            'Panel.TLabelframe.Label',
            background=SURFACE_COLOR,
            foreground=TEXT_PRIMARY,
            font=self.fonts['heading']
        )

    def create_modern_button(self, parent, text: str = "", icon: str = "",
                           style: str = "Modern", **kwargs) -> ttk.Button:
        """
        Create a modern styled button.

        Args:
            parent: Parent widget
            text: Button text
            icon: Icon character (if any)
            style: Button style variant
            **kwargs: Additional button arguments

        Returns:
            Styled button widget
        """
        button_text = f"{icon} {text}".strip() if icon else text

        button = ttk.Button(
            parent,
            text=button_text,
            style=f"{style}.TButton",
            **kwargs
        )

        return button

    def create_modern_label(self, parent, text: str = "", style: str = "Modern",
                           **kwargs) -> ttk.Label:
        """
        Create a modern styled label.

        Args:
            parent: Parent widget
            text: Label text
            style: Label style variant
            **kwargs: Additional label arguments

        Returns:
            Styled label widget
        """
        label = ttk.Label(
            parent,
            text=text,
            style=f"{style}.TLabel",
            **kwargs
        )

        return label

    def create_modern_frame(self, parent, style: str = "Modern", **kwargs) -> ttk.Frame:
        """
        Create a modern styled frame.

        Args:
            parent: Parent widget
            style: Frame style variant
            **kwargs: Additional frame arguments

        Returns:
            Styled frame widget
        """
        frame = ttk.Frame(
            parent,
            style=f"{style}.TFrame",
            **kwargs
        )

        return frame

    def create_card(self, parent, title: str = "", **kwargs) -> ttk.LabelFrame:
        """
        Create a card-style container.

        Args:
            parent: Parent widget
            title: Card title
            **kwargs: Additional arguments

        Returns:
            Styled label frame widget
        """
        card = ttk.LabelFrame(
            parent,
            text=title,
            style="Panel.TLabelframe",
            **kwargs
        )

        return card

    def apply_hover_effect(self, widget, normal_bg: str, hover_bg: str):
        """
        Apply hover effect to a widget.

        Args:
            widget: Widget to apply effect to
            normal_bg: Normal background color
            hover_bg: Hover background color
        """
        def on_enter(event):
            widget.configure(bg=hover_bg)

        def on_leave(event):
            widget.configure(bg=normal_bg)

        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)

    def get_font(self, name: str) -> tkfont.Font:
        """Get a configured font by name."""
        return self.fonts.get(name, self.fonts['primary'])

    def get_color(self, name: str) -> str:
        """Get a color value by name."""
        return self.color_vars.get(name, tk.StringVar()).get()


# Global style instance
_style_instance: Optional[ModernStyle] = None


def get_style_manager(root: tk.Tk = None) -> ModernStyle:
    """Get the global style manager instance."""
    global _style_instance
    if _style_instance is None and root is not None:
        _style_instance = ModernStyle(root)
    return _style_instance


def initialize_styles(root: tk.Tk) -> ModernStyle:
    """Initialize the styling system for the application."""
    global _style_instance
    _style_instance = ModernStyle(root)
    return _style_instance
