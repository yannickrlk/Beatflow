# Theme and color constants for Beatflow UI
# Cyber-Premium Design System

COLORS = {
    # Backgrounds - Deep blue-black tones
    'bg_darkest': '#0D0D11',      # Sidebar background
    'bg_dark': '#121217',          # Library index (Tree view)
    'bg_main': '#18181E',          # Main Sample List background
    'bg_card': '#1E1E26',          # Sample Row default state
    'bg_hover': '#262632',         # Hover effects on interactive elements
    'bg_input': '#1E1E26',         # Input fields
    'bg_playing': '#22222C',       # Playing state background

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

    # Borders & Dividers
    'border': '#2D2D3A',           # Subtle dividers between rows/sections

    # Status colors
    'success': '#4ade80',          # Green
    'error': '#f87171',            # Red
}

# Typography - Inter preferred, Segoe UI fallback
# Use Consolas/JetBrains Mono for monospaced data (BPM, Key)
FONTS = {
    'primary': 'Inter',            # Primary font (fallback: Segoe UI)
    'mono': 'Consolas',            # Monospaced for BPM/Key data

    'logo': ('Inter', 18, 'bold'),
    'nav': ('Inter', 13),
    'nav_active': ('Inter', 13, 'bold'),
    'header': ('Inter', 11, 'bold'),
    'body': ('Inter', 13),
    'body_bold': ('Inter', 14, 'bold'),
    'small': ('Inter', 11),
    'tiny': ('Inter', 10),
    'mono_data': ('Consolas', 12),  # For BPM/Key values
}

# Spacing constants (8px grid rule)
SPACING = {
    'xs': 4,
    'sm': 8,
    'md': 16,
    'lg': 24,
    'xl': 32,
}
