import os
import logging

from .file_analyzer import FileAnalyzer
from .config import (
    MAX_FILES_DEFAULT,
    SCAN_DEPTH_LIMIT,
    PROGRESS_UPDATE_INTERVAL,
    is_system_protected
)

logger = logging.getLogger(__name__)


class DirectoryScanner:
    def __init__(self, analyzer=None):
        self.analyzer = analyzer or FileAnalyzer()
        self.files_scanned = 0
        self.dirs_scanned = 0
        self.skipped_sys = 0
        self.cancelled = False

    def scan(self, root_path, max_files=MAX_FILES_DEFAULT, progress_cb=None, max_depth=SCAN_DEPTH_LIMIT):
        logger.info(f"Starting scan of {root_path}")

        if not os.path.exists(root_path):
            logger.error(f"Path does not exist: {root_path}")
            return []

        if not os.path.isdir(root_path):
            logger.error(f"Path is not a directory: {root_path}")
            return []

        if is_system_protected(root_path):
            logger.warning(f"Attempting to scan protected system folder: {root_path}")
            if progress_cb:
                progress_cb(0, "Warning: Scanning system folder")

        self.files_scanned = 0
        self.dirs_scanned = 0
        self.skipped_sys = 0
        self.cancelled = False
        self.analyzer.reset_statistics()

        file_data = []
        root_depth = len(os.path.normpath(root_path).split(os.sep))

        try:
            for curr_dir, subdirs, files in os.walk(root_path):
                if self.cancelled:
                    logger.info("Scan cancelled by user")
                    break

                curr_depth = len(os.path.normpath(curr_dir).split(os.sep))
                if curr_depth - root_depth > max_depth:
                    logger.debug(f"Skipping deep directory: {curr_dir}")
                    subdirs.clear()
                    continue

                if is_system_protected(curr_dir):
                    logger.debug(f"Skipping system folder: {curr_dir}")
                    self.skipped_sys += 1
                    subdirs.clear()
                    continue

                subdirs[:] = [d for d in subdirs if not d.startswith('.') and not d.startswith('$')]
                self.dirs_scanned += 1

                for filename in files:
                    if self.files_scanned >= max_files:
                        logger.info(f"Reached file limit: {max_files}")
                        return file_data

                    if self.cancelled:
                        break

                    if filename.startswith('.') or filename.startswith('$'):
                        continue

                    filepath = os.path.join(curr_dir, filename)
                    metadata = self.analyzer.extract_metadata(filepath)

                    if metadata:
                        file_data.append(metadata)
                        self.files_scanned += 1

                        if progress_cb and self.files_scanned % PROGRESS_UPDATE_INTERVAL == 0:
                            progress_cb(self.files_scanned, f"Scanning: {curr_dir}")

        except PermissionError as e:
            logger.error(f"Permission denied accessing directory: {e}")
        except Exception as e:
            logger.error(f"Error during scan: {str(e)}")

        if progress_cb:
            progress_cb(self.files_scanned, f"Scan complete: {self.files_scanned} files analyzed")

        logger.info(f"Scan complete: {self.files_scanned} files, {self.dirs_scanned} directories")
        return file_data

    def cancel(self):
        logger.info("Cancelling scan...")
        self.cancelled = True

    def get_statistics(self):
        stats = self.analyzer.get_statistics()
        stats.update({
            'files_scanned': self.files_scanned,
            'directories_scanned': self.dirs_scanned,
            'skipped_system_folders': self.skipped_sys,
        })
        return stats
