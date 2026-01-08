"""Beatflow Lab Drawer - Interactive waveform editor with trim, fade, and normalize."""

import os
import tkinter as tk
import threading
from typing import Dict, Callable, Optional

import customtkinter as ctk
from PIL import Image, ImageTk
import numpy as np

from ui.theme import COLORS, SPACING
from core.waveform import generate_waveform_image
from core.lab import get_lab_manager
from core.database import get_database


class LabDrawer(ctk.CTkFrame):
    """Inline drawer for non-destructive sample editing."""

    def __init__(
        self,
        parent,
        sample: Dict,
        on_close: Callable = None,
        on_preview: Callable = None,
        **kwargs
    ):
        super().__init__(parent, fg_color=COLORS['bg_dark'], corner_radius=0, **kwargs)

        self.sample = sample
        self.on_close = on_close
        self.on_preview = on_preview
        self.lab_manager = get_lab_manager()
        self.db = get_database()

        # Get duration
        self.duration_ms = self.lab_manager.get_duration_ms(sample['path'])
        if self.duration_ms <= 0:
            self.duration_ms = 1000  # Fallback

        # Load existing settings or create defaults
        saved_settings = self.db.get_lab_settings(sample['path'])
        if saved_settings:
            self.settings = saved_settings
        else:
            self.settings = {
                'trim_start_ms': 0,
                'trim_end_ms': self.duration_ms,
                'fade_in_ms': 0,
                'fade_out_ms': 0,
                'normalize': False
            }

        # Canvas dimensions
        self.canvas_width = 600
        self.canvas_height = 80

        # Handle dragging state
        self._dragging = None  # 'start', 'end', or None
        self._waveform_image = None
        self._waveform_photo = None

        self._build_ui()
        self._load_waveform()

    def _build_ui(self):
        """Build the drawer UI."""
        # Main container with padding
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=SPACING['md'], pady=SPACING['sm'])

        # Header row with title and close button
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, SPACING['sm']))

        title = ctk.CTkLabel(
            header,
            text="BEATFLOW LAB",
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color=COLORS['accent']
        )
        title.pack(side="left")

        close_btn = ctk.CTkButton(
            header,
            text="X",
            width=24,
            height=24,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            text_color=COLORS['fg_dim'],
            corner_radius=4,
            command=self._on_close
        )
        close_btn.pack(side="right")

        # Waveform canvas
        self.canvas_frame = ctk.CTkFrame(container, fg_color=COLORS['bg_card'], corner_radius=4)
        self.canvas_frame.pack(fill="x", pady=(0, SPACING['sm']))

        self.canvas = tk.Canvas(
            self.canvas_frame,
            width=self.canvas_width,
            height=self.canvas_height,
            bg=COLORS['bg_card'],
            highlightthickness=0
        )
        self.canvas.pack(padx=2, pady=2)

        # Bind mouse events for handle dragging
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

        # Controls row
        controls = ctk.CTkFrame(container, fg_color="transparent")
        controls.pack(fill="x")

        # Left side - Fade controls
        fade_frame = ctk.CTkFrame(controls, fg_color="transparent")
        fade_frame.pack(side="left")

        # Fade In
        fade_in_label = ctk.CTkLabel(
            fade_frame,
            text="Fade In:",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['fg_secondary']
        )
        fade_in_label.pack(side="left", padx=(0, 4))

        self.fade_in_slider = ctk.CTkSlider(
            fade_frame,
            from_=0,
            to=2000,
            width=80,
            height=16,
            button_color=COLORS['accent'],
            button_hover_color=COLORS['accent_hover'],
            progress_color=COLORS['accent_dim'],
            fg_color=COLORS['bg_hover'],
            command=self._on_fade_in_change
        )
        self.fade_in_slider.set(self.settings['fade_in_ms'])
        self.fade_in_slider.pack(side="left", padx=(0, SPACING['md']))

        # Fade Out
        fade_out_label = ctk.CTkLabel(
            fade_frame,
            text="Fade Out:",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['fg_secondary']
        )
        fade_out_label.pack(side="left", padx=(0, 4))

        self.fade_out_slider = ctk.CTkSlider(
            fade_frame,
            from_=0,
            to=2000,
            width=80,
            height=16,
            button_color=COLORS['accent'],
            button_hover_color=COLORS['accent_hover'],
            progress_color=COLORS['accent_dim'],
            fg_color=COLORS['bg_hover'],
            command=self._on_fade_out_change
        )
        self.fade_out_slider.set(self.settings['fade_out_ms'])
        self.fade_out_slider.pack(side="left", padx=(0, SPACING['md']))

        # Center - Normalize toggle
        self.normalize_var = ctk.BooleanVar(value=self.settings['normalize'])
        self.normalize_switch = ctk.CTkSwitch(
            controls,
            text="Normalize",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['fg_secondary'],
            button_color=COLORS['accent'],
            button_hover_color=COLORS['accent_hover'],
            progress_color=COLORS['accent'],
            fg_color=COLORS['bg_hover'],
            variable=self.normalize_var,
            command=self._on_normalize_change
        )
        self.normalize_switch.pack(side="left", padx=SPACING['md'])

        # Right side - Action buttons
        actions = ctk.CTkFrame(controls, fg_color="transparent")
        actions.pack(side="right")

        # Preview button (toggles play/pause)
        self.is_previewing = False
        self.preview_btn = ctk.CTkButton(
            actions,
            text="\u25B6 Preview",
            width=80,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['accent_dim'],
            text_color=COLORS['fg'],
            corner_radius=4,
            command=self._toggle_preview
        )
        self.preview_btn.pack(side="left", padx=(0, SPACING['sm']))

        # Reset button
        reset_btn = ctk.CTkButton(
            actions,
            text="Reset",
            width=60,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            text_color=COLORS['fg_dim'],
            border_width=1,
            border_color=COLORS['border'],
            corner_radius=4,
            command=self._on_reset
        )
        reset_btn.pack(side="left", padx=(0, SPACING['sm']))

        # Export/Drag button
        self.export_btn = ctk.CTkButton(
            actions,
            text="\u2193 Export",
            width=80,
            height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            text_color="#FFFFFF",
            corner_radius=4,
            command=self._on_export
        )
        self.export_btn.pack(side="left")

        # Time labels
        time_frame = ctk.CTkFrame(container, fg_color="transparent")
        time_frame.pack(fill="x", pady=(SPACING['xs'], 0))

        self.start_time_label = ctk.CTkLabel(
            time_frame,
            text=self._format_time(self.settings['trim_start_ms']),
            font=ctk.CTkFont(family="JetBrains Mono", size=10),
            text_color=COLORS['fg_dim']
        )
        self.start_time_label.pack(side="left")

        self.end_time_label = ctk.CTkLabel(
            time_frame,
            text=self._format_time(self.settings['trim_end_ms']),
            font=ctk.CTkFont(family="JetBrains Mono", size=10),
            text_color=COLORS['fg_dim']
        )
        self.end_time_label.pack(side="right")

        # Duration label (trimmed)
        trimmed_duration = self.settings['trim_end_ms'] - self.settings['trim_start_ms']
        self.duration_label = ctk.CTkLabel(
            time_frame,
            text=f"Duration: {self._format_time(trimmed_duration)}",
            font=ctk.CTkFont(family="JetBrains Mono", size=10),
            text_color=COLORS['accent']
        )
        self.duration_label.pack()

    def _load_waveform(self):
        """Load waveform image in background thread."""
        def load():
            try:
                img = generate_waveform_image(
                    self.sample['path'],
                    width=self.canvas_width,
                    height=self.canvas_height,
                    color=COLORS['fg_dim'],
                    bg_color=COLORS['bg_card'],
                    use_cache=False  # Get fresh for lab
                )
                self._waveform_image = img
                self.after(0, self._draw_waveform)
            except Exception:
                pass

        thread = threading.Thread(target=load, daemon=True)
        thread.start()

    def _draw_waveform(self):
        """Draw the waveform and handles on the canvas."""
        if self._waveform_image is None:
            return

        # Clear canvas
        self.canvas.delete("all")

        # Convert PIL image to PhotoImage
        self._waveform_photo = ImageTk.PhotoImage(self._waveform_image)

        # Draw waveform background
        self.canvas.create_image(0, 0, anchor="nw", image=self._waveform_photo)

        # Calculate handle positions
        start_x = int((self.settings['trim_start_ms'] / self.duration_ms) * self.canvas_width)
        end_x = int((self.settings['trim_end_ms'] / self.duration_ms) * self.canvas_width)

        # Draw dimmed regions (before start, after end)
        if start_x > 0:
            self.canvas.create_rectangle(
                0, 0, start_x, self.canvas_height,
                fill=COLORS['bg_darkest'], stipple='gray50', outline=''
            )

        if end_x < self.canvas_width:
            self.canvas.create_rectangle(
                end_x, 0, self.canvas_width, self.canvas_height,
                fill=COLORS['bg_darkest'], stipple='gray50', outline=''
            )

        # Draw fade regions
        fade_in_x = int((self.settings['fade_in_ms'] / self.duration_ms) * self.canvas_width)
        fade_out_x = int((self.settings['fade_out_ms'] / self.duration_ms) * self.canvas_width)

        if fade_in_x > 0:
            # Fade in triangle
            self.canvas.create_polygon(
                start_x, self.canvas_height,
                start_x, 0,
                start_x + fade_in_x, 0,
                fill='', outline=COLORS['accent_secondary'], width=1
            )

        if fade_out_x > 0:
            # Fade out triangle (volume decreases from left to right)
            # Mirror of fade in: top-left corner to bottom-right
            self.canvas.create_polygon(
                end_x - fade_out_x, 0,         # Top left (full volume)
                end_x, 0,                       # Top right
                end_x, self.canvas_height,     # Bottom right (zero volume)
                fill='', outline=COLORS['accent_secondary'], width=1
            )

        # Draw trim handles
        handle_width = 4

        # Start handle (green)
        self.canvas.create_rectangle(
            start_x - handle_width // 2, 0,
            start_x + handle_width // 2, self.canvas_height,
            fill=COLORS['success'], outline=''
        )
        self.canvas.create_text(
            start_x, 8,
            text="[",
            font=("JetBrains Mono", 10, "bold"),
            fill=COLORS['success']
        )

        # End handle (red)
        self.canvas.create_rectangle(
            end_x - handle_width // 2, 0,
            end_x + handle_width // 2, self.canvas_height,
            fill=COLORS['error'], outline=''
        )
        self.canvas.create_text(
            end_x, 8,
            text="]",
            font=("JetBrains Mono", 10, "bold"),
            fill=COLORS['error']
        )

    def _on_canvas_click(self, event):
        """Handle canvas click to select a handle."""
        start_x = int((self.settings['trim_start_ms'] / self.duration_ms) * self.canvas_width)
        end_x = int((self.settings['trim_end_ms'] / self.duration_ms) * self.canvas_width)

        # Check if clicking near start handle (within 10px)
        if abs(event.x - start_x) < 10:
            self._dragging = 'start'
        # Check if clicking near end handle
        elif abs(event.x - end_x) < 10:
            self._dragging = 'end'
        else:
            self._dragging = None

    def _on_canvas_drag(self, event):
        """Handle canvas drag to move handles."""
        if self._dragging is None:
            return

        # Constrain x to canvas bounds
        x = max(0, min(event.x, self.canvas_width))

        # Convert x to time
        time_ms = int((x / self.canvas_width) * self.duration_ms)

        if self._dragging == 'start':
            # Constrain start to not exceed end
            time_ms = min(time_ms, self.settings['trim_end_ms'] - 100)
            time_ms = max(0, time_ms)
            self.settings['trim_start_ms'] = time_ms
            self.start_time_label.configure(text=self._format_time(time_ms))

        elif self._dragging == 'end':
            # Constrain end to not go before start
            time_ms = max(time_ms, self.settings['trim_start_ms'] + 100)
            time_ms = min(self.duration_ms, time_ms)
            self.settings['trim_end_ms'] = time_ms
            self.end_time_label.configure(text=self._format_time(time_ms))

        # Update duration label
        trimmed_duration = self.settings['trim_end_ms'] - self.settings['trim_start_ms']
        self.duration_label.configure(text=f"Duration: {self._format_time(trimmed_duration)}")

        # Redraw handles (not full waveform for performance)
        self._draw_waveform()

    def _on_canvas_release(self, event):
        """Handle mouse release - save settings."""
        if self._dragging is not None:
            self._save_settings()
        self._dragging = None

    def _on_fade_in_change(self, value):
        """Handle fade in slider change."""
        self.settings['fade_in_ms'] = int(value)
        self._draw_waveform()
        self._save_settings()

    def _on_fade_out_change(self, value):
        """Handle fade out slider change."""
        self.settings['fade_out_ms'] = int(value)
        self._draw_waveform()
        self._save_settings()

    def _on_normalize_change(self):
        """Handle normalize toggle change."""
        self.settings['normalize'] = self.normalize_var.get()
        self._save_settings()

    def _on_reset(self):
        """Reset settings to defaults."""
        self.settings = {
            'trim_start_ms': 0,
            'trim_end_ms': self.duration_ms,
            'fade_in_ms': 0,
            'fade_out_ms': 0,
            'normalize': False
        }

        # Update UI
        self.fade_in_slider.set(0)
        self.fade_out_slider.set(0)
        self.normalize_var.set(False)
        self.start_time_label.configure(text=self._format_time(0))
        self.end_time_label.configure(text=self._format_time(self.duration_ms))
        self.duration_label.configure(text=f"Duration: {self._format_time(self.duration_ms)}")

        self._draw_waveform()
        self._save_settings()

    def _toggle_preview(self):
        """Toggle preview playback."""
        if self.is_previewing:
            self._stop_preview()
        else:
            self._start_preview()

    def _start_preview(self):
        """Start preview playback."""
        temp_path = self.lab_manager.export_temp(self.sample['path'], self.settings)
        if temp_path and self.on_preview:
            self.is_previewing = True
            self.preview_btn.configure(
                text="\u23F8 Stop",
                fg_color=COLORS['accent'],
                text_color="#FFFFFF"
            )
            self.on_preview(temp_path)

    def _stop_preview(self):
        """Stop preview playback."""
        import pygame
        pygame.mixer.music.stop()
        self.is_previewing = False
        self.preview_btn.configure(
            text="\u25B6 Preview",
            fg_color=COLORS['bg_hover'],
            text_color=COLORS['fg']
        )

    def set_preview_stopped(self):
        """Called when preview playback ends naturally."""
        self.is_previewing = False
        try:
            self.preview_btn.configure(
                text="\u25B6 Preview",
                fg_color=COLORS['bg_hover'],
                text_color=COLORS['fg']
            )
        except Exception:
            pass  # Widget may be destroyed

    def _on_export(self):
        """Export the edited sample."""
        from tkinter import filedialog
        import soundfile as sf

        # Get default filename
        base_name = os.path.splitext(self.sample['filename'])[0]
        default_name = f"{base_name}_edited.wav"

        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")],
            initialfile=default_name,
            title="Export Edited Sample"
        )

        if file_path:
            # Apply edits and export
            result = self.lab_manager.apply_edits(self.sample['path'], self.settings)
            if result:
                y, sr = result
                # Transpose for soundfile (expects samples x channels)
                audio_data = y.T if y.ndim > 1 else y
                sf.write(file_path, audio_data, sr)
                print(f"Exported to: {file_path}")

    def _on_close(self):
        """Handle close button click."""
        self._save_settings()
        if self.on_close:
            self.on_close()

    def _save_settings(self):
        """Save current settings to database."""
        self.db.save_lab_settings(self.sample['path'], self.settings)

    def _format_time(self, ms: int) -> str:
        """Format milliseconds as MM:SS.mmm"""
        seconds = ms // 1000
        millis = ms % 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}.{millis:03d}"

    def get_settings(self) -> Dict:
        """Get current settings."""
        return self.settings.copy()
