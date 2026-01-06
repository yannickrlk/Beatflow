"""Sample card component for displaying individual samples."""

import os
from typing import Dict, Callable, Optional
import customtkinter as ctk


class SampleCard(ctk.CTkFrame):
    """A card widget displaying sample information with playback controls."""

    def __init__(
        self,
        parent,
        sample: Dict,
        colors: Dict[str, str],
        on_play: Callable[[Dict, ctk.CTkButton], None],
        **kwargs
    ):
        """
        Initialize a SampleCard.

        Args:
            parent: Parent widget.
            sample: Sample info dictionary with keys: name, bpm, key, path, filename, tags.
            colors: Color scheme dictionary.
            on_play: Callback function called when play button is clicked.
        """
        super().__init__(
            parent,
            fg_color=colors['bg_card'],
            corner_radius=12,
            height=80,
            **kwargs
        )
        self.pack_propagate(False)

        self.sample = sample
        self.colors = colors
        self.on_play = on_play

        self._build_ui()

    def _build_ui(self):
        """Build the card UI."""
        # Play button
        self.play_btn = ctk.CTkButton(
            self,
            text="\u25b6",
            width=50,
            height=50,
            font=ctk.CTkFont(size=18),
            fg_color=self.colors['bg_hover'],
            hover_color=self.colors['accent'],
            corner_radius=25,
            command=self._handle_play
        )
        self.play_btn.pack(side="left", padx=(16, 12), pady=15)

        # Info section
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, pady=12)

        # Top row: name + format badge
        top_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        top_row.pack(fill="x")

        name_label = ctk.CTkLabel(
            top_row,
            text=self.sample['name'],
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors['fg']
        )
        name_label.pack(side="left")

        # Format badge
        ext = os.path.splitext(self.sample['filename'])[1].upper()[1:]
        format_badge = ctk.CTkLabel(
            top_row,
            text=f" {ext} ",
            font=ctk.CTkFont(size=10),
            fg_color=self.colors['bg_hover'],
            corner_radius=4,
            text_color=self.colors['fg_dim']
        )
        format_badge.pack(side="left", padx=(10, 0))

        # Bottom row: metadata
        bottom_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        bottom_row.pack(fill="x", pady=(6, 0))

        # BPM
        if self.sample.get('bpm'):
            bpm_label = ctk.CTkLabel(
                bottom_row,
                text=f"\u266a {self.sample['bpm']} BPM",
                font=ctk.CTkFont(size=12),
                text_color=self.colors['fg_secondary']
            )
            bpm_label.pack(side="left", padx=(0, 16))

        # Key
        if self.sample.get('key'):
            key_label = ctk.CTkLabel(
                bottom_row,
                text=f"\u25c6 {self.sample['key']}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=self.colors['accent']
            )
            key_label.pack(side="left", padx=(0, 16))

        # Tags
        tags = self.sample.get('tags', [])
        for tag in tags[:3]:
            tag_label = ctk.CTkLabel(
                bottom_row,
                text=f"#{tag}",
                font=ctk.CTkFont(size=11),
                text_color=self.colors['fg_dim']
            )
            tag_label.pack(side="left", padx=(0, 8))

        # Waveform placeholder
        waveform = ctk.CTkLabel(
            self,
            text="\u2581\u2582\u2583\u2585\u2587\u2585\u2583\u2582\u2581\u2582\u2584\u2586\u2587\u2586\u2584\u2582",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=self.colors['fg_dim']
        )
        waveform.pack(side="right", padx=20)

    def _handle_play(self):
        """Handle play button click."""
        self.on_play(self.sample, self.play_btn)

    def set_playing(self, is_playing: bool):
        """
        Update the visual state to reflect playback status.

        Args:
            is_playing: True if this sample is currently playing.
        """
        if is_playing:
            self.play_btn.configure(text="\u23f8", fg_color=self.colors['accent'])
        else:
            self.play_btn.configure(text="\u25b6", fg_color=self.colors['bg_hover'])
