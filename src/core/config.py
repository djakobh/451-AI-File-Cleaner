"""
Configuration constants and settings for the File Purge System
"""

import os
from pathlib import Path

# Application Info
APP_NAME = "AI File Purge System"
APP_VERSION = "1.0.0"
TEAM_NAME = "Team 13"
COURSE = "CECS 451"

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
FEEDBACK_DIR = DATA_DIR / "feedback"
LOGS_DIR = DATA_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"

# Create directories if they don't exist
for dir_path in [DATA_DIR, MODELS_DIR, FEEDBACK_DIR, LOGS_DIR, CONFIG_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# System Protection
SYSTEM_FOLDERS = {
    'Windows',
    'System32',
    'SysWOW64',
    'Program Files',
    'Program Files (x86)',
    'ProgramData',
    'Boot',
    'Recovery',
    '$Recycle.Bin',
    'System Volume Information',
    'WindowsApps',
    'WinSxS',
}

SYSTEM_PATHS_PARTIAL = {
    'AppData\\Local\\Temp',
    'AppData\\Local\\Microsoft',
    'AppData\\Roaming\\Microsoft',
}

# File Extensions
DISPOSABLE_EXTENSIONS = {
    # Temporary files
    'tmp', 'temp', 'cache', 'bak', 'old', 'backup',
    # Download fragments
    'download', 'part', 'crdownload', 'partial',
    # System files
    'log', 'dmp', 'chk', 'gid',
    # Compilation artifacts
    'o', 'obj', 'pyc', 'pyo', 'class',
    # Backup files
    '~', 'bak', 'swp', 'swo',
}

DOCUMENT_EXTENSIONS = {
    'txt', 'doc', 'docx', 'pdf', 'xls', 'xlsx', 'ppt', 'pptx',
    'odt', 'ods', 'odp', 'rtf', 'tex', 'md', 'csv',
}

IMAGE_EXTENSIONS = {
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico',
    'tiff', 'tif', 'raw', 'cr2', 'nef', 'heic',
}

VIDEO_EXTENSIONS = {
    'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'm4v',
    'mpg', 'mpeg', '3gp', 'ogv',
}

AUDIO_EXTENSIONS = {
    'mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'opus',
    'aiff', 'ape', 'alac',
}

ARCHIVE_EXTENSIONS = {
    'zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'iso',
    'cab', 'arj', 'lzh', 'ace',
}

EXECUTABLE_EXTENSIONS = {
    'exe', 'msi', 'bat', 'cmd', 'com', 'scr', 'dll', 'sys',
}

# Scanning Settings
MAX_FILES_DEFAULT = 5000
MAX_FILE_SIZE_MB = 1024 * 10  # 10 GB max file size to consider
SCAN_DEPTH_LIMIT = 20  # Maximum directory depth

# Progress Update Frequency
PROGRESS_UPDATE_INTERVAL = 100  # Update UI every N files

# ML Model Settings
ML_CONFIG = {
    'random_forest': {
        'n_estimators': 100,
        'max_depth': 10,
        'min_samples_split': 5,
        'random_state': 42,
    },
    'isolation_forest': {
        'contamination': 0.1,
        'n_estimators': 100,
        'random_state': 42,
    },
    'synthetic_samples': 5000,
}

# Feature Engineering
FEATURE_CONFIG = {
    'size_bins': [0, 0.1, 1, 10, 100, float('inf')],  # MB
    'access_threshold_days': 180,
    'large_file_threshold_mb': 100,
    'old_file_threshold_days': 365,
}

# Recommendation Settings
RECOMMENDATION_CONFIG = {
    'history_limit': 100,  # Keep last N user decisions
    'adjustment_factor': 0.3,  # Max score adjustment
    'min_similar_count': 3,  # Min similar files needed for adjustment
}

# UI Settings
UI_CONFIG = {
    'window_width': 1200,
    'window_height': 800,
    'tree_height': 20,
    'font_family': 'Segoe UI',
    'font_size': 10,
    'title_font_size': 16,
}

# Color Scheme
COLORS = {
    'delete_bg': '#ffcccc',  # Light red
    'keep_bg': '#ccffcc',    # Light green
    'anomaly_fg': '#ff6600', # Orange
    'header_bg': '#2c3e50',  # Dark blue-gray
    'header_fg': '#ffffff',  # White
    'status_info': '#0066cc',  # Blue
    'status_success': '#00cc00',  # Green
    'status_error': '#cc0000',  # Red
}

# Logging
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'filename': LOGS_DIR / 'file_purge.log',
    'max_bytes': 10 * 1024 * 1024,  # 10 MB
    'backup_count': 5,
}

# Export Settings
EXPORT_CONFIG = {
    'default_format': 'csv',
    'include_predictions': True,
    'include_probabilities': True,
    'include_anomalies': True,
}

# Safety Settings
SAFETY_CONFIG = {
    'simulation_mode': True,  # Default to simulation (no actual deletion)
    'require_confirmation': True,
    'min_confidence_threshold': 0.7,  # Only recommend if confidence > 70%
    'exclude_recent_days': 7,  # Don't recommend files accessed in last week
}

# File Categories for Analysis
FILE_CATEGORIES = {
    'documents': DOCUMENT_EXTENSIONS,
    'images': IMAGE_EXTENSIONS,
    'videos': VIDEO_EXTENSIONS,
    'audio': AUDIO_EXTENSIONS,
    'archives': ARCHIVE_EXTENSIONS,
    'executables': EXECUTABLE_EXTENSIONS,
    'disposable': DISPOSABLE_EXTENSIONS,
}

def get_file_category(extension: str) -> str:
    """Determine the category of a file based on its extension"""
    ext = extension.lower().lstrip('.')
    
    for category, extensions in FILE_CATEGORIES.items():
        if ext in extensions:
            return category
    
    return 'other'

def is_system_protected(filepath: str) -> bool:
    """Check if a file path is in a protected system location"""
    path_upper = filepath.upper()
    
    # Check full folder names
    for folder in SYSTEM_FOLDERS:
        if f"\\{folder.upper()}\\" in path_upper or path_upper.startswith(f"{folder.upper()}\\"):
            return True
    
    # Check partial paths
    for partial in SYSTEM_PATHS_PARTIAL:
        if partial.upper() in path_upper:
            return True
    
    return False

def is_disposable_extension(extension: str) -> bool:
    """Check if an extension is considered disposable"""
    return extension.lower().lstrip('.') in DISPOSABLE_EXTENSIONS