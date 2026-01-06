"""SQLite database manager for caching sample metadata."""

import os
import sqlite3
from typing import Dict, Optional, List


class DatabaseManager:
    """Manages SQLite database for caching scanned sample metadata."""

    def __init__(self, db_path: str = None):
        """
        Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file. If None, uses default location.
        """
        if db_path is None:
            # Default to beatflow.db in the project root
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'beatflow.db'
            )
        self.db_path = db_path
        self._conn = None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False  # Allow sharing across threads
            )
            self._conn.row_factory = sqlite3.Row  # Enable dict-like access
        return self._conn

    def _init_db(self):
        """Initialize the database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create samples table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS samples (
                path TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                mtime REAL,
                size INTEGER,
                title TEXT,
                artist TEXT,
                album TEXT,
                genre TEXT,
                year TEXT,
                bpm TEXT,
                key TEXT,
                duration REAL,
                bitrate INTEGER,
                sample_rate INTEGER,
                name TEXT
            )
        ''')

        # Create index for faster folder queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_samples_folder
            ON samples(path)
        ''')

        conn.commit()

    def get_sample(self, path: str) -> Optional[Dict]:
        """
        Get a sample from the cache by path.

        Args:
            path: Full path to the audio file.

        Returns:
            Sample dict or None if not found.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM samples WHERE path = ?', (path,))
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None

    def get_sample_if_valid(self, path: str, mtime: float, size: int) -> Optional[Dict]:
        """
        Get a sample from cache only if it's still valid (not modified).

        Args:
            path: Full path to the audio file.
            mtime: Current file modification time.
            size: Current file size.

        Returns:
            Sample dict if cache hit and valid, None otherwise.
        """
        sample = self.get_sample(path)
        if sample and sample.get('mtime') == mtime and sample.get('size') == size:
            return sample
        return None

    def upsert_sample(self, sample: Dict):
        """
        Insert or update a sample in the cache.

        Args:
            sample: Sample dict with metadata.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO samples
            (path, filename, mtime, size, title, artist, album, genre, year,
             bpm, key, duration, bitrate, sample_rate, name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            sample.get('path', ''),
            sample.get('filename', ''),
            sample.get('mtime', 0),
            sample.get('size', 0),
            sample.get('title', ''),
            sample.get('artist', ''),
            sample.get('album', ''),
            sample.get('genre', ''),
            sample.get('year', ''),
            sample.get('bpm', ''),
            sample.get('key', ''),
            sample.get('duration', 0),
            sample.get('bitrate', 0),
            sample.get('sample_rate', 0),
            sample.get('name', '')
        ))

        conn.commit()

    def upsert_samples(self, samples: List[Dict]):
        """
        Bulk insert or update samples in the cache.

        Args:
            samples: List of sample dicts.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        data = [
            (
                s.get('path', ''),
                s.get('filename', ''),
                s.get('mtime', 0),
                s.get('size', 0),
                s.get('title', ''),
                s.get('artist', ''),
                s.get('album', ''),
                s.get('genre', ''),
                s.get('year', ''),
                s.get('bpm', ''),
                s.get('key', ''),
                s.get('duration', 0),
                s.get('bitrate', 0),
                s.get('sample_rate', 0),
                s.get('name', '')
            )
            for s in samples
        ]

        cursor.executemany('''
            INSERT OR REPLACE INTO samples
            (path, filename, mtime, size, title, artist, album, genre, year,
             bpm, key, duration, bitrate, sample_rate, name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)

        conn.commit()

    def remove_sample(self, path: str):
        """
        Remove a sample from the cache.

        Args:
            path: Full path to the audio file.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM samples WHERE path = ?', (path,))
        conn.commit()

    def clear_all(self):
        """Clear all samples from the cache."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM samples')
        conn.commit()

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


# Global database instance (singleton pattern)
_db_instance: Optional[DatabaseManager] = None


def get_database() -> DatabaseManager:
    """Get the global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
