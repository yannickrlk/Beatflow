"""Configuration management for ProducerOS."""

import os
import json
from pathlib import Path


class ConfigManager:
    """Handles loading and saving application configuration."""

    DEFAULT_CONFIG = {
        'root_folders': [],
        'volume': 0.7,
        'sort_by': 'name',  # name, bpm, key, duration
        'sort_order': 'asc'  # asc, desc
    }

    def __init__(self, config_path: str = None):
        """
        Initialize the ConfigManager.

        Args:
            config_path: Path to the config file. If None, uses default location.
        """
        if config_path is None:
            # Default to produceros_config.json in the project root
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'produceros_config.json'
            )
        self.config_path = config_path
        self._config = None

    @property
    def config(self) -> dict:
        """Get the current configuration, loading if necessary."""
        if self._config is None:
            self.load()
        return self._config

    def load(self) -> dict:
        """Load configuration from file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._config = self.DEFAULT_CONFIG.copy()
        else:
            self._config = self.DEFAULT_CONFIG.copy()
        return self._config

    def save(self) -> bool:
        """
        Save current configuration to file.

        Returns:
            True if save was successful, False otherwise.
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2)
            return True
        except IOError:
            return False

    @property
    def root_folders(self) -> list:
        """Get the list of root folders."""
        return self.config.get('root_folders', [])

    def add_folder(self, folder_path: str) -> bool:
        """
        Add a folder to the root folders list.

        Args:
            folder_path: Path to the folder to add.

        Returns:
            True if folder was added, False if already exists.
        """
        folder_path = os.path.normpath(folder_path)
        if folder_path not in self.root_folders:
            self.config['root_folders'].append(folder_path)
            self.save()
            return True
        return False

    def remove_folder(self, folder_path: str) -> bool:
        """
        Remove a folder from the root folders list.

        Args:
            folder_path: Path to the folder to remove.

        Returns:
            True if folder was removed, False if not found.
        """
        folder_path = os.path.normpath(folder_path)
        if folder_path in self.root_folders:
            self.config['root_folders'].remove(folder_path)
            self.save()
            return True
        return False

    @property
    def volume(self) -> float:
        """Get the saved volume level (0.0 to 1.0)."""
        return self.config.get('volume', 0.7)

    def set_volume(self, volume: float):
        """Save volume level to config."""
        self.config['volume'] = max(0.0, min(1.0, volume))
        self.save()

    @property
    def sort_by(self) -> str:
        """Get the current sort field."""
        return self.config.get('sort_by', 'name')

    @property
    def sort_order(self) -> str:
        """Get the current sort order (asc/desc)."""
        return self.config.get('sort_order', 'asc')

    def set_sort(self, sort_by: str, sort_order: str):
        """Save sort preferences to config."""
        self.config['sort_by'] = sort_by
        self.config['sort_order'] = sort_order
        self.save()
