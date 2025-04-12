"""
Functions for getting user input
"""

import re
import logging
from utils.helpers import is_valid_email

logger = logging.getLogger("FBAccountCreator")

def get_user_email():
    """Get email address from user input"""
    print("\n=== Email Information ===")
    print("You need to provide a temporary email address (from services like temp-mail.org, mail.tm, etc.)")
    
    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts:
        email = input("Enter your temporary email address: ").strip()
        
        if is_valid_email(email):
            # Ask for optional password storage (user can leave blank)
            email_password = input("Optional: Enter the email password (if you want to save it): ").strip()
            return email, email_password
        
        print("Invalid email format. Please enter a valid email address.")
        attempts += 1
    
    print("Maximum attempts reached for email input")
    return None, None

def get_verification_code():
    """Get verification code from user"""
    verification_code = input("\nEnter FB code: ").strip()
    
    # Check if it's a URL (user pasted a link instead of code)
    if verification_code.startswith(('http://', 'https://')):
        print("That appears to be a URL. Please enter just the verification code from the email.")
        verification_code = input("Enter FB code only: ").strip()
            
    # Check if it's a numeric code or FB- prefixed code
    if re.match(r'^\d{4,}$', verification_code) or (verification_code.startswith('FB-') and re.match(r'^FB-\d{4,}$', verification_code)):
        return verification_code.strip()
    
    # If code format is invalid but user entered something, return it anyway
    if verification_code:
        return verification_code.strip()
    
    return None