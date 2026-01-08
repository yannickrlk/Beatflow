"""Global Footer Player component for Beatflow."""

import os
import time
import customtkinter as ctk
import pygame
from typing import Optional, List, Dict, Callable
from ui.theme import COLORS
from core.sync import get_sync_manager


class FooterPlayer(ctk.CTkFrame):
    """Global audio player footer with playback controls."""

    def __init__(self, parent, on_volume_change: Callable[[float], None] = None,
                 on_progress: Callable[[float], None] = None, **kwargs):
        super().__init__(parent, height=100, fg_color=COLORS['bg_darkest'], corner_radius=0, **kwargs)
        self.pack_propagate(False)
        self.grid_propagate(False)

        # Callbacks
        self.on_volume_change = on_volume_change
        self.on_progress = on_progress  # Called with progress 0.0-1.0

        # Playback state
        self.current_sample: Optional[Dict] = None
        self.playlist: List[Dict] = []
        self.playlist_index: int = -1
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.duration: float = 0  # in seconds
        self.position_offset: float = 0  # Track position offset for seeks
        self.volume: float = 0.7
        self._is_seeking: bool = False  # Flag to prevent feedback loop
        self._last_get_pos: int = 0  # Track last get_pos value to detect resets
        self._seek_target: float = 0  # Target position after seek
        self._seek_time: float = 0  # Time when last seek occurred
        self._get_pos_at_seek: int = 0  # get_pos() value when seek occurred

        # UI update timer
        self._update_job = None

        # Sync engine state
        self.sync_manager = get_sync_manager()
        self.sync_enabled = False
        self.target_bpm = 120
        self._synced_file_path: Optional[str] = None  # Path to currently playing synced file

        # Tap tempo state
        self._tap_times: List[float] = []
        self._tap_timeout = 2.0  # Reset taps after 2 seconds

        # Metronome state
        self.metronome_enabled = False
        self._metronome_job = None
        self._metronome_beat = 0
        self._metronome_sound = None
        self._init_metronome_sound()

        self._build_ui()

    def _build_ui(self):
        """Build the player UI."""
        # Use grid layout for precise control
        self.grid_columnconfigure(0, weight=0, minsize=200)  # Track info
        self.grid_columnconfigure(1, weight=1)               # Center (controls + progress)
        self.grid_columnconfigure(2, weight=0, minsize=220)  # Sync controls
        self.grid_columnconfigure(3, weight=0, minsize=130)  # Volume
        self.grid_rowconfigure(0, weight=1)

        # Left section: Track info
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="nsw", padx=(20, 10), pady=10)

        self.track_name = ctk.CTkLabel(
            info_frame,
            text="No track selected",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS['fg'],
            anchor="w"
        )
        self.track_name.pack(fill="x", pady=(5, 2))

        self.track_info = ctk.CTkLabel(
            info_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['fg_dim'],
            anchor="w"
        )
        self.track_info.pack(fill="x")

        # Center section: Controls + Progress
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=5)

        # Control buttons row
        controls_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        controls_frame.pack(pady=(5, 5))

        # Previous button
        self.prev_btn = ctk.CTkButton(
            controls_frame,
            text="\u23ee",
            width=32,
            height=32,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            text_color=COLORS['fg_secondary'],
            corner_radius=16,
            command=self._on_prev
        )
        self.prev_btn.pack(side="left", padx=4)

        # Play/Pause button
        self.play_btn = ctk.CTkButton(
            controls_frame,
            text="\u25b6",
            width=40,
            height=40,
            font=ctk.CTkFont(size=16),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            text_color="#ffffff",
            corner_radius=20,
            command=self._on_play_pause
        )
        self.play_btn.pack(side="left", padx=8)

        # Next button
        self.next_btn = ctk.CTkButton(
            controls_frame,
            text="\u23ed",
            width=32,
            height=32,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            hover_color=COLORS['bg_hover'],
            text_color=COLORS['fg_secondary'],
            corner_radius=16,
            command=self._on_next
        )
        self.next_btn.pack(side="left", padx=4)

        # Progress bar row
        progress_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        progress_frame.pack(fill="x", expand=True, pady=(0, 5))

        # Current time
        self.time_current = ctk.CTkLabel(
            progress_frame,
            text="0:00",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['fg_secondary'],
            width=40
        )
        self.time_current.pack(side="left")

        # Seek slider
        self.seek_slider = ctk.CTkSlider(
            progress_frame,
            from_=0,
            to=100,
            number_of_steps=200,
            height=12,
            fg_color=COLORS['bg_hover'],
            progress_color=COLORS['accent'],
            button_color=COLORS['fg'],
            button_hover_color=COLORS['accent'],
            command=self._on_seek_drag
        )
        self.seek_slider.set(0)
        self.seek_slider.pack(side="left", fill="x", expand=True, padx=8)

        # Bind mouse events for better seek control
        self.seek_slider.bind("<ButtonPress-1>", self._on_seek_start)
        self.seek_slider.bind("<ButtonRelease-1>", self._on_seek_end)

        # Total time
        self.time_total = ctk.CTkLabel(
            progress_frame,
            text="0:00",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['fg_secondary'],
            width=40
        )
        self.time_total.pack(side="left")

        # Sync section: BPM controls, Tap, Metronome, Sync toggle
        sync_frame = ctk.CTkFrame(self, fg_color="transparent")
        sync_frame.grid(row=0, column=2, sticky="ns", padx=10, pady=10)

        sync_row = ctk.CTkFrame(sync_frame, fg_color="transparent")
        sync_row.pack(expand=True)

        # BPM Entry
        bpm_label = ctk.CTkLabel(
            sync_row,
            text="BPM",
            font=ctk.CTkFont(size=10),
            text_color=COLORS['fg_dim']
        )
        bpm_label.pack(side="left", padx=(0, 4))

        self.bpm_entry = ctk.CTkEntry(
            sync_row,
            width=50,
            height=28,
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            fg_color=COLORS['bg_card'],
            border_color=COLORS['border'],
            text_color=COLORS['fg'],
            justify="center"
        )
        self.bpm_entry.insert(0, str(self.target_bpm))
        self.bpm_entry.bind("<Return>", self._on_bpm_change)
        self.bpm_entry.bind("<FocusOut>", self._on_bpm_change)
        self.bpm_entry.pack(side="left", padx=(0, 4))

        # Tap Tempo button
        self.tap_btn = ctk.CTkButton(
            sync_row,
            text="TAP",
            width=40,
            height=28,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['bg_card'],
            text_color=COLORS['fg_secondary'],
            corner_radius=4,
            command=self._on_tap_tempo
        )
        self.tap_btn.pack(side="left", padx=(0, 8))

        # Metronome toggle
        self.metronome_btn = ctk.CTkButton(
            sync_row,
            text="\U0001F3B5",  # Musical note
            width=28,
            height=28,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['bg_card'],
            text_color=COLORS['fg_dim'],
            corner_radius=4,
            command=self._toggle_metronome
        )
        self.metronome_btn.pack(side="left", padx=(0, 8))

        # Sync toggle button
        self.sync_btn = ctk.CTkButton(
            sync_row,
            text="SYNC",
            width=50,
            height=28,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=COLORS['bg_hover'],
            hover_color=COLORS['accent_dim'],
            text_color=COLORS['fg_dim'],
            corner_radius=4,
            command=self._toggle_sync
        )
        self.sync_btn.pack(side="left")

        # Right section: Volume
        volume_frame = ctk.CTkFrame(self, fg_color="transparent")
        volume_frame.grid(row=0, column=3, sticky="nse", padx=(10, 20), pady=10)

        volume_row = ctk.CTkFrame(volume_frame, fg_color="transparent")
        volume_row.pack(expand=True, pady=15)

        # Volume icon
        self.volume_icon = ctk.CTkLabel(
            volume_row,
            text="\U0001f50a",
            font=ctk.CTkFont(size=14),
            text_color=COLORS['fg_secondary']
        )
        self.volume_icon.pack(side="left", padx=(0, 8))

        # Volume slider
        self.volume_slider = ctk.CTkSlider(
            volume_row,
            from_=0,
            to=100,
            number_of_steps=100,
            width=100,
            height=12,
            fg_color=COLORS['bg_hover'],
            progress_color=COLORS['fg_secondary'],
            button_color=COLORS['fg'],
            button_hover_color=COLORS['accent'],
            command=self._on_volume
        )
        self.volume_slider.set(int(self.volume * 100))
        self.volume_slider.pack(side="left")

    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        self.volume_slider.set(int(self.volume * 100))
        pygame.mixer.music.set_volume(self.volume)
        self._update_volume_icon()

    def _update_volume_icon(self):
        """Update volume icon based on level."""
        if self.volume == 0:
            self.volume_icon.configure(text="\U0001f507")  # Muted
        elif self.volume < 0.5:
            self.volume_icon.configure(text="\U0001f509")  # Low
        else:
            self.volume_icon.configure(text="\U0001f50a")  # High

    def load_track(self, sample: Dict, playlist: List[Dict] = None, index: int = 0):
        """Load a track for playback."""
        # Stop current playback when loading a new track
        if self.is_playing or self.is_paused:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False
            self._stop_ui_update()

        self.current_sample = sample
        if playlist:
            self.playlist = playlist
            self.playlist_index = index
        else:
            self.playlist = [sample]
            self.playlist_index = 0

        # Get duration - prefer metadata duration, fallback to detection
        self.duration = sample.get('duration', 0) or self._get_duration(sample['path'])

        # Update UI - track name (prefer title, fallback to filename)
        display_name = sample.get('title') or sample.get('filename', 'Unknown')
        self.track_name.configure(text=display_name)

        # Update UI - info line with Artist, BPM, Key, Duration
        info_parts = []

        # Artist
        if sample.get('artist'):
            info_parts.append(sample['artist'])

        # BPM (prefer embedded, fallback to detected)
        bpm = sample.get('bpm') or sample.get('detected_bpm')
        if bpm:
            info_parts.append(f"{bpm} BPM")

        # Key (prefer embedded, fallback to detected)
        key = sample.get('key') or sample.get('detected_key')
        if key:
            info_parts.append(key)

        # Duration
        if self.duration > 0:
            info_parts.append(self._format_time(self.duration))

        self.track_info.configure(text=" • ".join(info_parts) if info_parts else "")

        # Update seek bar total time
        self.time_total.configure(text=self._format_time(self.duration))

        # Reset position tracking
        self.position_offset = 0
        self._last_get_pos = 0
        self.seek_slider.set(0)
        self.time_current.configure(text="0:00")

    def _get_duration(self, file_path: str) -> float:
        """Get audio duration in seconds."""
        ext = os.path.splitext(file_path)[1].lower()

        # Method 1: Try tinytag (works for MP3, FLAC, OGG, WAV, etc.)
        try:
            from tinytag import TinyTag
            tag = TinyTag.get(file_path)
            if tag.duration and tag.duration > 0:
                return tag.duration
        except Exception:
            pass

        # Method 2: Try pygame.mixer.Sound (reliable for WAV)
        if ext == '.wav':
            try:
                sound = pygame.mixer.Sound(file_path)
                return sound.get_length()
            except Exception:
                pass

        # Method 3: Try pydub as fallback (needs ffmpeg)
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(file_path)
            return len(audio) / 1000.0
        except Exception:
            pass

        return 0

    def play(self):
        """Start or resume playback."""
        if not self.current_sample:
            return

        try:
            if self.is_paused:
                pygame.mixer.music.unpause()
            else:
                # Get file path - use synced version if sync is enabled
                file_path = self._get_synced_file(self.current_sample)
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play()
                self.position_offset = 0
                self._get_pos_at_seek = 0  # Reset seek reference point

            self.is_playing = True
            self.is_paused = False
            self.play_btn.configure(text="\u23f8")  # Pause icon
            self._start_ui_update()
        except Exception as e:
            print(f"Playback error: {e}")

    def pause(self):
        """Pause playback."""
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.is_playing = False
            self.play_btn.configure(text="\u25b6")  # Play icon
            self._stop_ui_update()

    def stop(self):
        """Stop playback."""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.position_offset = 0
        self.play_btn.configure(text="\u25b6")
        self.seek_slider.set(0)
        self.time_current.configure(text="0:00")
        self._stop_ui_update()

    def toggle_play_pause(self):
        """Toggle between play and pause."""
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def _on_play_pause(self):
        """Handle play/pause button click."""
        self.toggle_play_pause()

    def _on_prev(self):
        """Handle previous button click."""
        if not self.playlist or self.playlist_index <= 0:
            # Restart current track
            if self.current_sample:
                self.stop()
                self.play()
            return

        self.playlist_index -= 1
        self.load_track(self.playlist[self.playlist_index], self.playlist, self.playlist_index)
        self.play()

    def _on_next(self):
        """Handle next button click."""
        if not self.playlist or self.playlist_index >= len(self.playlist) - 1:
            self.stop()
            return

        self.playlist_index += 1
        self.load_track(self.playlist[self.playlist_index], self.playlist, self.playlist_index)
        self.play()

    def _on_seek_start(self, event=None):
        """Handle seek slider mouse press - pause updates."""
        self._is_seeking = True

    def _on_seek_end(self, event=None):
        """Handle seek slider mouse release - perform actual seek."""
        self._is_seeking = False
        self._perform_seek(self.seek_slider.get())

    def _on_seek_drag(self, value):
        """Handle seek slider drag - update time display only."""
        if not self.current_sample or self.duration <= 0:
            return
        # Update time display while dragging
        target_pos = (value / 100) * self.duration
        self.time_current.configure(text=self._format_time(target_pos))

    def seek(self, percentage: float):
        """
        Public method to seek to a position.

        Args:
            percentage: Position as 0.0-1.0 (or 0-100 for compatibility)
        """
        # Normalize to 0-100 range for internal use
        if percentage <= 1.0:
            percentage = percentage * 100
        self._perform_seek(percentage)

    def _perform_seek(self, value):
        """Perform the actual seek operation."""
        if not self.current_sample or self.duration <= 0:
            return

        # Calculate target position
        target_pos = (value / 100) * self.duration
        ext = os.path.splitext(self.current_sample['path'])[1].lower()

        # Record seek time and target for UI update handling
        self._seek_time = time.time()
        self._seek_target = target_pos
        # Record current get_pos before seeking (to calculate delta later)
        self._get_pos_at_seek = pygame.mixer.music.get_pos()

        try:
            # For MP3/OGG, use set_pos which works better
            if ext in ['.mp3', '.ogg']:
                if self.is_playing or self.is_paused:
                    pygame.mixer.music.set_pos(target_pos)
                    self.position_offset = target_pos
                else:
                    # Not playing, start from position
                    pygame.mixer.music.play(start=target_pos)
                    pygame.mixer.music.set_volume(self.volume)
                    self.position_offset = target_pos
                    self._get_pos_at_seek = 0  # Reset since we called play()
                    self.is_playing = True
                    self.play_btn.configure(text="\u23f8")
                    self._start_ui_update()
            else:
                # For WAV and others, restart with start position
                pygame.mixer.music.play(start=target_pos)
                pygame.mixer.music.set_volume(self.volume)
                self.position_offset = target_pos
                self._get_pos_at_seek = 0  # Reset since we called play()
                if not self.is_playing and not self.is_paused:
                    self.is_playing = True
                    self.play_btn.configure(text="\u23f8")
                    self._start_ui_update()
                elif self.is_paused:
                    pygame.mixer.music.pause()

            # Update UI immediately with target position
            self.time_current.configure(text=self._format_time(target_pos))
            self.seek_slider.set(value)
        except Exception as e:
            print(f"Seek error: {e}")

    def _on_volume(self, value):
        """Handle volume slider change."""
        self.volume = value / 100
        pygame.mixer.music.set_volume(self.volume)
        self._update_volume_icon()

        if self.on_volume_change:
            self.on_volume_change(self.volume)

    def _start_ui_update(self):
        """Start periodic UI updates."""
        self._update_ui()

    def _stop_ui_update(self):
        """Stop periodic UI updates."""
        if self._update_job:
            self.after_cancel(self._update_job)
            self._update_job = None

    def _update_ui(self):
        """Update UI elements (position, slider)."""
        if self.is_playing and self.duration > 0:
            # Skip UI updates while user is seeking
            if self._is_seeking:
                self._update_job = self.after(100, self._update_ui)
                return

            # Check if we recently seeked - use target position for 500ms after seek
            time_since_seek = time.time() - self._seek_time
            if time_since_seek < 0.5:
                # Use the seek target position to prevent slider jumping back
                current_pos = self._seek_target + time_since_seek
                current_pos = min(current_pos, self.duration)
                progress = min(100, (current_pos / self.duration) * 100)
                self.seek_slider.set(progress)
                self.time_current.configure(text=self._format_time(current_pos))
                # Notify progress callback
                if self.on_progress:
                    self.on_progress(progress / 100)  # 0.0-1.0
                self._update_job = self.after(100, self._update_ui)
                return

            # Get position from pygame (milliseconds since play started)
            pos_ms = pygame.mixer.music.get_pos()
            if pos_ms >= 0:
                # Calculate position using delta from seek point
                # This handles the fact that get_pos() doesn't reset after set_pos()
                delta_ms = pos_ms - self._get_pos_at_seek
                current_pos = self.position_offset + (delta_ms / 1000)

                # Clamp to duration
                current_pos = min(current_pos, self.duration)

                # Check if track ended
                if not pygame.mixer.music.get_busy():
                    self._on_track_end()
                    return

                # Update slider and time
                progress = min(100, (current_pos / self.duration) * 100)
                self.seek_slider.set(progress)
                self.time_current.configure(text=self._format_time(current_pos))

                # Notify progress callback
                if self.on_progress:
                    self.on_progress(progress / 100)  # 0.0-1.0

        # Schedule next update
        self._update_job = self.after(100, self._update_ui)

    def _on_track_end(self):
        """Handle track ending."""
        # Auto-play next track
        if self.playlist_index < len(self.playlist) - 1:
            self._on_next()
        else:
            self.stop()

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds as M:SS."""
        if seconds < 0:
            seconds = 0
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"

    # ========== Sync Engine Methods ==========

    def _init_metronome_sound(self):
        """Initialize metronome click sound."""
        try:
            import numpy as np
            import io
            import wave

            # Generate a short click sound (10ms sine wave at 1000Hz)
            sample_rate = 44100
            duration = 0.01  # 10ms
            frequency = 1000
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            click = np.sin(2 * np.pi * frequency * t)

            # Apply envelope for clean click
            envelope = np.exp(-t * 50)
            click = (click * envelope * 0.5 * 32767).astype(np.int16)

            # Create WAV in memory
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                wav.writeframes(click.tobytes())

            buffer.seek(0)
            self._metronome_sound = pygame.mixer.Sound(buffer)
            self._metronome_sound.set_volume(0.5)
        except Exception as e:
            print(f"Failed to init metronome sound: {e}")
            self._metronome_sound = None

    def _on_bpm_change(self, event=None):
        """Handle BPM entry change."""
        try:
            value = int(self.bpm_entry.get())
            # Clamp to reasonable range
            value = max(40, min(240, value))
            self.target_bpm = value
            self.bpm_entry.delete(0, "end")
            self.bpm_entry.insert(0, str(value))

            # If sync is enabled and a track is playing, reload with new tempo
            if self.sync_enabled and self.is_playing and self.current_sample:
                # Stop current and restart with new sync
                was_playing = self.is_playing
                self.stop()
                if was_playing:
                    self.play()
        except ValueError:
            # Reset to current value
            self.bpm_entry.delete(0, "end")
            self.bpm_entry.insert(0, str(self.target_bpm))

    def _on_tap_tempo(self):
        """Handle tap tempo button click."""
        current_time = time.time()

        # Reset if too much time has passed since last tap
        if self._tap_times and (current_time - self._tap_times[-1]) > self._tap_timeout:
            self._tap_times = []

        self._tap_times.append(current_time)

        # Need at least 2 taps to calculate BPM
        if len(self._tap_times) >= 2:
            # Calculate average interval between taps
            intervals = [
                self._tap_times[i] - self._tap_times[i - 1]
                for i in range(1, len(self._tap_times))
            ]
            avg_interval = sum(intervals) / len(intervals)

            # Convert to BPM
            if avg_interval > 0:
                bpm = int(60 / avg_interval)
                bpm = max(40, min(240, bpm))
                self.target_bpm = bpm
                self.bpm_entry.delete(0, "end")
                self.bpm_entry.insert(0, str(bpm))

        # Keep only last 8 taps
        if len(self._tap_times) > 8:
            self._tap_times = self._tap_times[-8:]

        # Visual feedback
        self.tap_btn.configure(fg_color=COLORS['accent'])
        self.after(100, lambda: self.tap_btn.configure(fg_color=COLORS['bg_hover']))

    def _toggle_metronome(self):
        """Toggle metronome on/off."""
        self.metronome_enabled = not self.metronome_enabled

        if self.metronome_enabled:
            self.metronome_btn.configure(
                fg_color=COLORS['accent'],
                text_color="#FFFFFF"
            )
            self._start_metronome()
        else:
            self.metronome_btn.configure(
                fg_color=COLORS['bg_hover'],
                text_color=COLORS['fg_dim']
            )
            self._stop_metronome()

    def _start_metronome(self):
        """Start metronome ticking."""
        if not self.metronome_enabled:
            return

        # Play tick
        if self._metronome_sound:
            self._metronome_sound.play()

        # Pulse the BPM entry background
        self._metronome_beat = (self._metronome_beat + 1) % 4
        if self._metronome_beat == 0:
            # Downbeat - stronger pulse
            self.bpm_entry.configure(border_color=COLORS['accent'])
        else:
            self.bpm_entry.configure(border_color=COLORS['fg_dim'])

        # Reset border after short delay
        self.after(50, lambda: self.bpm_entry.configure(border_color=COLORS['border']))

        # Calculate interval from BPM
        interval_ms = int(60000 / self.target_bpm)

        # Schedule next tick
        self._metronome_job = self.after(interval_ms, self._start_metronome)

    def _stop_metronome(self):
        """Stop metronome ticking."""
        if self._metronome_job:
            self.after_cancel(self._metronome_job)
            self._metronome_job = None
        self._metronome_beat = 0
        self.bpm_entry.configure(border_color=COLORS['border'])

    def _toggle_sync(self):
        """Toggle sync mode on/off."""
        self.sync_enabled = not self.sync_enabled

        if self.sync_enabled:
            self.sync_btn.configure(
                fg_color=COLORS['accent'],
                text_color="#FFFFFF"
            )
        else:
            self.sync_btn.configure(
                fg_color=COLORS['bg_hover'],
                text_color=COLORS['fg_dim']
            )
            self._synced_file_path = None

        # If a track is loaded, reload it with/without sync
        if self.current_sample:
            was_playing = self.is_playing
            was_paused = self.is_paused
            current_pos = self._get_current_position()

            # Reload the track with new sync setting
            self._reload_with_sync()

            # Resume from similar position if was playing
            if was_playing or was_paused:
                if current_pos > 0:
                    self.seek(current_pos / self.duration * 100)
                if was_playing:
                    self.play()

    def _reload_with_sync(self):
        """Reload current track with or without sync."""
        if not self.current_sample:
            return

        try:
            # Get the appropriate file path
            file_path = self._get_synced_file(self.current_sample)

            # Stop current playback
            pygame.mixer.music.stop()

            # Load new file
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(self.volume)

            self.is_playing = False
            self.is_paused = False
            self.position_offset = 0
            self._get_pos_at_seek = 0
        except Exception:
            pass

    def _get_current_position(self) -> float:
        """Get current playback position in seconds."""
        if not self.is_playing and not self.is_paused:
            return 0
        pos_ms = pygame.mixer.music.get_pos()
        if pos_ms < 0:
            return 0
        delta_ms = pos_ms - self._get_pos_at_seek
        return self.position_offset + (delta_ms / 1000)

    def _get_sample_bpm(self, sample: Dict) -> float:
        """Get BPM from sample metadata."""
        # Try embedded BPM first, then detected
        bpm_str = sample.get('bpm') or sample.get('detected_bpm') or ''
        try:
            # Handle "≈120" format from detected BPM
            bpm_str = bpm_str.replace('≈', '').strip()
            return float(bpm_str)
        except (ValueError, AttributeError):
            return 0

    def _get_synced_file(self, sample: Dict) -> str:
        """Get path to synced (time-stretched) file if sync is enabled."""
        if not self.sync_enabled:
            return sample['path']

        original_bpm = self._get_sample_bpm(sample)
        if original_bpm <= 0:
            return sample['path']

        # Check if sync manager is available
        if not self.sync_manager.is_available():
            return sample['path']

        # Process the file
        synced_path = self.sync_manager.process_for_sync(
            sample['path'],
            original_bpm,
            self.target_bpm
        )

        if synced_path:
            self._synced_file_path = synced_path
            return synced_path
        else:
            return sample['path']

    def set_target_bpm(self, bpm: int):
        """Set the target BPM programmatically."""
        bpm = max(40, min(240, bpm))
        self.target_bpm = bpm
        self.bpm_entry.delete(0, "end")
        self.bpm_entry.insert(0, str(bpm))

    def is_sync_active(self) -> bool:
        """Check if sync mode is currently active."""
        return self.sync_enabled
