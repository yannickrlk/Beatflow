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
                is_favorite INTEGER DEFAULT 0,
                detected_bpm TEXT,
                detected_key TEXT,
                analysis_date REAL
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

        # Migration: Add audio analysis columns if they don't exist
        if 'detected_bpm' not in columns:
            cursor.execute('ALTER TABLE samples ADD COLUMN detected_bpm TEXT')
        if 'detected_key' not in columns:
            cursor.execute('ALTER TABLE samples ADD COLUMN detected_key TEXT')
        if 'analysis_date' not in columns:
            cursor.execute('ALTER TABLE samples ADD COLUMN analysis_date REAL')

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

        # Create recent_samples table for tracking recently played
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recent_samples (
                sample_path TEXT PRIMARY KEY,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sample_path) REFERENCES samples(path) ON DELETE CASCADE
            )
        ''')

        # Create fingerprints table for sonic similarity matching
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fingerprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sample_path TEXT NOT NULL,
                hash_value INTEGER NOT NULL,
                time_offset INTEGER NOT NULL,
                FOREIGN KEY (sample_path) REFERENCES samples(path) ON DELETE CASCADE
            )
        ''')

        # Create indexes for fast fingerprint lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_fingerprints_hash
            ON fingerprints(hash_value)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_fingerprints_path
            ON fingerprints(sample_path)
        ''')

        # Create lab_settings table for Beatflow Lab edits
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lab_settings (
                sample_path TEXT PRIMARY KEY,
                settings TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sample_path) REFERENCES samples(path) ON DELETE CASCADE
            )
        ''')

        # Create tagging_rules table for Metadata Architect
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tagging_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                condition_type TEXT NOT NULL,
                condition_field TEXT NOT NULL,
                condition_operator TEXT NOT NULL,
                condition_value TEXT NOT NULL,
                tags_to_add TEXT NOT NULL,
                is_enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create sample_tags table for custom tags
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sample_tags (
                sample_path TEXT NOT NULL,
                tag TEXT NOT NULL,
                source TEXT DEFAULT 'manual',
                PRIMARY KEY (sample_path, tag),
                FOREIGN KEY (sample_path) REFERENCES samples(path) ON DELETE CASCADE
            )
        ''')

        # Create index for tag queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sample_tags_tag
            ON sample_tags(tag)
        ''')

        # Create rename_history table for undo support
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rename_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_path TEXT NOT NULL,
                new_path TEXT NOT NULL,
                renamed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    # ==================== Folder Statistics Methods ====================

    def get_folder_sample_count(self, folder_path: str, recursive: bool = True) -> int:
        """
        Get count of cached samples in a folder.

        Args:
            folder_path: Path to the folder.
            recursive: If True, include samples from all subfolders.

        Returns:
            Number of cached samples in the folder (and subfolders if recursive).
        """
        import os
        conn = self._get_connection()
        cursor = conn.cursor()

        # Use OS-native path separator for matching
        sep = os.sep

        if recursive:
            # Count all samples where path starts with folder_path + separator
            pattern = folder_path + sep + '%'
            cursor.execute(
                'SELECT COUNT(*) FROM samples WHERE path LIKE ?',
                (pattern,)
            )
        else:
            # Count only direct children (samples in this folder, not subfolders)
            # Match folder_path\filename but not folder_path\subfolder\filename
            pattern = folder_path + sep + '%'
            exclude_pattern = folder_path + sep + '%' + sep + '%'
            cursor.execute('''
                SELECT COUNT(*) FROM samples
                WHERE path LIKE ?
                AND path NOT LIKE ?
            ''', (pattern, exclude_pattern))

        return cursor.fetchone()[0]

    # ==================== Global Search Methods ====================

    def search_samples(self, query: str, limit: int = 500) -> List[Dict]:
        """
        Search for samples across the entire library.

        Args:
            query: Search query string.
            limit: Maximum number of results to return.

        Returns:
            List of sample dicts matching the query.
        """
        if not query or not query.strip():
            return []

        conn = self._get_connection()
        cursor = conn.cursor()

        # Prepare search pattern
        search_pattern = f'%{query.strip()}%'

        # Search across multiple fields
        cursor.execute('''
            SELECT * FROM samples
            WHERE filename LIKE ?
               OR title LIKE ?
               OR artist LIKE ?
               OR album LIKE ?
               OR genre LIKE ?
               OR name LIKE ?
               OR bpm LIKE ?
               OR key LIKE ?
               OR detected_bpm LIKE ?
               OR detected_key LIKE ?
            ORDER BY filename ASC
            LIMIT ?
        ''', (search_pattern,) * 10 + (limit,))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ==================== Audio Analysis Methods ====================

    def update_analysis(self, path: str, detected_bpm: str, detected_key: str):
        """
        Update the analysis results for a sample.

        Args:
            path: Full path to the audio file.
            detected_bpm: Detected BPM value.
            detected_key: Detected musical key.
        """
        import time
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE samples
            SET detected_bpm = ?, detected_key = ?, analysis_date = ?
            WHERE path = ?
        ''', (detected_bpm, detected_key, time.time(), path))
        conn.commit()

    def get_analysis(self, path: str) -> Optional[Dict]:
        """
        Get the analysis results for a sample.

        Args:
            path: Full path to the audio file.

        Returns:
            Dict with detected_bpm, detected_key, analysis_date or None.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT detected_bpm, detected_key, analysis_date
            FROM samples WHERE path = ?
        ''', (path,))
        row = cursor.fetchone()
        if row and row['analysis_date']:
            return {
                'detected_bpm': row['detected_bpm'],
                'detected_key': row['detected_key'],
                'analysis_date': row['analysis_date']
            }
        return None

    def get_samples_needing_analysis(self, folder_path: str = None) -> List[Dict]:
        """
        Get samples that have no BPM/Key and haven't been analyzed.

        Args:
            folder_path: Optional folder to filter by (prefix match).

        Returns:
            List of sample dicts needing analysis.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if folder_path:
            cursor.execute('''
                SELECT * FROM samples
                WHERE path LIKE ?
                AND (bpm = '' OR bpm IS NULL)
                AND (key = '' OR key IS NULL)
                AND analysis_date IS NULL
            ''', (folder_path + '%',))
        else:
            cursor.execute('''
                SELECT * FROM samples
                WHERE (bpm = '' OR bpm IS NULL)
                AND (key = '' OR key IS NULL)
                AND analysis_date IS NULL
            ''')

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def clear_analysis(self, path: str):
        """
        Clear analysis results for a sample (to allow re-analysis).

        Args:
            path: Full path to the audio file.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE samples
            SET detected_bpm = NULL, detected_key = NULL, analysis_date = NULL
            WHERE path = ?
        ''', (path,))
        conn.commit()

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

    # ==================== Recent Samples Methods ====================

    def add_to_recent(self, sample_path: str, max_recent: int = 50):
        """
        Add a sample to the recently played list.

        Args:
            sample_path: Path to the sample file.
            max_recent: Maximum number of recent samples to keep.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Insert or update the played timestamp
        cursor.execute('''
            INSERT OR REPLACE INTO recent_samples (sample_path, played_at)
            VALUES (?, CURRENT_TIMESTAMP)
        ''', (sample_path,))

        # Trim old entries to keep only max_recent
        cursor.execute('''
            DELETE FROM recent_samples
            WHERE sample_path NOT IN (
                SELECT sample_path FROM recent_samples
                ORDER BY played_at DESC
                LIMIT ?
            )
        ''', (max_recent,))

        conn.commit()

    def get_recent_samples(self, limit: int = 50) -> List[Dict]:
        """
        Get recently played samples.

        Args:
            limit: Maximum number of samples to return.

        Returns:
            List of sample dicts, most recent first.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.* FROM samples s
            JOIN recent_samples r ON s.path = r.sample_path
            ORDER BY r.played_at DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_recent_count(self) -> int:
        """
        Get the count of recently played samples.

        Returns:
            Number of samples in recent list.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM recent_samples')
        return cursor.fetchone()[0]

    def clear_recent(self):
        """Clear all recently played samples."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM recent_samples')
        conn.commit()

    # ==================== Fingerprint Methods ====================

    def save_fingerprints(self, sample_path: str, hashes: List[tuple]):
        """
        Save fingerprint hashes for a sample.

        Args:
            sample_path: Path to the audio file.
            hashes: List of (hash_value, time_offset) tuples.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Delete existing fingerprints for this sample
        cursor.execute('DELETE FROM fingerprints WHERE sample_path = ?', (sample_path,))

        # Bulk insert new fingerprints
        if hashes:
            data = [(sample_path, h[0], h[1]) for h in hashes]
            cursor.executemany(
                'INSERT INTO fingerprints (sample_path, hash_value, time_offset) VALUES (?, ?, ?)',
                data
            )

        conn.commit()

    def get_fingerprints(self, sample_path: str) -> List[tuple]:
        """
        Get fingerprint hashes for a sample.

        Args:
            sample_path: Path to the audio file.

        Returns:
            List of (hash_value, time_offset) tuples.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT hash_value, time_offset FROM fingerprints WHERE sample_path = ?',
            (sample_path,)
        )
        return [(row[0], row[1]) for row in cursor.fetchall()]

    def has_fingerprint(self, sample_path: str) -> bool:
        """
        Check if a sample has fingerprints stored.

        Args:
            sample_path: Path to the audio file.

        Returns:
            True if fingerprints exist, False otherwise.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT 1 FROM fingerprints WHERE sample_path = ? LIMIT 1',
            (sample_path,)
        )
        return cursor.fetchone() is not None

    def find_similar_samples(self, query_hashes: List[tuple], exclude_path: str = None, limit: int = 25) -> List[tuple]:
        """
        Find samples with similar fingerprints.

        Uses time-aligned hash matching for accuracy.

        Args:
            query_hashes: List of (hash_value, time_offset) from query sample.
            exclude_path: Path to exclude from results (usually the query sample).
            limit: Maximum number of results.

        Returns:
            List of (sample_path, match_score) tuples, sorted by score descending.
        """
        if not query_hashes:
            return []

        conn = self._get_connection()
        cursor = conn.cursor()

        # Build hash lookup for query
        query_hash_set = {h[0] for h in query_hashes}
        query_hash_times = {h[0]: h[1] for h in query_hashes}

        # Find all samples that share hashes with the query
        placeholders = ','.join(['?' for _ in query_hash_set])
        query_sql = f'''
            SELECT DISTINCT sample_path FROM fingerprints
            WHERE hash_value IN ({placeholders})
        '''
        if exclude_path:
            query_sql += ' AND sample_path != ?'
            cursor.execute(query_sql, list(query_hash_set) + [exclude_path])
        else:
            cursor.execute(query_sql, list(query_hash_set))

        candidate_paths = [row[0] for row in cursor.fetchall()]

        # Score each candidate
        results = []
        for path in candidate_paths:
            # Get matching hashes for this candidate
            cursor.execute('''
                SELECT hash_value, time_offset FROM fingerprints
                WHERE sample_path = ? AND hash_value IN ({})
            '''.format(placeholders), [path] + list(query_hash_set))

            matches = []
            for row in cursor.fetchall():
                hash_val, offset = row
                if hash_val in query_hash_times:
                    query_time = query_hash_times[hash_val]
                    time_diff = offset - query_time
                    matches.append(time_diff)

            if not matches:
                continue

            # Count time-aligned matches (most common time difference)
            time_diff_counts = {}
            for td in matches:
                td_quantized = td // 5 * 5
                time_diff_counts[td_quantized] = time_diff_counts.get(td_quantized, 0) + 1

            best_count = max(time_diff_counts.values()) if time_diff_counts else 0

            # Calculate similarity score (0-100)
            score = min(100, (best_count / len(query_hashes)) * 500)

            if score > 5:
                results.append((path, score))

        # Sort by score and limit
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def get_samples_without_fingerprints(self, limit: int = 100) -> List[Dict]:
        """
        Get samples that don't have fingerprints yet.

        Args:
            limit: Maximum number of samples to return.

        Returns:
            List of sample dicts.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.* FROM samples s
            LEFT JOIN fingerprints f ON s.path = f.sample_path
            WHERE f.id IS NULL
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def clear_fingerprints(self, sample_path: str = None):
        """
        Clear fingerprints for a sample or all samples.

        Args:
            sample_path: Path to clear fingerprints for, or None for all.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        if sample_path:
            cursor.execute('DELETE FROM fingerprints WHERE sample_path = ?', (sample_path,))
        else:
            cursor.execute('DELETE FROM fingerprints')
        conn.commit()

    # ==================== Lab Settings Methods ====================

    def save_lab_settings(self, sample_path: str, settings: Dict):
        """
        Save Lab settings for a sample.

        Args:
            sample_path: Path to the audio file.
            settings: Dictionary with lab edit settings.
        """
        import json
        conn = self._get_connection()
        cursor = conn.cursor()
        settings_json = json.dumps(settings)
        cursor.execute('''
            INSERT OR REPLACE INTO lab_settings (sample_path, settings, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (sample_path, settings_json))
        conn.commit()

    def get_lab_settings(self, sample_path: str) -> Optional[Dict]:
        """
        Get Lab settings for a sample.

        Args:
            sample_path: Path to the audio file.

        Returns:
            Settings dictionary, or None if not found.
        """
        import json
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT settings FROM lab_settings WHERE sample_path = ?',
            (sample_path,)
        )
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

    def delete_lab_settings(self, sample_path: str):
        """
        Delete Lab settings for a sample.

        Args:
            sample_path: Path to the audio file.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM lab_settings WHERE sample_path = ?',
            (sample_path,)
        )
        conn.commit()

    def has_lab_settings(self, sample_path: str) -> bool:
        """
        Check if a sample has Lab settings.

        Args:
            sample_path: Path to the audio file.

        Returns:
            True if settings exist, False otherwise.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT 1 FROM lab_settings WHERE sample_path = ? LIMIT 1',
            (sample_path,)
        )
        return cursor.fetchone() is not None

    # ==================== Tagging Rules Methods ====================

    def create_tagging_rule(self, name: str, condition_type: str, condition_field: str,
                           condition_operator: str, condition_value: str,
                           tags_to_add: List[str]) -> int:
        """
        Create a new tagging rule.

        Args:
            name: Rule name for display.
            condition_type: Type of condition ('field', 'folder', 'bpm_range').
            condition_field: Field to check ('filename', 'folder', 'bpm', 'key', etc).
            condition_operator: Operator ('contains', 'equals', 'greater_than', 'less_than').
            condition_value: Value to compare against.
            tags_to_add: List of tags to add when rule matches.

        Returns:
            The ID of the created rule.
        """
        import json
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tagging_rules (name, condition_type, condition_field,
                                       condition_operator, condition_value, tags_to_add)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, condition_type, condition_field, condition_operator,
              condition_value, json.dumps(tags_to_add)))
        conn.commit()
        return cursor.lastrowid

    def get_tagging_rules(self, enabled_only: bool = False) -> List[Dict]:
        """
        Get all tagging rules.

        Args:
            enabled_only: If True, only return enabled rules.

        Returns:
            List of rule dicts.
        """
        import json
        conn = self._get_connection()
        cursor = conn.cursor()
        if enabled_only:
            cursor.execute('SELECT * FROM tagging_rules WHERE is_enabled = 1 ORDER BY id')
        else:
            cursor.execute('SELECT * FROM tagging_rules ORDER BY id')
        rows = cursor.fetchall()
        rules = []
        for row in rows:
            rule = dict(row)
            rule['tags_to_add'] = json.loads(rule['tags_to_add'])
            rules.append(rule)
        return rules

    def get_tagging_rule(self, rule_id: int) -> Optional[Dict]:
        """Get a tagging rule by ID."""
        import json
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tagging_rules WHERE id = ?', (rule_id,))
        row = cursor.fetchone()
        if row:
            rule = dict(row)
            rule['tags_to_add'] = json.loads(rule['tags_to_add'])
            return rule
        return None

    def update_tagging_rule(self, rule_id: int, **kwargs) -> bool:
        """
        Update a tagging rule.

        Args:
            rule_id: Rule ID to update.
            **kwargs: Fields to update.

        Returns:
            True if updated, False otherwise.
        """
        import json
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build update query dynamically
        updates = []
        values = []
        for key, value in kwargs.items():
            if key == 'tags_to_add' and isinstance(value, list):
                value = json.dumps(value)
            updates.append(f'{key} = ?')
            values.append(value)

        if not updates:
            return False

        values.append(rule_id)
        query = f'UPDATE tagging_rules SET {", ".join(updates)} WHERE id = ?'
        cursor.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0

    def delete_tagging_rule(self, rule_id: int) -> bool:
        """Delete a tagging rule."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tagging_rules WHERE id = ?', (rule_id,))
        conn.commit()
        return cursor.rowcount > 0

    def toggle_tagging_rule(self, rule_id: int) -> bool:
        """Toggle a rule's enabled status. Returns new status."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT is_enabled FROM tagging_rules WHERE id = ?', (rule_id,))
        row = cursor.fetchone()
        if row:
            new_status = 0 if row['is_enabled'] else 1
            cursor.execute('UPDATE tagging_rules SET is_enabled = ? WHERE id = ?',
                          (new_status, rule_id))
            conn.commit()
            return new_status == 1
        return False

    # ==================== Sample Tags Methods ====================

    def add_sample_tag(self, sample_path: str, tag: str, source: str = 'manual') -> bool:
        """
        Add a tag to a sample.

        Args:
            sample_path: Path to the audio file.
            tag: Tag to add.
            source: Source of the tag ('manual', 'rule', 'extracted').

        Returns:
            True if added, False if already exists.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO sample_tags (sample_path, tag, source) VALUES (?, ?, ?)',
                (sample_path, tag.strip().lower(), source)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_sample_tag(self, sample_path: str, tag: str) -> bool:
        """Remove a tag from a sample."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM sample_tags WHERE sample_path = ? AND tag = ?',
            (sample_path, tag.strip().lower())
        )
        conn.commit()
        return cursor.rowcount > 0

    def get_sample_tags(self, sample_path: str) -> List[str]:
        """Get all tags for a sample."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT tag FROM sample_tags WHERE sample_path = ? ORDER BY tag',
            (sample_path,)
        )
        return [row[0] for row in cursor.fetchall()]

    def get_all_tags(self) -> List[Dict]:
        """Get all unique tags with counts."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT tag, COUNT(*) as count FROM sample_tags
            GROUP BY tag ORDER BY count DESC
        ''')
        return [{'tag': row[0], 'count': row[1]} for row in cursor.fetchall()]

    def get_samples_by_tag(self, tag: str) -> List[Dict]:
        """Get all samples with a specific tag."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.* FROM samples s
            JOIN sample_tags st ON s.path = st.sample_path
            WHERE st.tag = ?
            ORDER BY s.filename
        ''', (tag.strip().lower(),))
        return [dict(row) for row in cursor.fetchall()]

    def clear_sample_tags(self, sample_path: str, source: str = None):
        """
        Clear tags from a sample.

        Args:
            sample_path: Path to the audio file.
            source: If specified, only clear tags from this source.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        if source:
            cursor.execute(
                'DELETE FROM sample_tags WHERE sample_path = ? AND source = ?',
                (sample_path, source)
            )
        else:
            cursor.execute('DELETE FROM sample_tags WHERE sample_path = ?', (sample_path,))
        conn.commit()

    # ==================== Rename History Methods ====================

    def add_rename_history(self, original_path: str, new_path: str):
        """Record a file rename for undo support."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO rename_history (original_path, new_path) VALUES (?, ?)',
            (original_path, new_path)
        )
        conn.commit()

    def get_rename_history(self, limit: int = 100) -> List[Dict]:
        """Get rename history, most recent first."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM rename_history ORDER BY renamed_at DESC LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def clear_rename_history(self):
        """Clear all rename history."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM rename_history')
        conn.commit()

    # ==================== Duplicate Detection Methods ====================

    def get_samples_for_duplicate_check(self) -> List[Dict]:
        """Get all samples with size and duration for duplicate checking."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT path, filename, size, duration FROM samples
            WHERE size > 0
            ORDER BY size, duration
        ''')
        return [dict(row) for row in cursor.fetchall()]


# Global database instance (singleton pattern)
_db_instance: Optional[DatabaseManager] = None


def get_database() -> DatabaseManager:
    """Get the global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
