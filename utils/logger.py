"""
Logging utilities for the application
"""

import os
import logging
import datetime
from config import LOGS_DIR, CONFIG

def setup_logger(name):
    """Set up and return a logger with file and console handlers"""
    # Ensure logs directory exists
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # Create timestamp for log file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOGS_DIR, f"{name}_{timestamp}.log")
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, CONFIG.get("log_level", "INFO")))
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logger.info(f"Logger initialized. Log file: {log_file}")
    return logger