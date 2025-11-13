"""
File operation utilities
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def safe_delete_file(filepath: str, use_recycle_bin: bool = True) -> bool:
    """
    Safely delete a file
    
    Args:
        filepath: Path to file
        use_recycle_bin: If True, move to recycle bin instead of permanent deletion
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if use_recycle_bin:
            # Try to use system recycle bin
            try:
                from send2trash import send2trash
                send2trash(filepath)
                logger.info(f"Moved to recycle bin: {filepath}")
                return True
            except ImportError:
                logger.warning("send2trash not available, using permanent deletion")
        
        # Permanent deletion
        os.remove(filepath)
        logger.info(f"Deleted: {filepath}")
        return True
        
    except PermissionError:
        logger.error(f"Permission denied: {filepath}")
        return False
        
    except FileNotFoundError:
        logger.warning(f"File not found: {filepath}")
        return False
        
    except Exception as e:
        logger.error(f"Error deleting {filepath}: {e}")
        return False


def get_file_size_formatted(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def ensure_directory_exists(directory: str) -> bool:
    """
    Ensure a directory exists, create if it doesn't
    
    Args:
        directory: Directory path
        
    Returns:
        True if directory exists or was created
    """
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {e}")
        return False


def get_directory_size(directory: str) -> int:
    """
    Calculate total size of a directory
    
    Args:
        directory: Directory path
        
    Returns:
        Total size in bytes
    """
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, FileNotFoundError):
                    pass
    except Exception as e:
        logger.error(f"Error calculating directory size: {e}")
    
    return total_size


def copy_file(source: str, destination: str) -> bool:
    """
    Copy a file safely
    
    Args:
        source: Source file path
        destination: Destination file path
        
    Returns:
        True if successful
    """
    try:
        shutil.copy2(source, destination)
        logger.info(f"Copied {source} to {destination}")
        return True
    except Exception as e:
        logger.error(f"Error copying file: {e}")
        return False


def move_file(source: str, destination: str) -> bool:
    """
    Move a file safely
    
    Args:
        source: Source file path
        destination: Destination file path
        
    Returns:
        True if successful
    """
    try:
        shutil.move(source, destination)
        logger.info(f"Moved {source} to {destination}")
        return True
    except Exception as e:
        logger.error(f"Error moving file: {e}")
        return False


def is_file_locked(filepath: str) -> bool:
    """
    Check if a file is locked by another process
    
    Args:
        filepath: File path
        
    Returns:
        True if file is locked
    """
    try:
        # Try to open file in exclusive mode
        with open(filepath, 'a'):
            pass
        return False
    except IOError:
        return True


def get_available_space(path: str) -> int:
    """
    Get available disk space for a path
    
    Args:
        path: Path to check
        
    Returns:
        Available space in bytes
    """
    try:
        stat = shutil.disk_usage(path)
        return stat.free
    except Exception as e:
        logger.error(f"Error getting disk space: {e}")
        return 0