import os
from pathlib import Path

# App info
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

for dir_path in [DATA_DIR, MODELS_DIR, FEEDBACK_DIR, LOGS_DIR, CONFIG_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# System folders we should never delete
SYSTEM_FOLDERS = {
    'Windows', 'System32', 'SysWOW64', 'Program Files', 'Program Files (x86)',
    'ProgramData', 'Boot', 'Recovery', '$Recycle.Bin', 'System Volume Information',
    'WindowsApps', 'WinSxS',
    'System', 'Library', 'Applications', 'bin', 'sbin', 'usr', 'var', 'tmp',
    'private', 'cores', 'dev', 'etc', '.Trash', '.fseventsd', '.Spotlight-V100',
    '.DocumentRevisions-V100', '.TemporaryItems',
    'Adobe', 'Adobe Premiere Pro', 'Adobe After Effects', 'Adobe Photoshop',
    'node_modules', 'Python', '.venv', 'venv',
}

SYSTEM_PATHS_PARTIAL = {
    'AppData\\Local\\Temp', 'AppData\\Local\\Microsoft', 'AppData\\Roaming\\Microsoft',
    'Library/Application Support', 'Library/Caches', 'Library/Preferences',
    'Library/LaunchAgents', 'Library/LaunchDaemons', 'Library/Frameworks',
    '/System/', '/Library/', '/private/', '/usr/', '/bin/', '/sbin/',
}

APPLICATION_PATHS = {
    'Plug-Ins', 'Plugins', 'Extensions', 'Add-ons', 'Addons', 'Common Files',
}

# File extension categories
DISPOSABLE_EXTENSIONS = {
    'tmp', 'temp', 'cache', 'bak', 'old', 'backup', 'download', 'part',
    'crdownload', 'partial', 'log', 'dmp', 'chk', 'gid', 'o', 'obj',
    'pyc', 'pyo', 'class', '~', 'swp', 'swo',
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

ADOBE_EXTENSIONS = {
    'aex', 'epr', 'prproj', 'aep', 'psb', 'ffx', 'mogrt', 'plb', 'zdct',
}

DEVELOPMENT_EXTENSIONS = {
    'py', 'pyc', 'pyo', 'js', 'jsx', 'ts', 'tsx', 'cpp', 'c', 'h', 'hpp',
    'java', 'class', 'jar', 'cs', 'csproj', 'sln', 'go', 'rs', 'rb', 'php',
    'json', 'xml', 'yaml', 'yml', 'toml', 'md', 'rst', 'css', 'scss', 'sass',
    'less', 'html', 'htm', 'vue', 'sql', 'db', 'sqlite',
}

CONFIG_EXTENSIONS = {
    'ini', 'cfg', 'conf', 'config', 'properties', 'settings',
    'env', 'gitignore', 'dockerignore',
}

# Scanning settings
MAX_FILES_DEFAULT = 5000
MAX_FILE_SIZE_MB = 1024 * 10
SCAN_DEPTH_LIMIT = 20
PROGRESS_UPDATE_INTERVAL = 100

# ML settings
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
        'use_threshold_based_detection': True,
    },
    'synthetic_samples': 5000,
}

FEATURE_CONFIG = {
    'size_bins': [0, 0.1, 1, 10, 100, float('inf')],
    'access_threshold_days': 365,
    'large_file_threshold_mb': 500,
    'old_file_threshold_days': 730,
}

RECOMMENDATION_CONFIG = {
    'history_limit': 100,
    'adjustment_factor': 0.3,
    'min_similar_count': 3,
}

# UI config
UI_CONFIG = {
    'window_width': 1200,
    'window_height': 800,
    'tree_height': 20,
    'font_family': 'Segoe UI',
    'font_size': 10,
    'title_font_size': 16,
}

COLORS = {
    'delete_bg': '#ffcccc',
    'keep_bg': '#ccffcc',
    'anomaly_fg': '#ff6600',
    'header_bg': '#2c3e50',
    'header_fg': '#ffffff',
    'status_info': '#0066cc',
    'status_success': '#00cc00',
    'status_error': '#cc0000',
}

LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'filename': LOGS_DIR / 'file_purge.log',
    'max_bytes': 10 * 1024 * 1024,
    'backup_count': 5,
}

EXPORT_CONFIG = {
    'default_format': 'csv',
    'include_predictions': True,
    'include_probabilities': True,
    'include_anomalies': True,
}

SAFETY_CONFIG = {
    'simulation_mode': True,
    'require_confirmation': True,
    'min_confidence_threshold': 0.7,
    'exclude_recent_days': 7,
}

FILE_CATEGORIES = {
    'documents': DOCUMENT_EXTENSIONS,
    'images': IMAGE_EXTENSIONS,
    'videos': VIDEO_EXTENSIONS,
    'audio': AUDIO_EXTENSIONS,
    'archives': ARCHIVE_EXTENSIONS,
    'executables': EXECUTABLE_EXTENSIONS,
    'disposable': DISPOSABLE_EXTENSIONS,
    'adobe': ADOBE_EXTENSIONS,
    'development': DEVELOPMENT_EXTENSIONS,
    'config': CONFIG_EXTENSIONS,
}

def get_file_category(extension):
    ext = extension.lower().lstrip('.')
    for category, extensions in FILE_CATEGORIES.items():
        if ext in extensions:
            return category
    return 'other'

def is_system_protected(filepath):
    normalized_path = filepath.replace('\\', '/').upper()

    for folder in SYSTEM_FOLDERS:
        folder_upper = folder.upper()
        if f"/{folder_upper}/" in normalized_path:
            return True
        if normalized_path.startswith(f"{folder_upper}/") or normalized_path.startswith(f"/{folder_upper}/"):
            return True
        if normalized_path.startswith(f"/{folder_upper}") and folder_upper in {'SYSTEM', 'LIBRARY', 'BIN', 'SBIN', 'USR', 'VAR', 'PRIVATE', 'DEV', 'ETC'}:
            return True
        if folder_upper in normalized_path:
            path_parts = normalized_path.split('/')
            if any(folder_upper in part for part in path_parts):
                return True

    for partial in SYSTEM_PATHS_PARTIAL:
        partial_normalized = partial.replace('\\', '/').upper()
        if partial_normalized in normalized_path:
            return True

    for app_path in APPLICATION_PATHS:
        if app_path.upper() in normalized_path:
            return True

    return False

def is_disposable_extension(extension):
    return extension.lower().lstrip('.') in DISPOSABLE_EXTENSIONS
