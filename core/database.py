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
                name TEXT,
                is_favorite INTEGER DEFAULT 0
            )
        ''')

        # Create index for faster folder queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_samples_folder
            ON samples(path)
        ''')

        # Migration: Add is_favorite column if it doesn't exist
        cursor.execute("PRAGMA table_info(samples)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'is_favorite' not in columns:
            cursor.execute('ALTER TABLE samples ADD COLUMN is_favorite INTEGER DEFAULT 0')

        # Create collections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create collection_samples junction table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collection_samples (
                collection_id INTEGER NOT NULL,
                sample_path TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (collection_id, sample_path),
                FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
                FOREIGN KEY (sample_path) REFERENCES samples(path) ON DELETE CASCADE
            )
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

    def toggle_favorite(self, path: str) -> bool:
        """
        Toggle the favorite status of a sample.

        Args:
            path: Full path to the audio file.

        Returns:
            New favorite status (True if now favorite, False otherwise).
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get current status
        cursor.execute('SELECT is_favorite FROM samples WHERE path = ?', (path,))
        row = cursor.fetchone()

        if row:
            new_status = 0 if row['is_favorite'] else 1
            cursor.execute('UPDATE samples SET is_favorite = ? WHERE path = ?', (new_status, path))
            conn.commit()
            return new_status == 1

        return False

    def set_favorite(self, path: str, is_favorite: bool):
        """
        Set the favorite status of a sample.

        Args:
            path: Full path to the audio file.
            is_favorite: True to mark as favorite, False to unmark.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE samples SET is_favorite = ? WHERE path = ?', (1 if is_favorite else 0, path))
        conn.commit()

    def get_favorites(self) -> List[Dict]:
        """
        Get all favorite samples.

        Returns:
            List of sample dicts that are marked as favorites.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM samples WHERE is_favorite = 1 ORDER BY filename')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_favorites_count(self) -> int:
        """
        Get the count of favorite samples.

        Returns:
            Number of samples marked as favorites.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM samples WHERE is_favorite = 1')
        return cursor.fetchone()[0]

    def is_favorite(self, path: str) -> bool:
        """
        Check if a sample is marked as favorite.

        Args:
            path: Full path to the audio file.

        Returns:
            True if the sample is a favorite, False otherwise.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT is_favorite FROM samples WHERE path = ?', (path,))
        row = cursor.fetchone()
        return row and row['is_favorite'] == 1

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    # ==================== Collection Methods ====================

    def create_collection(self, name: str) -> Optional[int]:
        """
        Create a new collection.

        Args:
            name: Name of the collection.

        Returns:
            The ID of the created collection, or None if creation failed.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO collections (name) VALUES (?)', (name,))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  # Name already exists

    def get_collections(self) -> List[Dict]:
        """
        Get all collections with their sample counts.

        Returns:
            List of collection dicts with id, name, created_at, and sample_count.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.id, c.name, c.created_at,
                   COUNT(cs.sample_path) as sample_count
            FROM collections c
            LEFT JOIN collection_samples cs ON c.id = cs.collection_id
            GROUP BY c.id
            ORDER BY c.name
        ''')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_collection(self, collection_id: int) -> Optional[Dict]:
        """
        Get a collection by ID.

        Args:
            collection_id: The collection ID.

        Returns:
            Collection dict or None if not found.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM collections WHERE id = ?', (collection_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def rename_collection(self, collection_id: int, new_name: str) -> bool:
        """
        Rename a collection.

        Args:
            collection_id: The collection ID.
            new_name: The new name.

        Returns:
            True if successful, False otherwise.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE collections SET name = ? WHERE id = ?', (new_name, collection_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False  # Name already exists

    def delete_collection(self, collection_id: int) -> bool:
        """
        Delete a collection and all its sample associations.

        Args:
            collection_id: The collection ID.

        Returns:
            True if successful, False otherwise.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        # Delete associations first
        cursor.execute('DELETE FROM collection_samples WHERE collection_id = ?', (collection_id,))
        cursor.execute('DELETE FROM collections WHERE id = ?', (collection_id,))
        conn.commit()
        return cursor.rowcount > 0

    def add_to_collection(self, collection_id: int, sample_path: str) -> bool:
        """
        Add a sample to a collection.

        Args:
            collection_id: The collection ID.
            sample_path: Path to the sample file.

        Returns:
            True if added, False if already exists.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO collection_samples (collection_id, sample_path) VALUES (?, ?)',
                (collection_id, sample_path)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Already in collection

    def remove_from_collection(self, collection_id: int, sample_path: str) -> bool:
        """
        Remove a sample from a collection.

        Args:
            collection_id: The collection ID.
            sample_path: Path to the sample file.

        Returns:
            True if removed, False otherwise.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM collection_samples WHERE collection_id = ? AND sample_path = ?',
            (collection_id, sample_path)
        )
        conn.commit()
        return cursor.rowcount > 0

    def get_collection_samples(self, collection_id: int) -> List[Dict]:
        """
        Get all samples in a collection.

        Args:
            collection_id: The collection ID.

        Returns:
            List of sample dicts.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.* FROM samples s
            JOIN collection_samples cs ON s.path = cs.sample_path
            WHERE cs.collection_id = ?
            ORDER BY cs.added_at DESC
        ''', (collection_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_sample_collections(self, sample_path: str) -> List[Dict]:
        """
        Get all collections that contain a sample.

        Args:
            sample_path: Path to the sample file.

        Returns:
            List of collection dicts.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.* FROM collections c
            JOIN collection_samples cs ON c.id = cs.collection_id
            WHERE cs.sample_path = ?
            ORDER BY c.name
        ''', (sample_path,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def is_in_collection(self, collection_id: int, sample_path: str) -> bool:
        """
        Check if a sample is in a collection.

        Args:
            collection_id: The collection ID.
            sample_path: Path to the sample file.

        Returns:
            True if in collection, False otherwise.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT 1 FROM collection_samples WHERE collection_id = ? AND sample_path = ?',
            (collection_id, sample_path)
        )
        return cursor.fetchone() is not None


# Global database instance (singleton pattern)
_db_instance: Optional[DatabaseManager] = None


def get_database() -> DatabaseManager:
    """Get the global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
