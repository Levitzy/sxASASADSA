"""
Helper functions for the application
"""

import time
import random
import string
import logging
import datetime
import re
from config import TYPING_SPEED_RANGE, FIELD_DELAY_RANGE, PAGE_LOAD_DELAY_RANGE, SUBMIT_DELAY_RANGE

logger = logging.getLogger("FBAccountCreator")

def generate_strong_password(length=12):
    """Generate a strong random password"""
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = "!@#$%^&*()_+-=[]{}|;:,./<>?"
    
    # Ensure at least one character from each set
    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(special)
    ]
    
    # Fill the remaining length with random characters
    remaining_length = length - len(password)
    all_chars = lowercase + uppercase + digits + special
    password.extend(random.choice(all_chars) for _ in range(remaining_length))
    
    # Shuffle the password characters
    random.shuffle(password)
    
    # Convert list to string
    return ''.join(password)

def simulate_typing_delay(text):
    """Simulate a human typing delay based on text length"""
    if not text:
        return
    
    # Calculate a realistic typing delay
    chars = len(text)
    typing_speed = random.uniform(*TYPING_SPEED_RANGE)  # seconds per character
    delay = chars * typing_speed
    
    # Add some randomness to make it more human-like
    delay = delay * random.uniform(0.8, 1.2)
    
    logger.debug(f"Simulating typing delay of {delay:.2f} seconds for {chars} characters")
    time.sleep(delay)

def simulate_field_delay():
    """Simulate delay between filling form fields"""
    delay = random.uniform(*FIELD_DELAY_RANGE)
    logger.debug(f"Simulating field delay of {delay:.2f} seconds")
    time.sleep(delay)

def simulate_page_load_delay():
    """Simulate delay for page loading and reading"""
    delay = random.uniform(*PAGE_LOAD_DELAY_RANGE)
    logger.debug(f"Simulating page load delay of {delay:.2f} seconds")
    time.sleep(delay)

def simulate_submit_delay():
    """Simulate delay before submitting a form"""
    delay = random.uniform(*SUBMIT_DELAY_RANGE)
    logger.debug(f"Simulating submit delay of {delay:.2f} seconds")
    time.sleep(delay)

def random_mouse_movement():
    """Simulate random mouse movements by adding random delays"""
    delay = random.uniform(0.1, 0.5)
    logger.debug(f"Simulating mouse movement delay of {delay:.2f} seconds")
    time.sleep(delay)

def format_cookies_for_json(cookies_dict):
    """Format cookies dictionary into detailed JSON structure."""
    formatted_cookies = []
    current_time = datetime.datetime.now().isoformat('T') + 'Z'
    
    # Sort cookies by name to maintain consistent order
    for key, value in sorted(cookies_dict.items()):
        # Create a small time difference between creation and lastAccessed
        creation_time = current_time
        last_accessed_time = current_time
        
        cookie_obj = {
            "key": key,
            "value": value,
            "domain": "facebook.com",
            "path": "/",
            "hostOnly": False,
            "creation": creation_time,
            "lastAccessed": last_accessed_time
        }
        
        formatted_cookies.append(cookie_obj)
        
    return formatted_cookies

def cookies_dict_to_string(cookies_dict):
    """Convert cookies dictionary to cookie string format."""
    return "; ".join([f"{key}={value}" for key, value in cookies_dict.items()])

def is_valid_email(email):
    """Check if email is valid"""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_regex, email))

def get_random_delay(min_delay=0.5, max_delay=2.0):
    """Get a random delay within the given range"""
    return random.uniform(min_delay, max_delay)

def days_in_month(month, year):
    """Return the number of days in a month"""
    if month in [4, 6, 9, 11]:
        return 30
    elif month == 2:
        # Leap year check
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            return 29
        else:
            return 28
    else:
        return 31