"""Global keyboard shortcuts for Beatflow.

Listens for configurable keyboard shortcuts system-wide
and dispatches commands to the FooterPlayer.
"""

from pynput import keyboard


# Default shortcut configuration
DEFAULT_SHORTCUTS = {
    'play_pause': {'key': 'space', 'modifiers': ['ctrl']},
    'next_track': {'key': 'right', 'modifiers': ['ctrl']},
    'prev_track': {'key': 'left', 'modifiers': ['ctrl']},
}

# Key name to pynput Key mapping
SPECIAL_KEYS = {
    'space': keyboard.Key.space,
    'left': keyboard.Key.left,
    'right': keyboard.Key.right,
    'up': keyboard.Key.up,
    'down': keyboard.Key.down,
    'enter': keyboard.Key.enter,
    'tab': keyboard.Key.tab,
    'f1': keyboard.Key.f1,
    'f2': keyboard.Key.f2,
    'f3': keyboard.Key.f3,
    'f4': keyboard.Key.f4,
    'f5': keyboard.Key.f5,
    'f6': keyboard.Key.f6,
    'f7': keyboard.Key.f7,
    'f8': keyboard.Key.f8,
    'f9': keyboard.Key.f9,
    'f10': keyboard.Key.f10,
    'f11': keyboard.Key.f11,
    'f12': keyboard.Key.f12,
    'media_play_pause': keyboard.Key.media_play_pause,
    'media_next': keyboard.Key.media_next,
    'media_previous': keyboard.Key.media_previous,
}


class GlobalShortcutListener:
    """Listens for global keyboard events and controls the player."""

    def __init__(self, app, player, config_manager=None):
        """Initialize the global shortcut listener.

        Args:
            app: The main BeatflowApp instance (for thread-safe UI updates).
            player: The FooterPlayer instance to control.
            config_manager: ConfigManager for loading/saving shortcut settings.
        """
        self.app = app
        self.player = player
        self.config_manager = config_manager
        self.listener = None

        # Current modifier state
        self._ctrl_pressed = False
        self._alt_pressed = False
        self._shift_pressed = False

        # Load shortcuts from config or use defaults
        self.shortcuts = self._load_shortcuts()

    def _load_shortcuts(self) -> dict:
        """Load shortcuts from config or return defaults."""
        if self.config_manager:
            return self.config_manager.config.get('shortcuts', DEFAULT_SHORTCUTS.copy())
        return DEFAULT_SHORTCUTS.copy()

    def save_shortcuts(self, shortcuts: dict):
        """Save shortcuts to config."""
        self.shortcuts = shortcuts
        if self.config_manager:
            self.config_manager.config['shortcuts'] = shortcuts
            self.config_manager.save()

    def _check_modifiers(self, required_modifiers: list) -> bool:
        """Check if the required modifiers are pressed."""
        ctrl_required = 'ctrl' in required_modifiers
        alt_required = 'alt' in required_modifiers
        shift_required = 'shift' in required_modifiers

        return (self._ctrl_pressed == ctrl_required and
                self._alt_pressed == alt_required and
                self._shift_pressed == shift_required)

    def _key_matches(self, pressed_key, shortcut_key: str) -> bool:
        """Check if the pressed key matches the shortcut key."""
        # Check if it's a special key
        if shortcut_key in SPECIAL_KEYS:
            return pressed_key == SPECIAL_KEYS[shortcut_key]

        # Check for regular character keys
        try:
            if hasattr(pressed_key, 'char') and pressed_key.char:
                return pressed_key.char.lower() == shortcut_key.lower()
        except AttributeError:
            pass

        return False

    def _on_press(self, key):
        """Handle key press events."""
        # Track modifier state
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self._ctrl_pressed = True
            return
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r or key == keyboard.Key.alt_gr:
            self._alt_pressed = True
            return
        if key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
            self._shift_pressed = True
            return

        # Check shortcuts
        for action, shortcut in self.shortcuts.items():
            shortcut_key = shortcut.get('key', '')
            modifiers = shortcut.get('modifiers', [])

            if self._key_matches(key, shortcut_key) and self._check_modifiers(modifiers):
                if action == 'play_pause':
                    self.app.after(0, self.player.toggle_play_pause)
                elif action == 'next_track':
                    self.app.after(0, self.player._on_next)
                elif action == 'prev_track':
                    self.app.after(0, self.player._on_prev)
                return

    def _on_release(self, key):
        """Handle key release events."""
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self._ctrl_pressed = False
        elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r or key == keyboard.Key.alt_gr:
            self._alt_pressed = False
        elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
            self._shift_pressed = False

    def start(self):
        """Start the global keyboard listener (non-blocking)."""
        if self.listener is not None:
            return  # Already running

        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()

    def stop(self):
        """Stop the global keyboard listener."""
        if self.listener is not None:
            self.listener.stop()
            self.listener = None

    def reload_shortcuts(self):
        """Reload shortcuts from config."""
        self.shortcuts = self._load_shortcuts()

    @staticmethod
    def format_shortcut(shortcut: dict) -> str:
        """Format a shortcut dict to a display string."""
        modifiers = shortcut.get('modifiers', [])
        key = shortcut.get('key', '')

        parts = []
        if 'ctrl' in modifiers:
            parts.append('Ctrl')
        if 'alt' in modifiers:
            parts.append('Alt')
        if 'shift' in modifiers:
            parts.append('Shift')

        # Capitalize key for display
        key_display = key.capitalize() if key else ''
        if key_display:
            parts.append(key_display)

        return ' + '.join(parts)

    @staticmethod
    def parse_shortcut(shortcut_str: str) -> dict:
        """Parse a shortcut string to a dict."""
        parts = [p.strip().lower() for p in shortcut_str.split('+')]

        modifiers = []
        key = ''

        for part in parts:
            if part == 'ctrl':
                modifiers.append('ctrl')
            elif part == 'alt':
                modifiers.append('alt')
            elif part == 'shift':
                modifiers.append('shift')
            else:
                key = part

        return {'key': key, 'modifiers': modifiers}
