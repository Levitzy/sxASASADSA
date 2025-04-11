"""
Save account information to files
"""

import os
import json
import logging
import datetime
import string
import random
from config import ACCOUNTS_DIR
from utils.helpers import format_cookies_for_json, cookies_dict_to_string

logger = logging.getLogger("FBAccountCreator")

class AccountSaver:
    def __init__(self):
        """Initialize the account saver"""
        # Ensure the accounts directory exists
        os.makedirs(ACCOUNTS_DIR, exist_ok=True)
        
    def save_account(self, account_data, user_data, email, email_password, cookies_dict, success=True):
        """Save account information to files"""
        try:
            # Get user ID from cookies or use a placeholder
            user_id = cookies_dict.get('c_user', ''.join(random.choices(string.digits, k=10)))
            
            # Format cookies for saving
            formatted_cookies = format_cookies_for_json(cookies_dict)
            
            # Create cookie string
            cookie_string = cookies_dict_to_string(cookies_dict)
            
            # Save account information
            account_info = {
                "success": success,
                "user_id": user_id,
                "first_name": user_data['first_name'],
                "last_name": user_data['last_name'],
                "email": email,
                "email_password": email_password,
                "fb_password": user_data['password'],
                "gender": "Female" if user_data['gender'] == "1" else "Male",
                "birth_date": f"{user_data['birth_month']}/{user_data['birth_day']}/{user_data['birth_year']}",
                "creation_time": datetime.datetime.now().isoformat(),
                "cookies": formatted_cookies,
                "cookie_string": cookie_string,
                "mobile_cookie_string": cookie_string,
                "device_id": user_data.get('device_id', '')
            }
            
            # Add extra account data if provided
            if account_data:
                account_info.update(account_data)
            
            # Save cookies to file
            cookies_file = os.path.join(ACCOUNTS_DIR, f"fb_account_{user_id}_cookies.json")
            with open(cookies_file, "w", encoding="utf-8") as f:
                json.dump(formatted_cookies, f, indent=2)
                
            # Save account info to file
            info_file = os.path.join(ACCOUNTS_DIR, f"fb_account_{user_id}_info.json")
            with open(info_file, "w", encoding="utf-8") as f:
                json.dump(account_info, f, indent=2)
                
            logger.info(f"Account information saved to {info_file}")
            logger.info(f"Cookies saved to {cookies_file}")
            
            return account_info
            
        except Exception as e:
            logger.error(f"Error saving account information: {str(e)}")
            return None
    
    def save_partial_account(self, user_data, email, email_password, cookies_dict):
        """Save partial account information when registration isn't fully successful"""
        try:
            # Generate a random ID for the file name
            random_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            
            # Format cookies for saving
            formatted_cookies = format_cookies_for_json(cookies_dict)
            
            # Create cookie string
            cookie_string = cookies_dict_to_string(cookies_dict)
            
            # Save partial account info
            partial_account_info = {
                "success": False,
                "partial": True,
                "first_name": user_data['first_name'],
                "last_name": user_data['last_name'],
                "email": email,
                "email_password": email_password,
                "fb_password": user_data['password'],
                "gender": "Female" if user_data['gender'] == "1" else "Male",
                "birth_date": f"{user_data['birth_month']}/{user_data['birth_day']}/{user_data['birth_year']}",
                "creation_time": datetime.datetime.now().isoformat(),
                "cookies": formatted_cookies,
                "cookie_string": cookie_string
            }
            
            # Save to file
            file_path = os.path.join(ACCOUNTS_DIR, f"fb_account_partial_{random_id}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(partial_account_info, f, indent=2)
                
            logger.info(f"Partial account information saved to {file_path}")
            
            return partial_account_info
            
        except Exception as e:
            logger.error(f"Error creating partial account info: {str(e)}")
            return False