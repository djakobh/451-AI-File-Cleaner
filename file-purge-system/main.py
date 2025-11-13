"""
AI File Purge System - Main Entry Point
Team 13 - CECS 451

Run this file to start the application
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.config import LOG_CONFIG, APP_NAME, APP_VERSION
from src.utils.logger import setup_logger
from src.gui.main_window import FilePurgeApp

def main():
    """Main application entry point"""
    
    # Setup logging
    setup_logger(
        log_file=LOG_CONFIG['filename'],
        level=LOG_CONFIG['level']
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    
    try:
        # Create and run application
        app = FilePurgeApp()
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()