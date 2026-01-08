"""Metadata Architect - Rule-based tagging, renaming, and duplicate detection."""

import os
import re
import hashlib
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from core.database import get_database


# ==================== Preset Rules ====================

PRESET_RULES = [
    {
        'name': '808 Samples → Bass, Drums',
        'condition_field': 'folder',
        'condition_operator': 'contains',
        'condition_value': '808',
        'tags_to_add': ['bass', 'drums']
    },
    {
        'name': 'High Energy (BPM > 140)',
        'condition_field': 'bpm',
        'condition_operator': 'greater_than',
        'condition_value': '140',
        'tags_to_add': ['high energy']
    },
    {
        'name': 'Minor Key → Dark',
        'condition_field': 'key',
        'condition_operator': 'contains',
        'condition_value': 'minor',
        'tags_to_add': ['dark']
    },
    {
        'name': 'Kick Samples',
        'condition_field': 'filename',
        'condition_operator': 'contains',
        'condition_value': 'kick',
        'tags_to_add': ['kick', 'drums']
    },
    {
        'name': 'Snare Samples',
        'condition_field': 'filename',
        'condition_operator': 'contains',
        'condition_value': 'snare',
        'tags_to_add': ['snare', 'drums']
    },
    {
        'name': 'Hi-Hat Samples',
        'condition_field': 'filename',
        'condition_operator': 'contains',
        'condition_value': 'hihat',
        'tags_to_add': ['hihat', 'drums']
    },
    {
        'name': 'Vocal Samples',
        'condition_field': 'filename',
        'condition_operator': 'contains',
        'condition_value': 'vocal',
        'tags_to_add': ['vocal']
    },
    {
        'name': 'Loop Samples',
        'condition_field': 'filename',
        'condition_operator': 'contains',
        'condition_value': 'loop',
        'tags_to_add': ['loop']
    },
]


# ==================== Rename Patterns ====================

RENAME_PATTERNS = [
    {
        'name': 'Remove copy suffixes',
        'pattern': r'\s*[\(\[]\s*(copy|\d+)\s*[\)\]]|\s+-\s*copy\s*\d*|\s+copy\s*\d*',
        'replacement': '',
        'description': 'Removes "(1)", "[copy]", "- Copy", etc.'
    },
    {
        'name': 'Standardize BPM format',
        'pattern': r'(\d{2,3})\s*bpm',
        'replacement': r'\1 BPM',
        'description': 'Converts "120bpm" to "120 BPM"',
        'flags': re.IGNORECASE
    },
    {
        'name': 'Remove underscores',
        'pattern': r'_+',
        'replacement': ' ',
        'description': 'Replaces underscores with spaces'
    },
    {
        'name': 'Clean multiple spaces',
        'pattern': r'\s{2,}',
        'replacement': ' ',
        'description': 'Reduces multiple spaces to single space'
    },
    {
        'name': 'Remove leading/trailing hyphens',
        'pattern': r'^[\s\-]+|[\s\-]+$',
        'replacement': '',
        'description': 'Cleans up stray hyphens at start/end'
    },
    {
        'name': 'Remove special characters',
        'pattern': r'[^\w\s\-\.\(\)\[\]]',
        'replacement': '',
        'description': 'Removes unusual characters'
    },
]


class RuleEngine:
    """Engine for applying tagging rules to samples."""

    def __init__(self):
        self.db = get_database()

    def check_rule(self, rule: Dict, sample: Dict) -> bool:
        """
        Check if a sample matches a rule's condition.

        Args:
            rule: Rule dict with condition_field, condition_operator, condition_value.
            sample: Sample dict with metadata.

        Returns:
            True if the sample matches the rule condition.
        """
        field = rule.get('condition_field', '')
        operator = rule.get('condition_operator', '')
        value = rule.get('condition_value', '')

        # Get the field value from sample
        if field == 'folder':
            sample_value = os.path.dirname(sample.get('path', ''))
        elif field == 'filename':
            sample_value = sample.get('filename', '')
        elif field == 'bpm':
            # Use detected BPM if no embedded BPM
            sample_value = sample.get('bpm', '') or sample.get('detected_bpm', '')
        elif field == 'key':
            # Use detected key if no embedded key
            sample_value = sample.get('key', '') or sample.get('detected_key', '')
        else:
            sample_value = sample.get(field, '')

        # Convert to string for comparison
        sample_value = str(sample_value).lower() if sample_value else ''
        value = str(value).lower() if value else ''

        # Apply operator
        if operator == 'contains':
            return value in sample_value
        elif operator == 'equals':
            return sample_value == value
        elif operator == 'starts_with':
            return sample_value.startswith(value)
        elif operator == 'ends_with':
            return sample_value.endswith(value)
        elif operator == 'greater_than':
            try:
                return float(sample_value) > float(value) if sample_value else False
            except ValueError:
                return False
        elif operator == 'less_than':
            try:
                return float(sample_value) < float(value) if sample_value else False
            except ValueError:
                return False
        elif operator == 'regex':
            try:
                return bool(re.search(value, sample_value, re.IGNORECASE))
            except re.error:
                return False

        return False

    def apply_rules_to_sample(self, sample: Dict, rules: List[Dict] = None) -> List[str]:
        """
        Apply all matching rules to a sample and add tags.

        Args:
            sample: Sample dict with metadata.
            rules: Optional list of rules. If None, uses enabled rules from DB.

        Returns:
            List of tags that were added.
        """
        if rules is None:
            rules = self.db.get_tagging_rules(enabled_only=True)

        added_tags = []
        sample_path = sample.get('path', '')

        for rule in rules:
            if self.check_rule(rule, sample):
                for tag in rule.get('tags_to_add', []):
                    if self.db.add_sample_tag(sample_path, tag, source='rule'):
                        added_tags.append(tag)

        return added_tags

    def apply_rules_to_folder(self, folder_path: str,
                              progress_callback: Callable[[int, int], None] = None) -> Dict:
        """
        Apply all enabled rules to samples in a folder.

        Args:
            folder_path: Path to the folder.
            progress_callback: Optional callback with (current, total).

        Returns:
            Dict with results: {'total': int, 'tagged': int, 'tags_added': int}
        """
        # Get samples in folder
        samples = []
        sep = os.sep
        pattern = folder_path + sep + '%'

        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM samples WHERE path LIKE ?', (pattern,))
        samples = [dict(row) for row in cursor.fetchall()]

        rules = self.db.get_tagging_rules(enabled_only=True)
        results = {'total': len(samples), 'tagged': 0, 'tags_added': 0}

        for i, sample in enumerate(samples):
            added = self.apply_rules_to_sample(sample, rules)
            if added:
                results['tagged'] += 1
                results['tags_added'] += len(added)

            if progress_callback:
                progress_callback(i + 1, len(samples))

        return results


class RegexRenamer:
    """Batch file renamer using regular expressions."""

    def __init__(self):
        self.db = get_database()

    def preview_rename(self, sample_path: str, pattern: str, replacement: str,
                       flags: int = 0) -> Optional[str]:
        """
        Preview what a file would be renamed to.

        Args:
            sample_path: Path to the file.
            pattern: Regex pattern to match.
            replacement: Replacement string.
            flags: Regex flags (re.IGNORECASE, etc).

        Returns:
            New filename (without path), or None if no change.
        """
        filename = os.path.basename(sample_path)
        name, ext = os.path.splitext(filename)

        try:
            new_name = re.sub(pattern, replacement, name, flags=flags)
            new_name = new_name.strip()

            if new_name and new_name != name:
                return new_name + ext
        except re.error:
            pass

        return None

    def preview_batch_rename(self, sample_paths: List[str], pattern: str,
                             replacement: str, flags: int = 0) -> List[Tuple[str, str, str]]:
        """
        Preview batch rename for multiple files.

        Args:
            sample_paths: List of file paths.
            pattern: Regex pattern.
            replacement: Replacement string.
            flags: Regex flags.

        Returns:
            List of (original_path, original_name, new_name) tuples for files that would change.
        """
        previews = []

        for path in sample_paths:
            new_name = self.preview_rename(path, pattern, replacement, flags)
            if new_name:
                old_name = os.path.basename(path)
                previews.append((path, old_name, new_name))

        return previews

    def rename_file(self, sample_path: str, new_filename: str) -> Tuple[bool, str]:
        """
        Rename a file and update database.

        Args:
            sample_path: Current path to the file.
            new_filename: New filename (without path).

        Returns:
            Tuple of (success, new_path or error_message).
        """
        if not os.path.exists(sample_path):
            return False, "File not found"

        directory = os.path.dirname(sample_path)
        new_path = os.path.join(directory, new_filename)

        # Check if target already exists
        if os.path.exists(new_path):
            return False, "Target file already exists"

        try:
            # Rename the file
            os.rename(sample_path, new_path)

            # Record in history for undo
            self.db.add_rename_history(sample_path, new_path)

            # Update database - need to update sample path
            # First get the old sample data
            old_sample = self.db.get_sample(sample_path)
            if old_sample:
                # Remove old entry
                self.db.remove_sample(sample_path)
                # Update with new path
                old_sample['path'] = new_path
                old_sample['filename'] = new_filename
                old_sample['name'] = os.path.splitext(new_filename)[0]
                self.db.upsert_sample(old_sample)

                # Update tags
                tags = self.db.get_sample_tags(sample_path)
                for tag in tags:
                    self.db.add_sample_tag(new_path, tag, source='migrated')
                self.db.clear_sample_tags(sample_path)

            return True, new_path

        except OSError as e:
            return False, str(e)

    def batch_rename(self, renames: List[Tuple[str, str]],
                     progress_callback: Callable[[int, int, str], None] = None) -> Dict:
        """
        Perform batch rename.

        Args:
            renames: List of (original_path, new_filename) tuples.
            progress_callback: Optional callback with (current, total, status).

        Returns:
            Dict with results: {'total': int, 'success': int, 'failed': int, 'errors': List}
        """
        results = {'total': len(renames), 'success': 0, 'failed': 0, 'errors': []}

        for i, (path, new_name) in enumerate(renames):
            success, result = self.rename_file(path, new_name)

            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({'path': path, 'error': result})

            if progress_callback:
                status = "OK" if success else f"Failed: {result}"
                progress_callback(i + 1, len(renames), status)

        return results

    def undo_last_rename(self) -> Tuple[bool, str]:
        """
        Undo the most recent rename.

        Returns:
            Tuple of (success, message).
        """
        history = self.db.get_rename_history(limit=1)
        if not history:
            return False, "No rename history"

        entry = history[0]
        original_path = entry['original_path']
        new_path = entry['new_path']

        if not os.path.exists(new_path):
            return False, "Renamed file no longer exists"

        if os.path.exists(original_path):
            return False, "Original filename is already taken"

        try:
            os.rename(new_path, original_path)

            # Update database
            sample = self.db.get_sample(new_path)
            if sample:
                self.db.remove_sample(new_path)
                sample['path'] = original_path
                sample['filename'] = os.path.basename(original_path)
                sample['name'] = os.path.splitext(sample['filename'])[0]
                self.db.upsert_sample(sample)

            return True, f"Restored: {os.path.basename(original_path)}"

        except OSError as e:
            return False, str(e)


class DuplicateFinder:
    """Find duplicate audio files."""

    def __init__(self):
        self.db = get_database()

    def calculate_checksum(self, file_path: str, algorithm: str = 'md5') -> Optional[str]:
        """
        Calculate file checksum.

        Args:
            file_path: Path to the file.
            algorithm: 'md5' or 'sha256'.

        Returns:
            Hex digest string, or None on error.
        """
        if not os.path.exists(file_path):
            return None

        hash_func = hashlib.md5() if algorithm == 'md5' else hashlib.sha256()

        try:
            with open(file_path, 'rb') as f:
                # Read in chunks for large files
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except (IOError, OSError):
            return None

    def find_exact_duplicates(self, sample_paths: List[str] = None,
                              progress_callback: Callable[[int, int], None] = None) -> List[List[Dict]]:
        """
        Find exact duplicates by file checksum.

        Args:
            sample_paths: Optional list of paths. If None, checks all samples.
            progress_callback: Optional progress callback.

        Returns:
            List of duplicate groups, each group is a list of sample dicts.
        """
        if sample_paths is None:
            samples = self.db.get_samples_for_duplicate_check()
            sample_paths = [s['path'] for s in samples]

        # Calculate checksums
        checksums: Dict[str, List[str]] = {}
        total = len(sample_paths)

        for i, path in enumerate(sample_paths):
            checksum = self.calculate_checksum(path)
            if checksum:
                if checksum not in checksums:
                    checksums[checksum] = []
                checksums[checksum].append(path)

            if progress_callback:
                progress_callback(i + 1, total)

        # Find groups with duplicates
        duplicate_groups = []
        for checksum, paths in checksums.items():
            if len(paths) > 1:
                group = []
                for path in paths:
                    sample = self.db.get_sample(path)
                    if sample:
                        sample['checksum'] = checksum
                        group.append(sample)
                if len(group) > 1:
                    duplicate_groups.append(group)

        return duplicate_groups

    def find_near_duplicates(self, sample_paths: List[str] = None,
                             duration_tolerance: float = 0.5,
                             size_tolerance: float = 0.05) -> List[List[Dict]]:
        """
        Find near-exact duplicates by duration and file size.

        Files are considered near-duplicates if they have:
        - Duration within tolerance (seconds)
        - File size within tolerance (percentage)

        Args:
            sample_paths: Optional list of paths. If None, checks all samples.
            duration_tolerance: Maximum duration difference in seconds.
            size_tolerance: Maximum size difference as fraction (0.05 = 5%).

        Returns:
            List of duplicate groups.
        """
        samples = self.db.get_samples_for_duplicate_check()

        if sample_paths:
            samples = [s for s in samples if s['path'] in sample_paths]

        # Group by approximate duration (rounded to tolerance)
        duration_groups: Dict[int, List[Dict]] = {}

        for sample in samples:
            duration = sample.get('duration', 0) or 0
            if duration > 0:
                # Round to tolerance bucket
                bucket = int(duration / duration_tolerance)
                if bucket not in duration_groups:
                    duration_groups[bucket] = []
                duration_groups[bucket].append(sample)

        # Find near-duplicates within each duration group
        duplicate_groups = []

        for bucket, group in duration_groups.items():
            if len(group) < 2:
                continue

            # Check each pair
            checked = set()
            for i, sample1 in enumerate(group):
                if sample1['path'] in checked:
                    continue

                near_dupes = [sample1]
                size1 = sample1.get('size', 0) or 0
                dur1 = sample1.get('duration', 0) or 0

                for j, sample2 in enumerate(group):
                    if i >= j or sample2['path'] in checked:
                        continue

                    size2 = sample2.get('size', 0) or 0
                    dur2 = sample2.get('duration', 0) or 0

                    # Check size tolerance
                    if size1 > 0 and size2 > 0:
                        size_diff = abs(size1 - size2) / max(size1, size2)
                        if size_diff > size_tolerance:
                            continue

                    # Check duration tolerance
                    if abs(dur1 - dur2) <= duration_tolerance:
                        near_dupes.append(sample2)
                        checked.add(sample2['path'])

                if len(near_dupes) > 1:
                    duplicate_groups.append(near_dupes)
                    checked.add(sample1['path'])

        return duplicate_groups

    def safe_delete(self, file_path: str) -> Tuple[bool, str]:
        """
        Safely delete a file by moving to system trash.

        Args:
            file_path: Path to the file to delete.

        Returns:
            Tuple of (success, message).
        """
        if not os.path.exists(file_path):
            return False, "File not found"

        try:
            # Try to use send2trash if available
            try:
                from send2trash import send2trash
                send2trash(file_path)
                # Remove from database
                self.db.remove_sample(file_path)
                return True, "Moved to trash"
            except ImportError:
                # Fallback: just remove from database, don't delete file
                self.db.remove_sample(file_path)
                return True, "Removed from library (file preserved)"

        except Exception as e:
            return False, str(e)


# ==================== Singleton Instances ====================

_rule_engine: Optional[RuleEngine] = None
_regex_renamer: Optional[RegexRenamer] = None
_duplicate_finder: Optional[DuplicateFinder] = None


def get_rule_engine() -> RuleEngine:
    """Get the global RuleEngine instance."""
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = RuleEngine()
    return _rule_engine


def get_regex_renamer() -> RegexRenamer:
    """Get the global RegexRenamer instance."""
    global _regex_renamer
    if _regex_renamer is None:
        _regex_renamer = RegexRenamer()
    return _regex_renamer


def get_duplicate_finder() -> DuplicateFinder:
    """Get the global DuplicateFinder instance."""
    global _duplicate_finder
    if _duplicate_finder is None:
        _duplicate_finder = DuplicateFinder()
    return _duplicate_finder
