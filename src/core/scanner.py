"""
Directory scanner with progress tracking
"""

import os
from typing import List, Dict, Callable, Optional
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
    """Scans directories and collects file metadata"""
    
    def __init__(self, analyzer: Optional[FileAnalyzer] = None):
        self.analyzer = analyzer or FileAnalyzer()
        self.files_scanned = 0
        self.directories_scanned = 0
        self.skipped_system_folders = 0
        self.is_cancelled = False
    
    def scan(
        self,
        root_path: str,
        max_files: int = MAX_FILES_DEFAULT,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        max_depth: int = SCAN_DEPTH_LIMIT
    ) -> List[Dict]:
        """
        Scan a directory and collect file metadata
        
        Args:
            root_path: Root directory to scan
            max_files: Maximum number of files to scan
            progress_callback: Function to call with progress updates
            max_depth: Maximum directory depth to traverse
            
        Returns:
            List of file metadata dictionaries
        """
        logger.info(f"Starting scan of {root_path}")
        
        # Validate path
        if not os.path.exists(root_path):
            logger.error(f"Path does not exist: {root_path}")
            return []
        
        if not os.path.isdir(root_path):
            logger.error(f"Path is not a directory: {root_path}")
            return []
        
        # Check if scanning system folder
        if is_system_protected(root_path):
            logger.warning(f"Attempting to scan protected system folder: {root_path}")
            if progress_callback:
                progress_callback(0, "Warning: Scanning system folder")
        
        # Reset state
        self.files_scanned = 0
        self.directories_scanned = 0
        self.skipped_system_folders = 0
        self.is_cancelled = False
        self.analyzer.reset_statistics()
        
        file_data = []
        root_depth = len(os.path.normpath(root_path).split(os.sep))
        
        try:
            for current_dir, subdirs, files in os.walk(root_path):
                # Check cancellation
                if self.is_cancelled:
                    logger.info("Scan cancelled by user")
                    break
                
                # Check depth limit
                current_depth = len(os.path.normpath(current_dir).split(os.sep))
                if current_depth - root_depth > max_depth:
                    logger.debug(f"Skipping deep directory: {current_dir}")
                    subdirs.clear()  # Don't descend into subdirectories
                    continue
                
                # Skip system folders
                if is_system_protected(current_dir):
                    logger.debug(f"Skipping system folder: {current_dir}")
                    self.skipped_system_folders += 1
                    subdirs.clear()  # Don't descend into subdirectories
                    continue
                
                # Filter out hidden/system subdirectories
                subdirs[:] = [
                    d for d in subdirs 
                    if not d.startswith('.') and not d.startswith('$')
                ]
                
                self.directories_scanned += 1
                
                # Process files in current directory
                for filename in files:
                    # Check if we've hit the limit
                    if self.files_scanned >= max_files:
                        logger.info(f"Reached file limit: {max_files}")
                        return file_data
                    
                    # Check cancellation
                    if self.is_cancelled:
                        break
                    
                    # Skip hidden files
                    if filename.startswith('.') or filename.startswith('$'):
                        continue
                    
                    # Construct full path
                    filepath = os.path.join(current_dir, filename)
                    
                    # Extract metadata
                    metadata = self.analyzer.extract_metadata(filepath)
                    
                    if metadata:
                        file_data.append(metadata)
                        self.files_scanned += 1
                        
                        # Progress update
                        if progress_callback and self.files_scanned % PROGRESS_UPDATE_INTERVAL == 0:
                            progress_callback(
                                self.files_scanned,
                                f"Scanning: {current_dir}"
                            )
        
        except PermissionError as e:
            logger.error(f"Permission denied accessing directory: {e}")
        
        except Exception as e:
            logger.error(f"Error during scan: {str(e)}")
        
        # Final progress update
        if progress_callback:
            progress_callback(
                self.files_scanned,
                f"Scan complete: {self.files_scanned} files analyzed"
            )
        
        logger.info(f"Scan complete: {self.files_scanned} files, "
                   f"{self.directories_scanned} directories")
        
        return file_data
    
    def cancel(self):
        """Cancel the current scan operation"""
        logger.info("Cancelling scan...")
        self.is_cancelled = True
    
    def get_statistics(self) -> Dict:
        """Get scanner statistics"""
        stats = self.analyzer.get_statistics()
        stats.update({
            'files_scanned': self.files_scanned,
            'directories_scanned': self.directories_scanned,
            'skipped_system_folders': self.skipped_system_folders,
        })
        return stats