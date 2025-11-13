"""
File metadata analyzer - extracts information without accessing content
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import logging

from .config import (
    is_system_protected,
    is_disposable_extension,
    get_file_category,
    MAX_FILE_SIZE_MB
)

logger = logging.getLogger(__name__)


class FileAnalyzer:
    """Analyzes file metadata without accessing file content for privacy"""
    
    def __init__(self):
        self.files_analyzed = 0
        self.errors = 0
    
    def extract_metadata(self, filepath: str) -> Optional[Dict]:
        """
        Extract comprehensive metadata from a file
        
        Args:
            filepath: Path to the file
            
        Returns:
            Dictionary containing file metadata, or None if error
        """
        try:
            # Get file stats
            stats = os.stat(filepath)
            path_obj = Path(filepath)
            
            # Current timestamp for age calculations
            now = datetime.now().timestamp()
            
            # Time-based features
            created_time = stats.st_ctime
            modified_time = stats.st_mtime
            accessed_time = stats.st_atime
            
            # Calculate ages in days
            created_days = (now - created_time) / 86400
            modified_days = (now - modified_time) / 86400
            accessed_days = (now - accessed_time) / 86400
            
            # File size
            size_bytes = stats.st_size
            size_mb = size_bytes / (1024 * 1024)
            
            # Skip extremely large files
            if size_mb > MAX_FILE_SIZE_MB:
                logger.warning(f"Skipping extremely large file: {filepath} ({size_mb:.1f} MB)")
                return None
            
            # Path analysis
            extension = path_obj.suffix.lower().lstrip('.')
            filename = path_obj.name
            directory = str(path_obj.parent)
            depth = len(path_obj.parts)
            
            # File characteristics
            is_hidden = filename.startswith('.')
            in_system_folder = is_system_protected(filepath)
            is_disposable = is_disposable_extension(extension)
            file_category = get_file_category(extension)
            
            # Construct metadata dictionary
            metadata = {
                # Identification
                'path': filepath,
                'name': filename,
                'directory': directory,
                'extension': extension,
                'category': file_category,
                
                # Size
                'size_bytes': size_bytes,
                'size_mb': size_mb,
                'size_kb': size_bytes / 1024,
                
                # Timestamps (raw)
                'created_timestamp': created_time,
                'modified_timestamp': modified_time,
                'accessed_timestamp': accessed_time,
                
                # Ages (calculated)
                'created_days_ago': created_days,
                'modified_days_ago': modified_days,
                'accessed_days_ago': accessed_days,
                
                # Characteristics
                'is_hidden': is_hidden,
                'depth': depth,
                'in_system_folder': in_system_folder,
                'is_disposable_ext': is_disposable,
                
                # Derived features
                'days_since_modification': modified_days,
                'days_since_access': accessed_days,
                'access_to_modify_ratio': accessed_days / max(modified_days, 0.1),
                'is_recent': accessed_days < 7,
                'is_old': modified_days > 365,
                'is_large': size_mb > 100,
            }
            
            self.files_analyzed += 1
            return metadata
            
        except PermissionError:
            logger.debug(f"Permission denied: {filepath}")
            self.errors += 1
            return None
            
        except FileNotFoundError:
            logger.debug(f"File not found: {filepath}")
            self.errors += 1
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing {filepath}: {str(e)}")
            self.errors += 1
            return None
    
    def get_statistics(self) -> Dict:
        """Get analyzer statistics"""
        return {
            'files_analyzed': self.files_analyzed,
            'errors': self.errors,
            'success_rate': self.files_analyzed / max(self.files_analyzed + self.errors, 1)
        }
    
    def reset_statistics(self):
        """Reset analyzer statistics"""
        self.files_analyzed = 0
        self.errors = 0