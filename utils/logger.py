"""
Logging utilities for the application
"""

import os
import logging
import datetime
from config import LOGS_DIR, CONFIG

def setup_logger(name, console_level=None):
    """Set up and return a logger with file and console handlers"""
    # Ensure logs directory exists
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # Create timestamp for log file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOGS_DIR, f"{name}_{timestamp}.log")
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Set logger to capture all levels
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # File handler - always keep detailed logging in the file
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)  # File gets everything
    logger.addHandler(file_handler)
    
    # Console handler - set to specified level or default from config
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Determine console log level
    if console_level:
        console_level = getattr(logging, console_level)
    else:
        console_level = getattr(logging, CONFIG.get("console_log_level", "INFO"))
        
    console_handler.setLevel(console_level)
    logger.addHandler(console_handler)
    
    # Only log initialization to file, not console
    logger.debug(f"Logger initialized. Log file: {log_file}")
    return logger