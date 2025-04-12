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

# Set up logging with minimal output
logger = setup_logger("FBAccountCreator", console_level="ERROR")

def create_required_folders():
    """Create necessary folders for the application"""
    folders = ['logs']  # Removed 'accounts' folder
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

def try_with_proxy(proxy_manager, email, email_password, user_data, max_attempts=3):
    """Try to create an account with multiple proxies until success"""
    
    for attempt in range(max_attempts):
        # Get a proxy for this attempt
        proxy = proxy_manager.get_proxy()
        if not proxy:
            print("❌ Failed to get a valid proxy.")
            return False
        
        print(f"\n[{attempt+1}/{max_attempts}] Using proxy: {proxy['ip']}:{proxy['port']}")
        
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
                return result
                
        except requests.exceptions.TooManyRedirects:
            print(f"❌ Proxy connection issue - too many redirects.")
            proxy_manager.remove_current_proxy()
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection error with proxy.")
            proxy_manager.remove_current_proxy()
            
        except requests.exceptions.Timeout:
            print(f"❌ Timeout with proxy.")
            proxy_manager.remove_current_proxy()
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            proxy_manager.remove_current_proxy()
        
        # Wait before trying the next proxy
        if attempt < max_attempts - 1:
            delay = 3 + (attempt * 2)
            print(f"Waiting {delay} seconds before trying the next proxy...")
            time.sleep(delay)
    
    print(f"\n❌ All {max_attempts} proxy attempts failed")
    return False

def main():
    """Main function to start the Facebook account creation process"""
    print("\n=== Facebook Account Creator ===")
    print("This tool creates a Facebook account with a temporary email address.")
    print("You'll need access to the temporary email to receive the verification code.")
    
    # Create required folders
    create_required_folders()
    
    try:
        # Initialize the proxy manager
        proxy_manager = ProxyManager()
        if not proxy_manager.load_proxies():
            print("❌ Failed to load proxies. Exiting...")
            return
        
        # Find working proxies
        print("Testing proxies to find working ones...")
        proxy_manager.find_working_proxies(max_to_test=5, silent=True)
            
        if not proxy_manager.working_proxies:
            print("No working proxies found in initial test. Using all available proxies.")
        
        # Create account generator with user data
        account_gen = AccountGenerator()
        user_data = account_gen.generate_user_data()
        
        # Get email from user
        from utils.user_input import get_user_email
        email, email_password = get_user_email()
        if not email:
            print("❌ No valid email provided. Aborting.")
            return
        
        # Try to create the account with multiple proxies if needed
        max_attempts = CONFIG.get("max_proxy_attempts", 3)
        account_info = try_with_proxy(proxy_manager, email, email_password, user_data, max_attempts)
        
        # Process the result
        if account_info and isinstance(account_info, dict):
            if account_info.get('verification_required', False):
                print("\n=== Verification Required ===")
                print("Please check your email for a verification code from Facebook")
                
                # Get verification code from user
                fb_code = input("\nEnter FB code: ").strip()
                
                if fb_code:
                    # Complete verification
                    if account_info.get('verify_func') and callable(account_info.get('verify_func')):
                        verify_func = account_info.get('verify_func')
                        success = verify_func(fb_code)
                        
                        if success:
                            print("\n✅ Account creation and verification successful!")
                            print(f"\nAccount Information:")
                            print(f"- Name: {account_info['first_name']} {account_info['last_name']}")
                            print(f"- Email: {account_info['email']}")
                            print(f"- Facebook Password: {account_info['password']}")
                            print(f"- User ID: {account_info.get('user_id', 'Unknown')}")
                            print("\nYou can now log in to Facebook with these credentials.")
                        else:
                            print("\n❌ Verification failed. Please try to log in manually.")
                    else:
                        print("\n❌ Could not complete verification. Please try to log in manually.")
                else:
                    print("\n❌ No verification code provided. Please try to log in manually.")
            elif account_info.get('success'):
                print("\n✅ Account creation successful!")
                print(f"\nAccount Information:")
                print(f"- Name: {account_info['first_name']} {account_info['last_name']}")
                print(f"- Email: {account_info['email']}")
                print(f"- Facebook Password: {account_info['password']}")
                print(f"- User ID: {account_info.get('user_id', 'Unknown')}")
                print("\nYou can now log in to Facebook with these credentials.")
            else:
                # Partial account info
                print("\n⚠️ Account created but additional steps may be required.")
                print(f"\nAccount Information:")
                print(f"- Name: {account_info['first_name']} {account_info['last_name']}")
                print(f"- Email: {account_info['email']}")
                print(f"- Facebook Password: {account_info['password']}")
                print("\nTry logging in to Facebook with these credentials and complete any verification steps.")
        else:
            print("\n❌ Account creation failed.")
            print("Try again with a different email or wait before retrying.")
            
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()