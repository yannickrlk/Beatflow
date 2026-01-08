# Configure ffmpeg PATH FIRST before any audio library imports
import os
import warnings
warnings.filterwarnings("ignore", message="Couldn't find ffmpeg")
warnings.filterwarnings("ignore", message="Couldn't find ffprobe")

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
import pygame
from ui.app import BeatflowApp
from core.shortcuts import GlobalShortcutListener


def main():
    # Initialize basic settings
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    # Initialize Audio
    pygame.mixer.init()

    # Parse command line arguments for folder path
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

    # Launch App with optional folder to add
    app = BeatflowApp(folder_to_add=folder_to_add)

    # Initialize global shortcuts listener
    shortcut_listener = GlobalShortcutListener(app, app.player, app.config_manager)
    shortcut_listener.start()

    # Store listener on app for access from settings
    app.shortcut_listener = shortcut_listener

    # Handle cleanup on app close
    def on_closing():
        shortcut_listener.stop()
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_closing)

    app.mainloop()


if __name__ == "__main__":
    main()
