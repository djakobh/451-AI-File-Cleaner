"""
UI styling constants and theme definitions
"""

# Color schemes
THEMES = {
    'light': {
        'bg': '#ffffff',
        'fg': '#000000',
        'select_bg': '#0078d7',
        'select_fg': '#ffffff',
        'delete_bg': '#ffcccc',
        'keep_bg': '#ccffcc',
        'warning_bg': '#fff3cd',
        'error_bg': '#f8d7da',
    },
    'dark': {
        'bg': '#2b2b2b',
        'fg': '#ffffff',
        'select_bg': '#0078d7',
        'select_fg': '#ffffff',
        'delete_bg': '#8b0000',
        'keep_bg': '#006400',
        'warning_bg': '#856404',
        'error_bg': '#721c24',
    }
}

# Font configurations
FONTS = {
    'title': ('Segoe UI', 16, 'bold'),
    'subtitle': ('Segoe UI', 10),
    'body': ('Segoe UI', 10),
    'mono': ('Consolas', 9),
}

# Spacing
PADDING = {
    'small': 5,
    'medium': 10,
    'large': 20,
}

# Button styles
BUTTON_STYLES = {
    'primary': {
        'bg': '#0078d7',
        'fg': '#ffffff',
        'active_bg': '#005a9e',
    },
    'danger': {
        'bg': '#d32f2f',
        'fg': '#ffffff',
        'active_bg': '#9a0007',
    },
    'success': {
        'bg': '#388e3c',
        'fg': '#ffffff',
        'active_bg': '#00600f',
    },
}

def apply_theme(widget, theme='light'):
    """
    Apply a theme to a widget
    
    Args:
        widget: tkinter widget
        theme: Theme name ('light' or 'dark')
    """
    colors = THEMES.get(theme, THEMES['light'])
    try:
        widget.configure(
            bg=colors['bg'],
            fg=colors['fg']
        )
    except:
        pass  # Some widgets don't support all options