"""
Configuration settings for Facebook Account Creator
"""

import os
import random
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
ACCOUNTS_DIR = BASE_DIR / "accounts"  # Kept for backwards compatibility

# Proxy configuration - update this with your own proxy API if needed
PROXY_API_URL = "https://proxy.webshare.io/api/v2/proxy/list/download/ipptaigswsjlkwrfbsyqyhomsttxsimhcdhoiboc/-/any/username/direct/-/"
PROXY_FILE = BASE_DIR / "proxies" / "proxy_list.txt"

# Request settings
REQUEST_TIMEOUT = 20  # seconds
MAX_RETRIES = 3

# Improved mobile user agents
USER_AGENTS = [
    # iPhone
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/113.0.5672.109 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6.1 Mobile/15E148 Safari/604.1",
    
    # Android
    "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G998U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Pixel 6 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    
    # Facebook App User Agents
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,3;FBMD/iPhone;FBSN/iOS;FBSV/16.5;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5]",
    "Mozilla/5.0 (Linux; Android 13; SM-S908B Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/412.0.0.22.115;]",
]

def get_random_user_agent():
    """Return a random mobile user agent"""
    return random.choice(USER_AGENTS)

# Facebook URLs - focusing only on m.facebook.com for better mobile experience
FB_MOBILE_HOME = "https://m.facebook.com/"
FB_MOBILE_SIGNUP = "https://m.facebook.com/reg/"
FB_MOBILE_LOGIN = "https://m.facebook.com/login/"

# Human-like behavior settings - reduced to speed up the process
TYPING_SPEED_RANGE = (0.02, 0.06)  # seconds per character (faster)
FIELD_DELAY_RANGE = (0.3, 0.8)     # seconds between fields (faster)
PAGE_LOAD_DELAY_RANGE = (0.5, 1.2) # seconds for page loading (faster)
SUBMIT_DELAY_RANGE = (0.5, 1.0)    # seconds before submitting form

# Account generation settings
CONFIG = {
    # Logging settings
    "log_level": "INFO",
    "console_log_level": "ERROR",  # Only show errors in console
    
    # Account settings
    "attempts_per_proxy": 2,
    "max_proxy_attempts": 3,
    "use_random_birthday": True,
    "min_age": 31,  # Facebook requires 18+, but add 1 for safety
    "max_age": 54,
    "password_length": 12,
    
    # Proxy settings
    "test_proxies_first": True,
    "max_proxies_to_test": 5,
}