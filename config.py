"""
Configuration settings for Facebook Account Creator
"""

import os
import random
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
ACCOUNTS_DIR = BASE_DIR / "accounts"

# Proxy configuration
PROXY_API_URL = "https://proxy.webshare.io/api/v2/proxy/list/download/ipptaigswsjlkwrfbsyqyhomsttxsimhcdhoiboc/-/any/username/direct/-/"
PROXY_FILE = BASE_DIR / "proxies" / "proxy_list.txt"

# Request settings
REQUEST_TIMEOUT = 30  # seconds
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
    "Mozilla/5.0 (Linux; Android 12; SM-A525F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    
    # Facebook App User Agents
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,3;FBMD/iPhone;FBSN/iOS;FBSV/16.5;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5]",
    "Mozilla/5.0 (Linux; Android 13; SM-S908B Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/412.0.0.22.115;]",
    "Mozilla/5.0 (Linux; Android 12; SM-G998U Build/SP1A.210812.016) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/412.0.0.22.115;]",
]

def get_random_user_agent():
    """Return a random mobile user agent"""
    return random.choice(USER_AGENTS)

# Facebook URLs - focusing only on m.facebook.com
FB_MOBILE_HOME = "https://m.facebook.com/"
FB_MOBILE_SIGNUP = "https://m.facebook.com/reg/"
FB_MOBILE_LOGIN = "https://m.facebook.com/login/"

# Human-like behavior settings
TYPING_SPEED_RANGE = (0.04, 0.12)  # seconds per character - slightly faster
FIELD_DELAY_RANGE = (0.7, 2.0)     # seconds between fields - slightly faster
PAGE_LOAD_DELAY_RANGE = (1.0, 2.5) # seconds for page loading - slightly faster
SUBMIT_DELAY_RANGE = (1.2, 2.5)    # seconds before submitting form

# Account generation settings
CONFIG = {
    "log_level": "INFO",
    "save_cookies": True,
    "save_accounts": True,
    "verify_success": True,
    "attempts_per_proxy": 2,
    "use_random_birthday": True,
    "min_age": 19,  # Facebook requires 18+, but add 1 for safety
    "max_age": 42,  # Not too old to avoid suspicion
    "password_length": 12,
}