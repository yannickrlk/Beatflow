"""Exporter module for Beatflow - ZIP bundling and kit generation."""

import os
import zipfile
from typing import List, Tuple, Callable, Optional
from core.database import get_database


class CollectionExporter:
    """Export collections to ZIP files."""

    def __init__(self):
        self.db = get_database()

    def get_collection_files(self, collection_id: int) -> List[dict]:
        """
        Get all sample files in a collection.

        Args:
            collection_id: The collection ID.

        Returns:
            List of sample dicts with path and filename.
        """
        return self.db.get_collection_samples(collection_id)

    def validate_files(self, samples: List[dict]) -> Tuple[List[str], List[str]]:
        """
        Validate which files exist on disk.

        Args:
            samples: List of sample dicts.

        Returns:
            Tuple of (valid_paths, missing_paths).
        """
        valid = []
        missing = []

        for sample in samples:
            path = sample.get('path', '')
            if path and os.path.exists(path):
                valid.append(path)
            else:
                missing.append(path)

        return valid, missing

    def export_to_zip(
        self,
        collection_id: int,
        output_path: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[bool, str, int]:
        """
        Export a collection to a ZIP file.

        Args:
            collection_id: The collection ID to export.
            output_path: Full path for the output ZIP file.
            progress_callback: Optional callback with (current, total, filename).

        Returns:
            Tuple of (success, message, file_count).
        """
        # Get collection info
        collection = self.db.get_collection(collection_id)
        if not collection:
            return False, "Collection not found", 0

        # Get all samples in the collection
        samples = self.get_collection_files(collection_id)
        if not samples:
            return False, "Collection is empty", 0

        # Validate files
        valid_paths, missing_paths = self.validate_files(samples)

        if not valid_paths:
            return False, "No valid files found in collection", 0

        # Create ZIP file
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                total = len(valid_paths)

                for i, filepath in enumerate(valid_paths):
                    filename = os.path.basename(filepath)

                    # Update progress
                    if progress_callback:
                        progress_callback(i + 1, total, filename)

                    # Add file to ZIP (use filename only, no folder structure)
                    try:
                        zf.write(filepath, filename)
                    except PermissionError:
                        # Skip files that are locked
                        continue
                    except FileNotFoundError:
                        # File was deleted between validation and export
                        continue

            # Build result message
            exported_count = len(valid_paths)
            message = f"Exported {exported_count} samples"

            if missing_paths:
                message += f" ({len(missing_paths)} files were missing)"

            return True, message, exported_count

        except PermissionError:
            return False, "Permission denied - cannot write to destination", 0
        except OSError as e:
            return False, f"Error creating ZIP: {str(e)}", 0

    def export_samples_to_zip(
        self,
        sample_paths: List[str],
        output_path: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[bool, str, int]:
        """
        Export a list of sample paths to a ZIP file.

        Args:
            sample_paths: List of file paths to export.
            output_path: Full path for the output ZIP file.
            progress_callback: Optional callback with (current, total, filename).

        Returns:
            Tuple of (success, message, file_count).
        """
        if not sample_paths:
            return False, "No samples to export", 0

        # Validate files
        valid_paths = [p for p in sample_paths if os.path.exists(p)]

        if not valid_paths:
            return False, "No valid files found", 0

        # Create ZIP file
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                total = len(valid_paths)

                for i, filepath in enumerate(valid_paths):
                    filename = os.path.basename(filepath)

                    if progress_callback:
                        progress_callback(i + 1, total, filename)

                    try:
                        zf.write(filepath, filename)
                    except (PermissionError, FileNotFoundError):
                        continue

            exported_count = len(valid_paths)
            missing_count = len(sample_paths) - exported_count

            message = f"Exported {exported_count} samples"
            if missing_count > 0:
                message += f" ({missing_count} files were skipped)"

            return True, message, exported_count

        except PermissionError:
            return False, "Permission denied - cannot write to destination", 0
        except OSError as e:
            return False, f"Error creating ZIP: {str(e)}", 0


# Singleton instance
_exporter_instance: Optional[CollectionExporter] = None


def get_exporter() -> CollectionExporter:
    """Get the global CollectionExporter instance."""
    global _exporter_instance
    if _exporter_instance is None:
        _exporter_instance = CollectionExporter()
    return _exporter_instance
