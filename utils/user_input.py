"""
Enhanced functions for getting user input
"""

import re
import logging
import time
from utils.helpers import is_valid_email

logger = logging.getLogger("FBAccountCreator")

def get_user_email():
    """Get email address from user input"""
    print("\n=== Email Information ===")
    print("You need to provide a temporary email address (from services like temp-mail.org, mail.tm, etc.)")
    print("Facebook has high security measures, so make sure this is a fresh email not previously used.")
    
    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts:
        email = input("Enter your temporary email address: ").strip()
        
        if is_valid_email(email):
            # Check for obvious temporary email patterns that Facebook might block
            risky_patterns = ['temp', 'disposable', 'throwaway', 'fake']
            
            if any(pattern in email.lower() for pattern in risky_patterns):
                print("Warning: This email contains patterns that Facebook might detect as temporary.")
                print("Consider using a less obvious temporary mail service.")
                confirmation = input("Continue with this email anyway? (y/n): ").strip().lower()
                if confirmation != 'y':
                    attempts += 1
                    continue
            
            # Ask for optional password storage (user can leave blank)
            email_password = input("Optional: Enter the email password (if you want to save it): ").strip()
            return email, email_password
        
        print("Invalid email format. Please enter a valid email address.")
        attempts += 1
    
    print("Maximum attempts reached for email input")
    return None, None

def verify_email_access(email, email_password=None):
    """Verify that the user has access to the email"""
    print("\n=== Verifying Email Access ===")
    print(f"Please confirm you have access to: {email}")
    print("Facebook will likely send a verification code to this address.")
    
    confirmation = input("Do you have access to this email inbox right now? (y/n): ").strip().lower()
    if confirmation != 'y':
        print("You must have access to the email to complete registration.")
        while confirmation != 'y':
            time.sleep(1)
            confirmation = input("Please confirm when you have access to the email (y to continue): ").strip().lower()
    
    print("Great! Continue with the registration process.")
    return True

def get_verification_code():
    """Get verification code from user with improved validation"""
    print("\n=== Email Verification ===")
    print("Check your email inbox (and spam folder) for a verification code from Facebook.")
    print("The code might look like 'FB-123456' or just '123456'.")
    
    verification_code = input("\nEnter FB code: ").strip()
    
    # Check if it's a URL (user pasted a link instead of code)
    if verification_code.startswith(('http://', 'https://')):
        print("That appears to be a URL. Please enter just the verification code from the email.")
        print("The code is typically 6-8 digits, sometimes with an 'FB-' prefix.")
        verification_code = input("Enter FB code only: ").strip()
            
    # Clean up the code - remove any spaces, FB- prefix is optional
    verification_code = verification_code.replace(" ", "")
    
    # If code contains FB-, keep it as is, otherwise check if it's numeric
    if verification_code.upper().startswith('FB-'):
        if re.match(r'^FB-\d{4,8}$', verification_code, re.IGNORECASE):
            return verification_code.upper()  # Return in uppercase
    elif re.match(r'^\d{4,8}$', verification_code):
        # Some FB codes need the FB- prefix
        if len(verification_code) >= 6:
            return verification_code
    
    # If we got here, code format might be unusual, but we'll still try it
    if verification_code:
        print("Note: The code format is unusual, but we'll try it anyway.")
        return verification_code.strip()
    
    # If empty code
    print("No code entered. Please check your email and try again.")
    return None