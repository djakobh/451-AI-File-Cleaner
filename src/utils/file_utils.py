"""
File operation utilities
"""

import os
import shutil
import platform
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
            # Use platform-specific recycle bin implementation
            if platform.system() == 'Windows':
                if _move_to_recycle_bin_windows(filepath):
                    logger.info(f"Moved to recycle bin: {filepath}")
                    return True
                else:
                    logger.warning("Failed to move to recycle bin, using permanent deletion")
            else:
                # For non-Windows, fall back to permanent deletion with warning
                logger.warning(f"Recycle bin not supported on {platform.system()}, using permanent deletion")

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


def _move_to_recycle_bin_windows(filepath: str) -> bool:
    """
    Move file to Windows Recycle Bin using shell32.dll

    Args:
        filepath: Path to file

    Returns:
        True if successful, False otherwise
    """
    try:
        import ctypes
        from ctypes import windll, c_uint, c_wchar_p, c_int, c_void_p, Structure, byref

        # Define SHFILEOPSTRUCTW structure (64-bit compatible)
        class SHFILEOPSTRUCTW(Structure):
            _fields_ = [
                ("hwnd", c_void_p),
                ("wFunc", c_uint),
                ("pFrom", c_wchar_p),
                ("pTo", c_wchar_p),
                ("fFlags", c_uint),
                ("fAnyOperationsAborted", c_int),
                ("hNameMappings", c_void_p),
                ("lpszProgressTitle", c_wchar_p)
            ]

        # Constants
        FO_DELETE = 0x0003
        FOF_ALLOWUNDO = 0x0040
        FOF_NOCONFIRMATION = 0x0010
        FOF_SILENT = 0x0004
        FOF_NOERRORUI = 0x0400

        # Convert to absolute path with double null terminator (required by API)
        abs_path = os.path.abspath(filepath) + '\0\0'

        # Setup structure
        fileop = SHFILEOPSTRUCTW()
        fileop.hwnd = None
        fileop.wFunc = FO_DELETE
        fileop.pFrom = abs_path
        fileop.pTo = None
        fileop.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT | FOF_NOERRORUI
        fileop.fAnyOperationsAborted = 0
        fileop.hNameMappings = None
        fileop.lpszProgressTitle = None

        # Call SHFileOperationW
        result = windll.shell32.SHFileOperationW(byref(fileop))

        if result == 0:
            return True
        else:
            logger.error(f"SHFileOperationW returned error code: {result}")
            return False

    except Exception as e:
        logger.error(f"Error moving to recycle bin: {e}")
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