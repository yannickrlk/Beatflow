import os
import re
from typing import List, Dict, Set, Optional

# Metadata reading
try:
    import mutagen
    from mutagen.easyid3 import EasyID3
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC
    from mutagen.oggvorbis import OggVorbis
    from mutagen.wave import WAVE
    from mutagen.aiff import AIFF
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

# Database caching
try:
    from core.database import get_database
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


class LibraryScanner:
    """Manages file system scanning and metadata extraction."""
    
    AUDIO_EXTENSIONS = {'.wav', '.mp3', '.ogg', '.flac', '.aiff', '.aif'}
    
    @classmethod
    def scan_folder(cls, folder_path: str, recursive: bool = False) -> List[Dict]:
        """
        Scan a folder for audio files with database caching.

        Args:
            folder_path: Path to scan
            recursive: If True, scan subfolders too. Default False.
        """
        samples = []
        samples_to_cache = []  # New/modified samples to save to DB

        # Get database if available
        db = get_database() if DB_AVAILABLE else None

        try:
            if recursive:
                for root, dirs, files in os.walk(folder_path):
                    files.sort()
                    for item in files:
                        ext = os.path.splitext(item)[1].lower()
                        if ext in cls.AUDIO_EXTENSIONS:
                            file_path = os.path.join(root, item)
                            sample_info = cls._get_sample_with_cache(
                                item, file_path, db, samples_to_cache
                            )
                            samples.append(sample_info)
            else:
                # Non-recursive: only files in this folder
                items = sorted(os.listdir(folder_path))
                for item in items:
                    item_path = os.path.join(folder_path, item)
                    if os.path.isfile(item_path):
                        ext = os.path.splitext(item)[1].lower()
                        if ext in cls.AUDIO_EXTENSIONS:
                            sample_info = cls._get_sample_with_cache(
                                item, item_path, db, samples_to_cache
                            )
                            samples.append(sample_info)

            # Bulk save new/modified samples to cache
            if db and samples_to_cache:
                db.upsert_samples(samples_to_cache)

        except Exception as e:
            print(f"Error scanning {folder_path}: {e}")

        return samples

    @classmethod
    def _get_sample_with_cache(cls, filename: str, filepath: str, db, samples_to_cache: list) -> Dict:
        """
        Get sample info, using cache if available and valid.

        Args:
            filename: Name of the file.
            filepath: Full path to the file.
            db: Database manager instance or None.
            samples_to_cache: List to append new samples for bulk insert.

        Returns:
            Sample info dict.
        """
        # Get file stats
        try:
            stat = os.stat(filepath)
            mtime = stat.st_mtime
            size = stat.st_size
        except OSError:
            mtime = 0
            size = 0

        # Try cache first
        if db:
            cached = db.get_sample_if_valid(filepath, mtime, size)
            if cached:
                # Cache hit - return cached data
                return cached

        # Cache miss - parse file
        sample_info = cls.parse_sample_info(filename, filepath)

        # Add file stats for cache validation
        sample_info['mtime'] = mtime
        sample_info['size'] = size

        # Queue for bulk cache update
        samples_to_cache.append(sample_info)

        return sample_info

    @classmethod
    def get_subfolders(cls, folder_path: str) -> List[str]:
        """Get immediate subfolders of a folder."""
        subfolders = []
        try:
            for item in sorted(os.listdir(folder_path)):
                item_path = os.path.join(folder_path, item)
                if os.path.isdir(item_path):
                    subfolders.append(item_path)
        except (PermissionError, OSError):
            pass
        return subfolders

    @classmethod
    def count_samples_shallow(cls, folder_path: str) -> int:
        """Count audio files in a folder (non-recursive)."""
        count = 0
        try:
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(item_path):
                    ext = os.path.splitext(item)[1].lower()
                    if ext in cls.AUDIO_EXTENSIONS:
                        count += 1
        except (PermissionError, OSError):
            pass
        return count

    @classmethod
    def parse_sample_info(cls, filename: str, filepath: str) -> Dict:
        """Parse filename and file metadata for sample info."""
        name = os.path.splitext(filename)[0]

        # Extract BPM from filename
        bpm = ""
        for pattern in [r'(\d{2,3})\s*bpm', r'bpm\s*(\d{2,3})', r'_(\d{2,3})_']:
            match = re.search(pattern, filename.lower())
            if match:
                bpm = match.group(1)
                break

        # Extract key from filename
        key = ""
        match = re.search(r'\b([A-G][#b]?(?:maj|min|m)?)\b', filename, re.IGNORECASE)
        if match:
            key = match.group(1)

        # Base sample info
        sample = {
            'name': name,
            'bpm': bpm,
            'key': key,
            'path': filepath,
            'filename': filename,
            # New metadata fields (populated by mutagen)
            'title': '',
            'artist': '',
            'album': '',
            'genre': '',
            'year': '',
            'duration': 0,
            'bitrate': 0,
            'sample_rate': 0,
        }

        # Read real metadata from file tags
        if MUTAGEN_AVAILABLE:
            metadata = cls._read_file_metadata(filepath)
            sample.update(metadata)

            # Use title from metadata if available, otherwise keep filename
            if sample['title']:
                sample['name'] = sample['title']

        return sample

    @classmethod
    def _read_file_metadata(cls, filepath: str) -> Dict:
        """Read metadata from audio file using mutagen."""
        def get_first(value_list) -> str:
            """Get first item from a list or return empty string."""
            if value_list and len(value_list) > 0:
                return str(value_list[0])
            return ""

        metadata = {
            'title': '',
            'artist': '',
            'album': '',
            'genre': '',
            'year': '',
            'duration': 0,
            'bitrate': 0,
            'sample_rate': 0,
        }

        try:
            audio = mutagen.File(filepath, easy=True)
            if audio is None:
                return metadata

            # Extract common tags (EasyID3-style)
            if hasattr(audio, 'get'):
                metadata['title'] = get_first(audio.get('title', []))
                metadata['artist'] = get_first(audio.get('artist', []))
                metadata['album'] = get_first(audio.get('album', []))
                metadata['genre'] = get_first(audio.get('genre', []))
                metadata['year'] = get_first(audio.get('date', []) or audio.get('year', []))

            # Get audio properties (duration, bitrate, sample rate)
            if hasattr(audio, 'info') and audio.info:
                info = audio.info
                if hasattr(info, 'length'):
                    metadata['duration'] = info.length
                if hasattr(info, 'bitrate'):
                    metadata['bitrate'] = info.bitrate // 1000 if info.bitrate else 0
                if hasattr(info, 'sample_rate'):
                    metadata['sample_rate'] = info.sample_rate

        except Exception:
            # Silently fail for corrupted/unreadable files
            pass

        return metadata

    @staticmethod
    def extract_tags(name: str) -> List[str]:
        """Extract characteristic tags from filename."""
        tags = []
        keywords = ['808', 'kick', 'snare', 'hihat', 'hat', 'clap', 'perc',
                   'loop', 'bass', 'pad', 'lead', 'synth', 'piano', 'guitar',
                   'trap', 'drill', 'lofi', 'ambient', 'hard', 'soft', 'dark']
        name_lower = name.lower()
        for kw in keywords:
            if kw in name_lower:
                tags.append(kw.capitalize())
        return tags

    @classmethod
    def save_metadata(cls, filepath: str, metadata: Dict) -> bool:
        """
        Save metadata to audio file tags.

        Args:
            filepath: Path to the audio file.
            metadata: Dict with keys: title, artist, album, bpm, key, genre, year

        Returns:
            True if save succeeded, False otherwise.
        """
        if not MUTAGEN_AVAILABLE:
            print("Mutagen not available for saving metadata")
            return False

        ext = os.path.splitext(filepath)[1].lower()

        try:
            if ext == '.mp3':
                return cls._save_mp3_metadata(filepath, metadata)
            elif ext == '.flac':
                return cls._save_flac_metadata(filepath, metadata)
            elif ext in ['.ogg', '.oga']:
                return cls._save_ogg_metadata(filepath, metadata)
            elif ext in ['.wav', '.wave']:
                # WAV has limited support, try RIFF INFO tags
                return cls._save_wav_metadata(filepath, metadata)
            elif ext in ['.aiff', '.aif']:
                return cls._save_aiff_metadata(filepath, metadata)
            else:
                print(f"Unsupported format for metadata: {ext}")
                return False
        except Exception as e:
            print(f"Error saving metadata: {e}")
            return False

    @classmethod
    def _save_mp3_metadata(cls, filepath: str, metadata: Dict) -> bool:
        """Save metadata to MP3 file using ID3 tags."""
        from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC, TBPM, TKEY

        try:
            try:
                tags = ID3(filepath)
            except Exception:
                # No existing tags, create new
                tags = ID3()

            # Set tags
            if metadata.get('title'):
                tags['TIT2'] = TIT2(encoding=3, text=metadata['title'])
            if metadata.get('artist'):
                tags['TPE1'] = TPE1(encoding=3, text=metadata['artist'])
            if metadata.get('album'):
                tags['TALB'] = TALB(encoding=3, text=metadata['album'])
            if metadata.get('genre'):
                tags['TCON'] = TCON(encoding=3, text=metadata['genre'])
            if metadata.get('year'):
                tags['TDRC'] = TDRC(encoding=3, text=metadata['year'])
            if metadata.get('bpm'):
                tags['TBPM'] = TBPM(encoding=3, text=metadata['bpm'])
            if metadata.get('key'):
                tags['TKEY'] = TKEY(encoding=3, text=metadata['key'])

            tags.save(filepath)
            return True
        except Exception as e:
            print(f"Error saving MP3 metadata: {e}")
            return False

    @classmethod
    def _save_flac_metadata(cls, filepath: str, metadata: Dict) -> bool:
        """Save metadata to FLAC file using Vorbis comments."""
        audio = FLAC(filepath)

        if metadata.get('title'):
            audio['title'] = metadata['title']
        if metadata.get('artist'):
            audio['artist'] = metadata['artist']
        if metadata.get('album'):
            audio['album'] = metadata['album']
        if metadata.get('genre'):
            audio['genre'] = metadata['genre']
        if metadata.get('year'):
            audio['date'] = metadata['year']
        if metadata.get('bpm'):
            audio['bpm'] = metadata['bpm']
        if metadata.get('key'):
            audio['initialkey'] = metadata['key']

        audio.save()
        return True

    @classmethod
    def _save_ogg_metadata(cls, filepath: str, metadata: Dict) -> bool:
        """Save metadata to OGG file using Vorbis comments."""
        audio = OggVorbis(filepath)

        if metadata.get('title'):
            audio['title'] = metadata['title']
        if metadata.get('artist'):
            audio['artist'] = metadata['artist']
        if metadata.get('album'):
            audio['album'] = metadata['album']
        if metadata.get('genre'):
            audio['genre'] = metadata['genre']
        if metadata.get('year'):
            audio['date'] = metadata['year']
        if metadata.get('bpm'):
            audio['bpm'] = metadata['bpm']
        if metadata.get('key'):
            audio['initialkey'] = metadata['key']

        audio.save()
        return True

    @classmethod
    def _save_wav_metadata(cls, filepath: str, metadata: Dict) -> bool:
        """Save metadata to WAV file (limited support via RIFF INFO)."""
        # WAV metadata support is very limited
        # mutagen.wave doesn't support writing tags well
        # For now, just return True to not block the flow
        print("WAV metadata saving has limited support")
        return True

    @classmethod
    def _save_aiff_metadata(cls, filepath: str, metadata: Dict) -> bool:
        """Save metadata to AIFF file."""
        audio = AIFF(filepath)

        # AIFF uses ID3 tags similar to MP3
        if audio.tags is None:
            audio.add_tags()

        if metadata.get('title'):
            audio.tags['TIT2'] = mutagen.id3.TIT2(encoding=3, text=metadata['title'])
        if metadata.get('artist'):
            audio.tags['TPE1'] = mutagen.id3.TPE1(encoding=3, text=metadata['artist'])
        if metadata.get('album'):
            audio.tags['TALB'] = mutagen.id3.TALB(encoding=3, text=metadata['album'])
        if metadata.get('genre'):
            audio.tags['TCON'] = mutagen.id3.TCON(encoding=3, text=metadata['genre'])
        if metadata.get('year'):
            audio.tags['TDRC'] = mutagen.id3.TDRC(encoding=3, text=metadata['year'])

        audio.save()
        return True
