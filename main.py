import customtkinter as ctk
import pygame
from ui.app import BeatflowApp

def main():
    # Initialize basic settings
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    
    # Initialize Audio
    pygame.mixer.init()
    
    # Launch App
    app = BeatflowApp()
    app.mainloop()

if __name__ == "__main__":
    main()
