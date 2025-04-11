#!/usr/bin/env python3
"""
Main entry point for Facebook Account Creator
"""

import os
import sys
import time
import requests
from utils.logger import setup_logger
from proxies.proxy_manager import ProxyManager
from account.generator import AccountGenerator
from facebook.registration import FacebookRegistration
from config import CONFIG

# Set up logging
logger = setup_logger("FBAccountCreator")

def create_required_folders():
    """Create necessary folders for the application"""
    folders = ['logs', 'accounts']
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    logger.info("Required folders created")

def try_with_proxy(proxy_manager, email, email_password, user_data, max_attempts=3):
    """Try to create an account with multiple proxies until success"""
    
    for attempt in range(max_attempts):
        # Get a proxy for this attempt
        proxy = proxy_manager.get_proxy()
        if not proxy:
            logger.error("Failed to get a valid proxy. Exiting...")
            return False
        
        logger.info(f"Attempt {attempt+1}/{max_attempts} using proxy: {proxy['ip']}:{proxy['port']}")
        
        try:
            # Initialize Facebook registration with proxy and user data
            fb_reg = FacebookRegistration(
                user_data=user_data,
                email=email,
                email_password=email_password,
                proxy=proxy
            )
            
            # Try to create account
            result = fb_reg.create_account()
            
            # If successful or partial account created, return the result
            if result:
                logger.info(f"Account creation attempt {attempt+1} successful")
                return result
                
        except requests.exceptions.TooManyRedirects:
            logger.error(f"Proxy {proxy['ip']}:{proxy['port']} caused too many redirects. Facebook may be blocking this proxy.")
            # Remove this proxy from the working list
            proxy_manager.remove_current_proxy()
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error with proxy {proxy['ip']}:{proxy['port']}. The proxy may be down.")
            proxy_manager.remove_current_proxy()
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout with proxy {proxy['ip']}:{proxy['port']}. The proxy may be slow.")
            proxy_manager.remove_current_proxy()
            
        except Exception as e:
            logger.error(f"Error with proxy {proxy['ip']}:{proxy['port']}: {str(e)}")
            proxy_manager.remove_current_proxy()
        
        # Wait before trying the next proxy to avoid rate limiting
        if attempt < max_attempts - 1:
            delay = 5 + (attempt * 3)  # Increase delay with each failure
            logger.info(f"Waiting {delay} seconds before trying the next proxy...")
            time.sleep(delay)
    
    logger.error(f"All {max_attempts} proxy attempts failed")
    return False

def main():
    """Main function to start the Facebook account creation process"""
    print("\n=== Facebook Account Creator - Enhanced Version ===")
    print("This tool helps you create a Facebook account with your own temp email address.")
    print("You'll need to have access to a temporary email service (like temp-mail.org, mail.tm, etc.)")
    print("The script will guide you through the process and handle Facebook registration.\n")
    
    logger.info("Starting Facebook account creator")
    
    # Create required folders
    create_required_folders()
    
    try:
        # Initialize the proxy manager
        proxy_manager = ProxyManager()
        if not proxy_manager.load_proxies():
            logger.error("Failed to load proxies. Exiting...")
            return
        
        # Try to find working proxies first
        if CONFIG.get("test_proxies_first", True):
            print("Testing proxies to find working ones... (this may take a few minutes)")
            proxy_manager.find_working_proxies(max_to_test=5)  # Test a few to save time
            
            if not proxy_manager.working_proxies:
                print("\nNo working proxies found in initial test. Using all available proxies.")
        
        # Create account generator with user data
        account_gen = AccountGenerator()
        user_data = account_gen.generate_user_data()
        
        # Get email from user
        from utils.user_input import get_user_email
        email, email_password = get_user_email()
        if not email:
            logger.error("Failed to get valid email. Aborting.")
            return
        
        # Try to create the account with multiple proxies if needed
        max_attempts = CONFIG.get("max_proxy_attempts", 3)
        result = try_with_proxy(proxy_manager, email, email_password, user_data, max_attempts)
        
        # Process the result
        if result and isinstance(result, dict) and result.get('success'):
            logger.info("Account creation successful!")
            print("\n=== Account Creation Successful! ===")
            print(f"Account details saved to accounts/fb_account_{result['user_id']}_info.json")
            print(f"\nAccount Information:")
            print(f"- Name: {result['first_name']} {result['last_name']}")
            print(f"- Email: {result['email']}")
            print(f"- Facebook Password: {result['fb_password']}")
            print(f"- User ID: {result['user_id']}")
            print(f"- Gender: {result['gender']}")
            print(f"- Birth Date: {result['birth_date']}")
            print("\nYou can now log in to Facebook with these credentials.")
        elif result and isinstance(result, dict):
            # We got partial account info
            logger.warning("Created partial account.")
            print("\n=== Partial Account Created ===")
            print("The account may require additional verification steps.")
            print(f"\nPartial Account Information:")
            print(f"- Name: {result['first_name']} {result['last_name']}")
            print(f"- Email: {result['email']}")
            print(f"- Facebook Password: {result['fb_password']}")
            print(f"- Gender: {result['gender']}")
            print(f"- Birth Date: {result['birth_date']}")
            print("\nTry logging in to Facebook with these credentials and complete any remaining verification steps.")
            
            # Extra hint for users
            print("\nTIP: Facebook might require additional verification when you log in for the first time.")
            print("Try logging in from a web browser instead of the mobile app for easier verification.")
        else:
            logger.error("Account creation failed")
            print("\n=== Account Creation Failed ===")
            print("Failed to create Facebook account after multiple attempts. Check the logs for details.")
            print("You may need to try again with a different email or wait before retrying.")
            
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        print("\n=== Error ===")
        print(f"An unexpected error occurred: {str(e)}")
        print("Check the logs for more details.")

if __name__ == "__main__":
    main()