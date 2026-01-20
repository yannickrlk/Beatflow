# Configure ffmpeg PATH FIRST before any audio library imports
import os
import warnings
warnings.filterwarnings("ignore", message="Couldn't find ffmpeg")
warnings.filterwarnings("ignore", message="Couldn't find ffprobe")

# STARTUP OPTIMIZATION: Defer heavy ffmpeg/pydub imports until actually needed
# These are only required for audio format conversion, not basic playback
def _configure_ffmpeg():
    """Configure ffmpeg path lazily when needed."""
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_path)
        os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
        # Also configure pydub directly
        from pydub import AudioSegment
        AudioSegment.converter = ffmpeg_path
    except ImportError:
        pass

import sys
import customtkinter as ctk


def main():
    # Initialize basic settings
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    # Parse command line arguments for folder path (fast - no heavy imports)
    folder_to_add = None
    if len(sys.argv) > 1:
        arg_path = sys.argv[1]
        # Handle quoted paths and normalize
        if arg_path.startswith('"') and arg_path.endswith('"'):
            arg_path = arg_path[1:-1]
        arg_path = os.path.normpath(arg_path)

        # Validate it's a directory
        if os.path.isdir(arg_path):
            folder_to_add = arg_path

    # Import app module (deferred to keep module-level imports minimal)
    from ui.app import ProducerOSApp

    # Launch App with optional folder to add
    app = ProducerOSApp(folder_to_add=folder_to_add)

    # STARTUP OPTIMIZATION: Defer heavy initializations until after window is shown
    def _deferred_init():
        """Initialize heavy components after UI is visible."""
        # Initialize pygame mixer (blocking operation)
        import pygame
        pygame.mixer.init()
        app.player._pygame_ready = True

        # Configure ffmpeg (only needed for format conversion)
        _configure_ffmpeg()

        # Initialize global shortcuts listener (imports pynput which is slow)
        from core.shortcuts import GlobalShortcutListener
        shortcut_listener = GlobalShortcutListener(app, app.player, app.config_manager)
        shortcut_listener.start()

        # Store listener on app for access from settings
        app.shortcut_listener = shortcut_listener

    # Schedule deferred init after window is drawn (100ms delay)
    app.after(100, _deferred_init)

    # Handle cleanup on app close
    def on_closing():
        if hasattr(app, 'shortcut_listener') and app.shortcut_listener:
            app.shortcut_listener.stop()
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_closing)

    app.mainloop()


if __name__ == "__main__":
    main()
