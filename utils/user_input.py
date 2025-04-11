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
            logger.info(f"Valid email provided: {email}")
            return email, email_password
        
        print("Invalid email format. Please enter a valid email address.")
        attempts += 1
    
    logger.error("Maximum attempts reached for email input")
    return None, None

def get_verification_info():
    """Get verification code or link from user"""
    print("\n=== Email Verification Required ===")
    print("Facebook sent a verification email to your temporary email address.")
    print("Please check your email and provide either:")
    print("1. The verification link (starts with http/https), or")
    print("2. The verification code (usually 6-8 digits)")
    
    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts:
        verification_info = input("Enter verification link or code: ").strip()
        
        # Check if it's a URL
        if verification_info.startswith(('http://', 'https://')):
            logger.info("User provided a verification link")
            return verification_info
            
        # Check if it's a numeric code
        if re.match(r'^\d{4,8}$', verification_info):
            logger.info("User provided a verification code")
            return verification_info
            
        # Check for FB- prefixed code
        if verification_info.startswith('FB-') and len(verification_info) > 3:
            if re.match(r'^FB-\d{4,8}$', verification_info):
                logger.info("User provided an FB- prefixed code")
                return verification_info
                
        print("Invalid input. Please enter a valid verification link (https://...) or code (numeric digits).")
        attempts += 1
    
    logger.error("Maximum attempts reached for verification info input")
    return None

def get_debug_choice():
    """Get user choice for debug mode"""
    print("\n=== Debug Options ===")
    print("1. Run normally")
    print("2. Run in debug mode (verbose logging)")
    print("3. Exit")
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        return False
    elif choice == "2":
        return True
    else:
        return None  # Exit