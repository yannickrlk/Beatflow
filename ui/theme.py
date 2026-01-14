# Theme and color constants for ProducerOS UI
# Cyber-Premium Design System - Professional DAW-like appearance

import os
import sys
import customtkinter as ctk

# =============================================================================
# FONT LOADING
# =============================================================================

def _get_assets_path():
    """Get the path to the assets directory."""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.join(os.path.dirname(sys.executable), 'assets')
    else:
        # Running in development
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')

def _load_fonts():
    """Load custom fonts if available, otherwise use system fallbacks."""
    fonts_dir = os.path.join(_get_assets_path(), 'fonts')
    loaded = {'inter': False, 'jetbrains': False}

    # Try to load Inter font family
    inter_regular = os.path.join(fonts_dir, 'Inter-Regular.ttf')
    if os.path.exists(inter_regular):
        try:
            ctk.FontManager.load_font(inter_regular)
            loaded['inter'] = True
        except Exception:
            pass

    inter_medium = os.path.join(fonts_dir, 'Inter-Medium.ttf')
    if os.path.exists(inter_medium):
        try:
            ctk.FontManager.load_font(inter_medium)
        except Exception:
            pass

    inter_bold = os.path.join(fonts_dir, 'Inter-Bold.ttf')
    if os.path.exists(inter_bold):
        try:
            ctk.FontManager.load_font(inter_bold)
        except Exception:
            pass

    # Try to load JetBrains Mono font family
    jb_regular = os.path.join(fonts_dir, 'JetBrainsMono-Regular.ttf')
    if os.path.exists(jb_regular):
        try:
            ctk.FontManager.load_font(jb_regular)
            loaded['jetbrains'] = True
        except Exception:
            pass

    jb_medium = os.path.join(fonts_dir, 'JetBrainsMono-Medium.ttf')
    if os.path.exists(jb_medium):
        try:
            ctk.FontManager.load_font(jb_medium)
        except Exception:
            pass

    return loaded

# Load fonts on module import
_FONTS_LOADED = _load_fonts()

# =============================================================================
# FONT FAMILIES - With fallback chain
# =============================================================================

# Primary font with platform-specific fallbacks
if _FONTS_LOADED.get('inter'):
    FONT_PRIMARY = 'Inter'
elif sys.platform == 'darwin':
    FONT_PRIMARY = 'SF Pro Display'
elif sys.platform == 'win32':
    FONT_PRIMARY = 'Segoe UI'
else:
    FONT_PRIMARY = 'Cantarell'

# Monospace font with platform-specific fallbacks
if _FONTS_LOADED.get('jetbrains'):
    FONT_MONO = 'JetBrains Mono'
elif sys.platform == 'darwin':
    FONT_MONO = 'SF Mono'
elif sys.platform == 'win32':
    FONT_MONO = 'Consolas'
else:
    FONT_MONO = 'monospace'

# =============================================================================
# COLORS - Deep blue-black tones for professional DAW-like appearance
# =============================================================================

COLORS = {
    # Backgrounds - Deep blue-black tones
    'bg_darkest': '#0D0D11',      # Sidebar background
    'bg_dark': '#121217',          # Library index (Tree view)
    'bg_main': '#18181E',          # Main Sample List background
    'bg_card': '#1E1E26',          # Sample Row default state
    'bg_hover': '#262632',         # Hover effects on interactive elements
    'bg_input': '#1E1E26',         # Input fields
    'bg_playing': '#22222C',       # Playing state background

    # Row striping for dense lists
    'bg_stripe': '#1A1A22',        # Alternate row background (slightly different from bg_main)

    # Accent colors
    'accent': '#FF6100',           # Primary buttons, play icons, focus states
    'accent_hover': '#FF7A1A',     # Orange hover
    'accent_dim': '#CC4E00',       # Dimmed orange
    'accent_overlay': '#4D2810',   # Waveform progress overlay (SoundCloud-style)
    'accent_secondary': '#8B5CF6', # Detected metadata (BPM/Key), Analysis buttons

    # Foreground / Text
    'fg': '#FFFFFF',               # Primary text
    'fg_secondary': '#A0A0B0',     # Muted descriptions (BPM/Key labels)
    'fg_dim': '#606070',           # Secondary metadata (Bitrate, Format, Path)
    'fg_muted': '#404050',         # Very dim text

    # Borders & Dividers - Key for pro look
    'border': '#2D2D3A',           # Subtle dividers between rows/sections
    'border_subtle': '#232330',    # Very subtle borders

    # Status colors
    'success': '#4ade80',          # Green
    'error': '#f87171',            # Red
    'warning': '#fbbf24',          # Amber
}

# =============================================================================
# TYPOGRAPHY - Using loaded fonts with fallbacks
# =============================================================================

FONTS = {
    'primary': FONT_PRIMARY,       # Primary font
    'mono': FONT_MONO,             # Monospaced for data

    'logo': (FONT_PRIMARY, 18, 'bold'),
    'nav': (FONT_PRIMARY, 12),               # Slightly smaller for density
    'nav_active': (FONT_PRIMARY, 12, 'bold'),
    'header': (FONT_PRIMARY, 11, 'bold'),    # Section headers
    'body': (FONT_PRIMARY, 12),              # Default body text
    'body_bold': (FONT_PRIMARY, 12, 'bold'),
    'small': (FONT_PRIMARY, 11),             # Secondary info
    'tiny': (FONT_PRIMARY, 10),              # Very small text
    'mono_data': (FONT_MONO, 11),            # BPM/Key values - slightly smaller for density
}

# =============================================================================
# SPACING - Compact 4px grid for professional density
# =============================================================================

SPACING = {
    'xs': 2,     # Minimal gaps (was 4)
    'sm': 4,     # Small gaps (was 8)
    'md': 8,     # Medium gaps (was 16)
    'lg': 12,    # Large gaps (was 24)
    'xl': 16,    # Extra large (was 32)

    # Specific layout values
    'row_padding': 4,      # Vertical padding inside list rows
    'row_gap': 1,          # Gap between rows
    'section_gap': 8,      # Gap between sections
    'panel_padding': 8,    # Padding inside panels
}

# =============================================================================
# SIZING - Consistent component sizes
# =============================================================================

SIZING = {
    # Row heights
    'row_height': 32,          # Compact row height for lists
    'row_height_detail': 48,   # Row with more info (waveform, etc.)

    # Sidebar
    'sidebar_width': 200,
    'sidebar_item_height': 32,

    # Tree view
    'tree_item_height': 24,
    'tree_indent': 16,

    # Buttons
    'button_height': 28,
    'button_height_sm': 24,
    'icon_button_size': 24,

    # Borders
    'border_width': 1,
    'border_radius': 4,
    'border_radius_sm': 2,
}
