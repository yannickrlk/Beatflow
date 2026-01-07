import sys
import os
import customtkinter as ctk
import pygame
from ui.app import BeatflowApp


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
    app.mainloop()


if __name__ == "__main__":
    main()
