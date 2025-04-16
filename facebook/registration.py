"""
Enhanced Facebook registration process with better security handling
"""

import re
import logging
import uuid
import time
import random
import json
from bs4 import BeautifulSoup
from config import FB_MOBILE_HOME, FB_MOBILE_SIGNUP
from facebook.session import FacebookSession
from facebook.verification import VerificationHandler
from utils.helpers import (
    simulate_typing_delay, 
    simulate_field_delay, 
    simulate_page_load_delay,
    simulate_submit_delay
)

logger = logging.getLogger("FBAccountCreator")

class FacebookRegistration:
    def __init__(self, user_data, email, email_password, proxy=None):
        """Initialize Facebook registration with user data"""
        self.user_data = user_data
        self.email = email
        self.email_password = email_password
        self.session = FacebookSession(proxy)
        self.verification_handler = VerificationHandler(self.session)
        self.registration_attempts = 0
        self.max_registration_attempts = 2
        
    def create_account(self):
        """Create a new Facebook account using mobile site"""
        print("\nStarting Facebook account creation...")
        
        # Print user credentials
        print("\n=== Account Information ===")
        print(f"Name: {self.user_data['first_name']} {self.user_data['last_name']}")
        print(f"Gender: {'Female' if self.user_data['gender'] == '1' else 'Male'}")
        print(f"DOB: {self.user_data['birth_month']}/{self.user_data['birth_day']}/{self.user_data['birth_year']}")
        print(f"Email: {self.email}")
        print(f"Password: {self.user_data['password']}")
        
        print("\nAttempting to create Facebook account...")
        
        # Start with warmup requests to make the session look more natural
        self._enhanced_warmup_session()
        
        # Start mobile registration process
        result = self._mobile_registration()
        
        # If mobile registration fails, try desktop registration
        if not result:
            print("Mobile registration failed, trying desktop registration...")
            # Wait before trying a different approach
            time.sleep(random.uniform(3, 5))
            result = self._desktop_registration()
        
        # If desktop registration fails, try API-based registration
        if not result:
            print("Desktop registration failed, trying API registration...")
            # Wait before trying a different approach
            time.sleep(random.uniform(3, 5))
            result = self._api_registration()
        
        # Return partial account info
        if not result:
            print("❌ Account creation failed with all methods")
            
            # Return partial account info
            cookies_dict = self.session.get_cookies_dict()
            if cookies_dict:
                return self._create_partial_account_info()
            
            return False
        
        return result
    
    def _enhanced_warmup_session(self):
        """Perform a more thorough warm-up to look like a real browser"""
        try:
            # First visit google.com (common entry point)
            print("Warming up session...")
            self.session.get('https://www.google.com/search?q=facebook+login', max_redirects=3)
            
            # Random delay
            time.sleep(random.uniform(2, 3))
            
            # Visit Facebook's main page like a real user would
            main_response = self.session.get('https://www.facebook.com/', max_redirects=3)
            
            # Random delay like a human reading the page
            time.sleep(random.uniform(2, 4))
            
            # Visit the help page (looks more natural)
            self.session.get('https://www.facebook.com/help/', max_redirects=3)
            
            # Random delay
            time.sleep(random.uniform(1.5, 2.5))
            
            # Visit another common page to build browsing history
            self.session.get('https://www.facebook.com/policies/', max_redirects=3)
            
            # Random delay
            time.sleep(random.uniform(2, 3))
            
            # Visit about page
            self.session.get('https://www.facebook.com/about/', max_redirects=3)
            
            # Random delay
            time.sleep(random.uniform(1.5, 2.5))
            
            # Set important cookies for browser fingerprinting
            browser_cookies = {
                'locale': 'en_US',
                'wd': f"{random.choice([1280, 1366, 1440, 1920])}x{random.choice([720, 768, 900, 1080])}",
                'dpr': f"{random.choice([1, 1.5, 2])}",
            }
            
            for name, value in browser_cookies.items():
                self.session.set_cookie(name, value)
                
        except Exception as e:
            logger.debug(f"Error during enhanced session warm-up: {str(e)}")
    
    def _mobile_registration(self):
        """Register using Facebook's mobile site with improved anti-detection"""
        self.registration_attempts += 1
        
        try:
            # First, visit the homepage to get cookies and session data
            print("Accessing Facebook...")
            initial_response = self.session.get(FB_MOBILE_HOME, max_redirects=7)
            
            if initial_response.status_code != 200:
                print(f"Failed to access Facebook: {initial_response.status_code}")
                return False
            
            # Human delay - simulating reading the page
            time.sleep(random.uniform(2, 4))
            
            # Try alternative URLs if the main one fails
            signup_urls = [
                "https://m.facebook.com/reg/",
                "https://m.facebook.com/reg/submit/",
                "https://m.facebook.com/r.php",
                "https://m.facebook.com/signup"
            ]
            
            signup_response = None
            signup_soup = None
            reg_form = None
            
            for signup_url in signup_urls:
                try:
                    print(f"Trying signup URL: {signup_url}")
                    
                    # Add delay before clicking signup (like a human)
                    time.sleep(random.uniform(1, 2))
                    
                    signup_response = self.session.get(
                        signup_url,
                        referer=FB_MOBILE_HOME,
                        max_redirects=7
                    )
                    
                    if signup_response.status_code != 200:
                        continue
                    
                    # Parse the signup page to extract form data
                    signup_soup = BeautifulSoup(signup_response.text, 'html.parser')
                    
                    # Check if we find a registration form
                    reg_form = self._find_registration_form(signup_soup)
                    if reg_form:
                        print(f"Found registration form...")
                        break
                
                except Exception as e:
                    print(f"Error accessing signup URL {signup_url}: {str(e)}")
                    continue
            
            # If we couldn't get a registration form from any URL, bail out
            if not signup_response or not signup_soup or not reg_form:
                print("Could not access signup page")
                return False
            
            # Extract form action URL
            form_action = reg_form.get('action', '')
            if not form_action:
                form_action = "https://m.facebook.com/reg/submit/"
            elif not form_action.startswith('http'):
                form_action = f"https://m.facebook.com{form_action}"
            
            # Extract hidden fields and process form
            form_data = self._extract_form_data(reg_form)
            
            # Fill in user data
            form_data = self._fill_registration_form(form_data)
            
            # Add extra headers for better success
            extra_headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                'Accept-Language': 'en-US,en;q=0.9',
                'X-Requested-With': 'XMLHttpRequest',
                'X-FB-LSD': self.session.lsd if self.session.lsd else '',
                'X-FB-DTSG': self.session.fb_dtsg if self.session.fb_dtsg else ''
            }
            
            # Extra: Add Facebook's expected form fields that might be missing
            form_data = self._add_extra_form_fields(form_data)
            
            # Simulate human form filling with more realistic delays
            self._simulate_enhanced_human_form_filling()
            
            # Submit registration form
            print("Submitting registration form...")
            registration_response = self.session.post(
                form_action,
                data=form_data,
                extra_headers=extra_headers,
                referer=signup_response.url,
                max_redirects=7
            )
            
            # Wait after registration before checking result - Facebook often has delays
            time.sleep(random.uniform(3, 5))
            
            # Check for successful registration
            cookies = self.session.get_cookies_dict()
            
            # Debug: print all cookies to see what we have
            print("Cookies after registration:")
            important_cookies = ['c_user', 'xs', 'fr', 'datr', 'sb']
            for cookie_name in important_cookies:
                if cookie_name in cookies:
                    print(f"  {cookie_name}: {cookies[cookie_name]}")
            
            # Check for success indicators
            if "c_user" in cookies and cookies["c_user"]:
                print(f"✅ Registration successful! User ID: {cookies['c_user']}")
                return self._finalize_account(cookies['c_user'])
            
            # Handle various verification pathways
            if any(term in registration_response.url for term in ["checkpoint", "confirmemail", "confirm_email", "confirmation"]):
                print("Registration requires verification...")
                
                # Return account info with verification flag and callback
                return self._create_verification_info()
            
            # Check for other success indicators
            elif "welcome" in registration_response.url or "home" in registration_response.url:
                print("Registration successful based on redirect!")
                # Try to extract user ID from URL
                user_id = self._extract_user_id_from_url(registration_response.url)
                if user_id:
                    return self._finalize_account(user_id)
                return self._finalize_account()
            
            # Check for login form - if present, our registration succeeded
            registration_soup = BeautifulSoup(registration_response.text, 'html.parser')
            login_form = registration_soup.find('form', id='login_form')
            if login_form:
                print("Registration successful! Found login form in response.")
                
                # Wait a bit longer before login attempt to allow Facebook to process the account
                time.sleep(random.uniform(5, 8))
                
                return self._attempt_login_with_credentials()
            
            # Check for verification messages
            if any(phrase in registration_response.text.lower() for phrase in 
                  ["confirmation code", "verification code", "check your email", "verify your account"]):
                print("Detected verification request in the response")
                
                # Return account info with verification flag and callback
                return self._create_verification_info()
            
            # Check for error messages
            error_messages = self._extract_error_messages(registration_soup)
            if error_messages:
                print(f"❌ Registration errors: {', '.join(error_messages)}")
                
                # If this is our first attempt and we have specific errors, retry with adjustments
                if self.registration_attempts < self.max_registration_attempts:
                    if any("email" in err.lower() for err in error_messages):
                        return False
                    
                    # For other errors, try desktop registration
                    return False
            
            # As a last resort, try logging in
            print("No success indicators found. Trying to log in as a fallback.")
            
            # Wait a bit longer before login attempt
            time.sleep(random.uniform(5, 8))
            
            return self._attempt_login_with_credentials()
                
        except Exception as e:
            print(f"❌ Error during registration: {str(e)}")
            return False
    
    def _extract_user_id_from_url(self, url):
        """Extract user ID from URL if present"""
        # Common patterns for user ID in URLs
        patterns = [
            r'user=(\d+)',
            r'uid=(\d+)',
            r'id=(\d+)',
            r'profile\.php\?id=(\d+)',
            r'\/(\d{8,})\/',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _api_registration(self):
        """Try to register using Facebook's API endpoints directly"""
        try:
            print("Attempting API-based registration...")
            
            # Reset session and cookies for a fresh start
            self.session.clear_cookies(preserve_fingerprint=True)
            
            # Use a mobile user agent for this attempt
            mobile_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6.1 Mobile/15E148 Safari/604.1"
            self.session.update_user_agent(mobile_ua)
            
            # Get CSRF tokens first
            token_response = self.session.get('https://m.facebook.com/', max_redirects=7)
            time.sleep(random.uniform(2, 3))
            
            # Extract tokens from the response
            soup = BeautifulSoup(token_response.text, 'html.parser')
            lsd = None
            fb_dtsg = None
            
            # Extract LSD token
            lsd_tag = soup.find('input', {'name': 'lsd'})
            if lsd_tag:
                lsd = lsd_tag.get('value', '')
            
            # Extract FB_DTSG token from scripts
            for script in soup.find_all('script'):
                if script.string and 'fb_dtsg' in script.string:
                    match = re.search(r'"fb_dtsg":"([^"]+)"', script.string)
                    if match:
                        fb_dtsg = match.group(1)
                        break
            
            # Create registration data
            reg_data = {
                'firstname': self.user_data['first_name'],
                'lastname': self.user_data['last_name'],
                'reg_email__': self.email,
                'reg_email_confirmation__': self.email,
                'reg_passwd__': self.user_data['password'],
                'birthday_day': str(self.user_data['birth_day']),
                'birthday_month': str(self.user_data['birth_month']),
                'birthday_year': str(self.user_data['birth_year']),
                'sex': self.user_data['gender'],
                'locale': 'en_US',
                'fb_dtsg': fb_dtsg if fb_dtsg else (self.session.fb_dtsg if self.session.fb_dtsg else ''),
                'lsd': lsd if lsd else (self.session.lsd if self.session.lsd else ''),
                'websubmit': '1',
                'referrer': 'mobile_fb',
                'ccp': '2',
                'reg_instance': str(uuid.uuid4()),
                'reg_impression_id': str(uuid.uuid4()),
                'guid': str(uuid.uuid4()).upper(),
                'contactpoint_type': 'email',
                'submission_request': 'true',
                'terms': 'on',
                'ns': '0',
                'application_locale': 'en_US',
                'is_birthday_verified': 'true',
                'birthday_age': str(2025 - self.user_data['birth_year']),
                'utm_source': '',
                'utm_medium': '',
                'utm_campaign': '',
                'timezone': '-480',
                'device_id': self.user_data.get('device_id', str(uuid.uuid4())),
                'machine_id': self.user_data.get('machine_id', str(uuid.uuid4())),
            }
            
            # Add API-specific headers
            headers = {
                'Origin': 'https://m.facebook.com',
                'Referer': 'https://m.facebook.com/reg/',
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-ASBD-ID': '129477',
                'X-FB-LSD': lsd if lsd else (self.session.lsd if self.session.lsd else ''),
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'X-FB-Friendly-Name': 'RegMobileCreateAccount',
            }
            
            # Simulate human behavior
            time.sleep(random.uniform(3, 5))
            
            # Try direct API submission
            response = self.session.post(
                'https://m.facebook.com/reg/submit/',
                data=reg_data,
                extra_headers=headers,
                max_redirects=7  # Increase redirects limit
            )
            
            # Wait to allow processing
            time.sleep(random.uniform(4, 6))
            
            # Check for success
            cookies = self.session.get_cookies_dict()
            
            # Debug: print all cookies to see what we have
            print("Cookies after API registration:")
            important_cookies = ['c_user', 'xs', 'fr', 'datr', 'sb']
            for cookie_name in important_cookies:
                if cookie_name in cookies:
                    print(f"  {cookie_name}: {cookies[cookie_name]}")
            
            if "c_user" in cookies and cookies["c_user"]:
                print(f"✅ API registration successful! User ID: {cookies['c_user']}")
                return self._finalize_account(cookies['c_user'])
            
            # Check for verification redirect
            if any(term in response.url for term in ["checkpoint", "confirmemail", "confirm_email", "confirmation"]):
                print("API registration requires verification...")
                return self._create_verification_info()
            
            # Try one more login attempt
            print("Trying final login attempt after API registration...")
            time.sleep(random.uniform(3, 5))
            
            return self._attempt_login_with_credentials()
            
        except Exception as e:
            print(f"❌ Error during API registration: {str(e)}")
            return False
    
    def _extract_error_messages(self, soup):
        """Extract error messages from the page"""
        error_messages = []
        
        # Look for standard error containers
        error_selectors = [
            '.errorMessage', 
            '.error', 
            '.errorContent', 
            '#error',
            'div[role="alert"]',
            '.UIMessageBox',
            'div[class*="error"]'
        ]
        
        for selector in error_selectors:
            for element in soup.select(selector):
                message = element.get_text().strip()
                if message:
                    error_messages.append(message)
        
        # Also look for texts that indicate errors
        error_keywords = ['error', 'invalid', 'cannot', 'failed', 'not available', 'try again', 'problem']
        
        for paragraph in soup.find_all(['p', 'div']):
            text = paragraph.get_text().strip().lower()
            if any(keyword in text for keyword in error_keywords):
                error_messages.append(paragraph.get_text().strip())
        
        return error_messages
    
    def _add_extra_form_fields(self, form_data):
        """Add extra fields that Facebook might expect but aren't in the form"""
        # Device information
        form_data['device_id'] = self.user_data.get('device_id', str(uuid.uuid4()))
        form_data['machine_id'] = self.user_data.get('machine_id', str(uuid.uuid4()))
        form_data['locale'] = 'en_US'
        form_data['timezone'] = '-480'  # Pacific Time
        
        # Registration metadata
        form_data['create_timestamp'] = str(int(time.time()))
        form_data['reg_instance'] = str(uuid.uuid4())
        form_data['platform'] = 'android'
        form_data['flow_name'] = 'reg'
        
        # Consent to terms
        form_data['terms'] = '1'
        form_data['data_policy'] = '1'
        form_data['tos'] = '1'
        
        # Other common Facebook form fields
        form_data['websubmit'] = '1'
        form_data['ref'] = 'dbl'
        form_data['referrer'] = ''
        form_data['logger_id'] = str(uuid.uuid4())
        
        # Facebook-specific fields that might help reduce detection
        form_data['reg_impression_id'] = str(uuid.uuid4())
        form_data['guid'] = self.user_data.get('device_id', str(uuid.uuid4())).upper()
        form_data['action_type'] = 'submit'
        form_data['ccp'] = '2'
        form_data['application_locale'] = 'en_US'
        form_data['is_birthday_verified'] = 'true'
        form_data['birthday_age'] = str(2025 - self.user_data['birth_year'])
        
        # Anti-bot prevention
        form_data['had_cp_prefilled'] = '0'
        form_data['had_password_prefilled'] = '0'
        form_data['is_mobile_device'] = 'true'
        
        return form_data
            
    def _desktop_registration(self):
        """Register using Facebook's desktop site as fallback"""
        self.registration_attempts += 1
        
        try:
            print("Trying desktop registration approach...")
            
            # Update user agent to desktop
            desktop_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            self.session.update_user_agent(desktop_ua)
            
            # Clear cookies for a fresh start but preserve browser fingerprinting
            self.session.clear_cookies(preserve_fingerprint=True)
            
            # Wait a bit before trying again
            time.sleep(random.uniform(2, 3))
            
            # Warm up session again with desktop UA
            self.session.get('https://www.google.com/search?q=facebook+create+account', max_redirects=3)
            time.sleep(random.uniform(1.5, 2.5))
            
            self.session.get('https://www.facebook.com/', max_redirects=3)
            time.sleep(random.uniform(1.5, 2.5))
            
            # Visit the regular desktop signup page
            signup_url = "https://www.facebook.com/r.php"
            
            signup_response = self.session.get(
                signup_url,
                referer="https://www.facebook.com/",
                max_redirects=7
            )
            
            if signup_response.status_code != 200:
                print(f"Failed to access desktop signup page: {signup_response.status_code}")
                return False
            
            # Parse the signup page
            signup_soup = BeautifulSoup(signup_response.text, 'html.parser')
            
            # Find registration form
            reg_form = self._find_registration_form(signup_soup)
                
            if not reg_form:
                print("No registration form found on desktop site")
                return False
            
            # Extract form action URL
            form_action = reg_form.get('action', '')
            if not form_action:
                form_action = "https://www.facebook.com/reg/submit/"
            elif not form_action.startswith('http'):
                form_action = f"https://www.facebook.com{form_action}"
            
            # Extract form data
            form_data = self._extract_form_data(reg_form)
            
            # Fill in user data
            form_data = self._fill_registration_form(form_data)
            
            # Add extra form fields for better success chance
            form_data = self._add_extra_form_fields(form_data)
            
            # Add extra headers for better success
            extra_headers = {
                'Origin': 'https://www.facebook.com',
                'Referer': signup_url,
                'Content-Type': 'application/x-www-form-urlencoded',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            # Simulate human form filling
            self._simulate_enhanced_human_form_filling()
            
            # Submit the form
            print("Submitting desktop registration form...")
            registration_response = self.session.post(
                form_action,
                data=form_data,
                extra_headers=extra_headers,
                referer=signup_url,
                max_redirects=7
            )
            
            # Wait after registration to let Facebook process it
            time.sleep(random.uniform(3, 5))
            
            # Check for successful registration
            cookies = self.session.get_cookies_dict()
            
            # Debug: print all cookies to see what we have
            print("Cookies after desktop registration:")
            important_cookies = ['c_user', 'xs', 'fr', 'datr', 'sb']
            for cookie_name in important_cookies:
                if cookie_name in cookies:
                    print(f"  {cookie_name}: {cookies[cookie_name]}")
            
            if "c_user" in cookies and cookies["c_user"]:
                print(f"✅ Desktop registration successful! User ID: {cookies['c_user']}")
                return self._finalize_account(cookies['c_user'])
            
            # Handle verification
            if any(term in registration_response.url for term in ["checkpoint", "confirmemail", "confirm_email", "confirmation"]):
                print("Desktop registration requires verification")
                
                # Return account info with verification flag and callback
                return self._create_verification_info()
            
            # Check for other success indicators
            elif "welcome" in registration_response.url or "home" in registration_response.url:
                print("Desktop registration successful based on redirect!")
                # Try to extract user ID from URL
                user_id = self._extract_user_id_from_url(registration_response.url)
                if user_id:
                    return self._finalize_account(user_id)
                return self._finalize_account()
            
            # Check for registration success or error messages
            registration_soup = BeautifulSoup(registration_response.text, 'html.parser')
            
            # Look for error messages
            error_messages = self._extract_error_messages(registration_soup)
            if error_messages:
                print(f"❌ Desktop registration errors: {', '.join(error_messages)}")
                # No retry for desktop errors, as we've already tried both methods
                
            # Wait before login attempt
            time.sleep(random.uniform(5, 8))
            
            # Try login as fallback
            return self._attempt_login_with_credentials()
            
        except Exception as e:
            print(f"❌ Error during desktop registration: {str(e)}")
            return False
    
    def _find_registration_form(self, soup):
        """Find the registration form in the page using multiple approaches"""
        # Try standard form selectors
        form_selectors = [
            'form[id="mobile-reg-form"]', 
            'form[id="signup-form"]',
            'form[id="reg"]',
            'form[id="registration_form"]',
            'form[action="/reg/submit/"]',
            'form[method="post"]',
            'form[name="reg"]',
            'form[action*="reg"]',
            'form[action*="signup"]',
            'form[action*="register"]'
        ]
        
        for selector in form_selectors:
            form = soup.select_one(selector)
            if form:
                return form
        
        # Look for common registration form fields in any form
        registration_field_patterns = [
            'firstname', 'lastname', 'email', 'reg_email', 'password', 'reg_passwd',
            'birthday', 'gender', 'sex', 'name_first', 'name_last'
        ]
        
        for form in soup.find_all('form'):
            for input_field in form.find_all('input'):
                field_name = input_field.get('name', '').lower()
                for pattern in registration_field_patterns:
                    if pattern in field_name:
                        return form
        
        # Look for forms with signup/register buttons
        for form in soup.find_all('form'):
            buttons = form.find_all(['button', 'input'], type='submit')
            for button in buttons:
                button_text = button.get_text().lower() if hasattr(button, 'get_text') else ''
                button_value = button.get('value', '').lower()
                button_id = button.get('id', '').lower()
                button_name = button.get('name', '').lower()
                
                signup_terms = ['sign up', 'signup', 'register', 'join', 'create', 'submit']
                
                for term in signup_terms:
                    if (term in button_text or term in button_value or 
                        term in button_id or term in button_name):
                        return form
        
        # Try looking for registration areas based on text content
        registration_areas = soup.find_all(['h2', 'h3', 'div'], string=lambda s: s and any(term in s.lower() for term in ['sign up', 'create account', 'join facebook', 'registration']))
        
        for area in registration_areas:
            # Look for the closest form
            form = area.find_parent('form')
            if form:
                return form
        
        # If all else fails, just try to find any form that seems like a registration form
        for form in soup.find_all('form'):
            # Count input fields (registration forms typically have many)
            inputs = form.find_all('input')
            if len(inputs) >= 5:  # Most registration forms have at least 5 fields
                return form
                
        # If we've tried everything and still haven't found a form, return None
        return None
    
    def _extract_form_data(self, form):
        """Extract all form fields and values"""
        form_data = {}
        
        # Extract all input fields
        for input_field in form.find_all('input'):
            name = input_field.get('name')
            value = input_field.get('value', '')
            if name:
                form_data[name] = value
        
        # Extract select fields if any
        for select_field in form.find_all('select'):
            name = select_field.get('name')
            if name:
                # Try to find selected option
                selected_option = select_field.find('option', selected=True)
                if selected_option:
                    value = selected_option.get('value', '')
                else:
                    # If no option is selected, use the first option
                    first_option = select_field.find('option')
                    value = first_option.get('value', '') if first_option else ''
                form_data[name] = value
        
        # Extract textarea fields if any
        for textarea_field in form.find_all('textarea'):
            name = textarea_field.get('name')
            if name:
                value = textarea_field.string if textarea_field.string else ''
                form_data[name] = value
        
        # Look for tokens in scripts
        script_content = ""
        for script in form.find_all('script'):
            if script.string:
                script_content += script.string
                
        # Also look in all scripts on the page
        for script in form.find_all('script', src=False):
            if script.string:
                script_content += script.string
                
        # Extract common token patterns from script
        token_patterns = [
            r'name="lsd" value="([^"]+)"',
            r'name="jazoest" value="([^"]+)"',
            r'"__spin_r":"([^"]+)"',
            r'"__spin_t":"([^"]+)"',
            r'"__dyn":"([^"]+)"',
            r'"__csr":"([^"]+)"',
            r'"fbdscid":"([^"]+)"',
            r'"fb_dtsg":"([^"]+)"'
        ]
        
        for pattern in token_patterns:
            match = re.search(pattern, script_content)
            if match:
                token_name = pattern.split('"')[1]
                token_value = match.group(1)
                if token_name not in form_data:
                    form_data[token_name] = token_value
        
        # Add submit button if present
        submit_button = form.find('button', {'type': 'submit'}) or form.find('input', {'type': 'submit'})
        if submit_button:
            name = submit_button.get('name')
            value = submit_button.get('value', '')
            if name and name not in form_data:
                form_data[name] = value
        
        return form_data
    
    def _fill_registration_form(self, form_data):
        """Fill out the registration form with user data"""
        user_data = self.user_data
        
        # Special handling for birthday in mobile site - may use separate fields or a combined field
        if 'birthday_day' in form_data or 'birthday[day]' in form_data:
            # Separate day field
            key = 'birthday_day' if 'birthday_day' in form_data else 'birthday[day]'
            form_data[key] = str(user_data['birth_day'])
            
        if 'birthday_month' in form_data or 'birthday[month]' in form_data:
            # Separate month field
            key = 'birthday_month' if 'birthday_month' in form_data else 'birthday[month]'
            form_data[key] = str(user_data['birth_month'])
            
        if 'birthday_year' in form_data or 'birthday[year]' in form_data:
            # Separate year field
            key = 'birthday_year' if 'birthday_year' in form_data else 'birthday[year]'
            form_data[key] = str(user_data['birth_year'])
            
        # Desktop site may have different field names
        if 'day' in form_data:
            form_data['day'] = str(user_data['birth_day'])
        if 'month' in form_data:
            form_data['month'] = str(user_data['birth_month'])
        if 'year' in form_data:
            form_data['year'] = str(user_data['birth_year'])
            
        # Birthday as a combined field
        if 'birthday' in form_data:
            form_data['birthday'] = f"{user_data['birth_month']}/{user_data['birth_day']}/{user_data['birth_year']}"
            
        # Age-based field (some mobile forms use this)
        if 'birthday_age' in form_data:
            import datetime
            current_year = datetime.datetime.now().year
            age = current_year - user_data['birth_year']
            form_data['birthday_age'] = str(age)
        
        # Fill in name fields with various possible field names
        name_field_patterns = {
            'firstname': user_data['first_name'],
            'lastname': user_data['last_name'],
            'first_name': user_data['first_name'],
            'last_name': user_data['last_name'],
            'name_first': user_data['first_name'],
            'name_last': user_data['last_name'],
            'full_name': f"{user_data['first_name']} {user_data['last_name']}",
            # Also add exact field names for desktop site
            'firstName': user_data['first_name'],
            'lastName': user_data['last_name'],
        }
        
        for field_pattern, value in name_field_patterns.items():
            for field in list(form_data.keys()):
                if field_pattern.lower() in field.lower():
                    form_data[field] = value
        
        # Set email fields - try all possible variations
        email_field_patterns = ['email', 'reg_email', 'contactpoint', 'email_address', 'emailaddress']
        for pattern in email_field_patterns:
            for field in list(form_data.keys()):
                if pattern in field.lower():
                    form_data[field] = self.email
                    
        # Set confirmation email if needed
        confirmation_patterns = ['confirm', 'verification', 'repeat']
        for pattern in confirmation_patterns:
            for field in list(form_data.keys()):
                if pattern in field.lower() and any(email_pattern in field.lower() for email_pattern in email_field_patterns):
                    form_data[field] = self.email
        
        # Set password fields
        password_patterns = ['pass', 'passwd', 'password']
        for pattern in password_patterns:
            for field in list(form_data.keys()):
                if pattern in field.lower():
                    form_data[field] = user_data['password']
        
        # Set gender fields
        gender_patterns = ['sex', 'gender']
        for pattern in gender_patterns:
            for field in list(form_data.keys()):
                if pattern in field.lower():
                    form_data[field] = user_data['gender']
        
        # Add privacy policy/terms acceptance
        terms_patterns = ['terms', 'privacy', 'tos', 'policy', 'agree']
        for pattern in terms_patterns:
            for field in list(form_data.keys()):
                if pattern in field.lower() and form_data[field] in ('', '0'):
                    form_data[field] = '1'  # Accept terms
        
        # Add common fields for registration
        common_fields = {
            'websubmit': '1',
            'referrer': 'mobile_fb',
            'locale': 'en_US',
            'reg_instance': str(uuid.uuid4()),
            'contactpoint_type': 'email',
            'submission_request': 'true',
            'is_birthday_verified': 'true',
            'device_id': user_data.get('device_id', str(uuid.uuid4()))
        }
        
        for field, value in common_fields.items():
            if field not in form_data:
                form_data[field] = value
                
        return form_data
    
    def _simulate_enhanced_human_form_filling(self):
        """Simulate human behavior with more realistic delays and variations"""
        # Simulate reading form before filling
        time.sleep(random.uniform(2, 4))
        
        # Simulate typing and field navigation with random pauses
        for _ in range(6):  # For each form field
            # Simulate typing
            typing_time = random.uniform(1, 3)
            time.sleep(typing_time)
            
            # Simulate pause between fields (as if tabbing or clicking next field)
            field_pause = random.uniform(0.5, 1.5)
            time.sleep(field_pause)
        
        # Simulate reviewing form before submission
        review_time = random.uniform(2, 4)
        time.sleep(review_time)
        
        # Simulate final pause before clicking submit
        submit_pause = random.uniform(1, 2)
        time.sleep(submit_pause)
    
    def _attempt_login_with_credentials(self):
        """Attempt to log in with the credentials we created with improved handling"""
        print("Attempting to log in with credentials...")
        
        try:
            # Wait a bit before attempting login (simulate human behavior)
            time.sleep(random.uniform(3, 5))
            
            # Use the mobile login page
            login_url = "https://m.facebook.com/login/"
            
            # First, visit the login page to get the form and tokens
            login_page_response = self.session.get(login_url, max_redirects=7)
            
            if login_page_response.status_code != 200:
                print(f"Failed to access login page: {login_page_response.status_code}")
                
                # Try alternate login URL
                login_url = "https://m.facebook.com/login.php"
                login_page_response = self.session.get(login_url, max_redirects=7)
                
                if login_page_response.status_code != 200:
                    print(f"Failed to access alternate login page: {login_page_response.status_code}")
                    return False
            
            # Parse login page
            login_soup = BeautifulSoup(login_page_response.text, 'html.parser')
            
            # Find login form
            login_form = login_soup.find('form', id='login_form') or login_soup.find('form', action='/login/')
            
            if not login_form:
                print("No login form found on login page")
                
                # Check if we already have a c_user cookie (might have auto-logged in)
                if self.session.has_cookie('c_user'):
                    user_id = self.session.get_cookie('c_user')
                    if user_id:
                        print(f"Found c_user cookie without login: {user_id}")
                        return self._finalize_account(user_id)
                    
                return False
            
            # Extract form action
            form_action = login_form.get('action', '')
            if not form_action:
                form_action = "https://m.facebook.com/login/device-based/regular/login/"
            elif not form_action.startswith('http'):
                form_action = f"https://m.facebook.com{form_action}"
            
            # Extract form fields
            login_data = {}
            for input_field in login_form.find_all('input'):
                name = input_field.get('name')
                value = input_field.get('value', '')
                if name:
                    login_data[name] = value
            
            # Add credentials
            email_fields = ['email', 'username', 'login', 'identity']
            email_field_found = False
            for field in email_fields:
                if field in login_data:
                    login_data[field] = self.email
                    email_field_found = True
            
            # If no standard email field was found, look for anything that might be an email field
            if not email_field_found:
                for field in login_data.keys():
                    if any(term in field.lower() for term in ['email', 'user', 'login', 'ident']):
                        login_data[field] = self.email
                        email_field_found = True
            
            password_fields = ['pass', 'password']
            password_field_found = False
            for field in password_fields:
                if field in login_data:
                    login_data[field] = self.user_data['password']
                    password_field_found = True
            
            # If no standard password field was found, look for anything that might be a password field
            if not password_field_found:
                for field in login_data.keys():
                    if 'pass' in field.lower():
                        login_data[field] = self.user_data['password']
                        password_field_found = True
            
            # Add common login fields
            login_data.update({
                'locale': 'en_US',
                'login': '1',
                'persistent': '1',  # Keep logged in
                'login_source': 'mobile_web',
                'default_persistent': '1'
            })
            
            # If we have fb_dtsg, add it
            if self.session.fb_dtsg:
                login_data['fb_dtsg'] = self.session.fb_dtsg
            
            # If we have lsd, add it
            if self.session.lsd:
                login_data['lsd'] = self.session.lsd
            
            # Add extra headers for login
            extra_headers = {
                'Origin': 'https://m.facebook.com',
                'Referer': login_url,
                'Content-Type': 'application/x-www-form-urlencoded',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            # Simulate human behavior
            time.sleep(random.uniform(1, 2))  # Reading the form
            time.sleep(random.uniform(1, 2))  # Typing email
            time.sleep(random.uniform(1, 2))  # Typing password
            time.sleep(random.uniform(1, 2))  # Final pause before submit
            
            # Submit login form with increased redirects
            print("Submitting login form...")
            login_response = self.session.post(
                form_action,
                data=login_data,
                extra_headers=extra_headers,
                referer=login_url,
                max_redirects=10  # Increase redirects limit
            )
            
            # Wait longer after login
            time.sleep(random.uniform(3, 5))
            
            # Get cookies after login
            cookies = self.session.get_cookies_dict()
            
            # Debug: print all cookies to see what we have
            print("Cookies after login attempt:")
            important_cookies = ['c_user', 'xs', 'fr', 'datr', 'sb']
            for cookie_name in important_cookies:
                if cookie_name in cookies:
                    print(f"  {cookie_name}: {cookies[cookie_name]}")
            
            # Check for c_user cookie
            if "c_user" in cookies and cookies["c_user"]:
                print(f"Login successful! Found c_user cookie: {cookies['c_user']}")
                return self._finalize_account(cookies['c_user'])
            
            # Check for specific verification pathways
            if "checkpoint" in login_response.url or "confirmation" in login_response.url:
                print("Login requires verification")
                
                # Return account info with verification flag and callback
                return self._create_verification_info()
            
            # Check for login success based on URL patterns
            if "home.php" in login_response.url or "feed" in login_response.url:
                print("Login successful based on redirect URL!")
                
                # Try to extract user ID from URL
                user_id = self._extract_user_id_from_url(login_response.url)
                if user_id:
                    return self._finalize_account(user_id)
                return self._finalize_account()
            
            # Try visiting the homepage as a fallback
            return self._visit_homepage_for_cookies()
        
        except Exception as e:
            print(f"Error during login attempt: {str(e)}")
            return False
    
    def _visit_homepage_for_cookies(self):
        """Visit Facebook homepage to try to get cookies"""
        print("Visiting Facebook homepage to get cookies...")
        
        try:
            # Wait a bit before visiting homepage
            time.sleep(random.uniform(2, 3))
            
            # Visit homepage
            home_response = self.session.get('https://m.facebook.com/', max_redirects=7)
            
            # Get cookies
            cookies = self.session.get_cookies_dict()
            
            # Debug: print all cookies to see what we have
            print("Cookies after visiting homepage:")
            important_cookies = ['c_user', 'xs', 'fr', 'datr', 'sb']
            for cookie_name in important_cookies:
                if cookie_name in cookies:
                    print(f"  {cookie_name}: {cookies[cookie_name]}")
            
            # Check for c_user cookie
            if "c_user" in cookies and cookies["c_user"]:
                print(f"Success! Found c_user cookie: {cookies['c_user']}")
                return self._finalize_account(cookies['c_user'])
            
            # Check if we're at a verification page
            if "checkpoint" in home_response.url or "confirm" in home_response.url:
                print("Redirected to verification page...")
                return self._create_verification_info()
            
            # Try to extract user ID from homepage content
            try:
                home_soup = BeautifulSoup(home_response.text, 'html.parser')
                for script in home_soup.find_all('script'):
                    if script.string and 'USER_ID' in script.string:
                        match = re.search(r'"USER_ID":"(\d+)"', script.string)
                        if match:
                            user_id = match.group(1)
                            print(f"Found USER_ID in script: {user_id}")
                            return self._finalize_account(user_id)
            except Exception as e:
                print(f"Error extracting USER_ID: {str(e)}")
            
            # One more attempt - load the profile page
            print("Trying to visit profile page...")
            time.sleep(random.uniform(1.5, 2.5))
            
            profile_response = self.session.get('https://m.facebook.com/profile.php', max_redirects=7)
            
            # Get updated cookies
            cookies = self.session.get_cookies_dict()
            
            # Check for c_user cookie
            if "c_user" in cookies and cookies["c_user"]:
                print(f"Success! Found c_user cookie: {cookies['c_user']}")
                return self._finalize_account(cookies['c_user'])
            
            # Check if we're at a verification page
            if "checkpoint" in profile_response.url or "confirm" in profile_response.url:
                print("Redirected to verification page from profile...")
                return self._create_verification_info()
            
            # Try to extract user ID from URL
            user_id = self._extract_user_id_from_url(profile_response.url)
            if user_id:
                print(f"Found user ID in profile URL: {user_id}")
                return self._finalize_account(user_id)
            
            print("No c_user cookie found. Account creation may have failed.")
            
            # Create a partial account info
            return self._create_partial_account_info()
        
        except Exception as e:
            print(f"Error visiting homepage: {str(e)}")
            return self._create_partial_account_info()
    
    def _create_partial_account_info(self):
        """Create partial account info when we can't get the c_user cookie"""
        print("Creating partial account info...")
        
        return {
            'success': False,
            'partial': True,
            'first_name': self.user_data['first_name'],
            'last_name': self.user_data['last_name'],
            'email': self.email,
            'password': self.user_data['password'],
            'gender': "Female" if self.user_data['gender'] == "1" else "Male"
        }
    
    def _create_verification_info(self):
        """Create account info with verification callback"""
        print("Account created but requires verification...")
        
        # Define the verification function that will be called later
        def verify_with_code(code):
            return self.verification_handler.handle_verification_code(code)
        
        # Return account info with verification flag and callback
        return {
            'verification_required': True,
            'first_name': self.user_data['first_name'],
            'last_name': self.user_data['last_name'],
            'email': self.email,
            'password': self.user_data['password'],
            'gender': "Female" if self.user_data['gender'] == "1" else "Male",
            'verify_func': verify_with_code
        }
    
    def _finalize_account(self, user_id=None):
        """Finalize account creation and return account data"""
        print("Finalizing account creation...")
        
        try:
            # Get cookies
            cookies_dict = self.session.get_cookies_dict()
            
            # Check for c_user cookie (user ID)
            c_user = cookies_dict.get('c_user', '')
            
            # Use provided user ID or c_user cookie
            user_id = user_id or c_user
            
            if user_id:
                print(f"Account created successfully! User ID: {user_id}")
                
                # Return account information
                return {
                    'success': True,
                    'user_id': user_id,
                    'first_name': self.user_data['first_name'],
                    'last_name': self.user_data['last_name'],
                    'email': self.email,
                    'password': self.user_data['password'],
                    'gender': "Female" if self.user_data['gender'] == "1" else "Male"
                }
            else:
                # One last attempt - try to infer user_id from other cookies
                inferred_user_id = self._infer_user_id_from_cookies(cookies_dict)
                
                if inferred_user_id:
                    print(f"Inferred user ID: {inferred_user_id} from other cookies")
                    
                    # Return account information with inferred ID
                    return {
                        'success': True,
                        'user_id': inferred_user_id,
                        'first_name': self.user_data['first_name'],
                        'last_name': self.user_data['last_name'],
                        'email': self.email,
                        'password': self.user_data['password'],
                        'gender': "Female" if self.user_data['gender'] == "1" else "Male"
                    }
                
                # If we still don't have a user ID, create partial info
                return self._create_partial_account_info()
                
        except Exception as e:
            print(f"Error finalizing account: {str(e)}")
            return self._create_partial_account_info()
            
    def _infer_user_id_from_cookies(self, cookies_dict):
        """Try to infer user ID from other cookies"""
        try:
            # Check for xs cookie - it contains user ID sometimes
            if 'xs' in cookies_dict:
                xs_parts = cookies_dict['xs'].split(':')
                if len(xs_parts) >= 2 and xs_parts[0].isdigit():
                    return xs_parts[0]
            
            # Look for fr cookie - sometimes contains user ID
            if 'fr' in cookies_dict:
                fr_parts = cookies_dict['fr'].split('.')
                for part in fr_parts:
                    if part.isdigit() and len(part) > 8:
                        return part
            
            # Look for other cookies that might contain a user ID
            user_id_cookies = ['i_user', 'presence', 'a_user']
            for cookie_name in user_id_cookies:
                if cookie_name in cookies_dict and cookies_dict[cookie_name].isdigit():
                    return cookies_dict[cookie_name]
            
            return None
        except Exception as e:
            print(f"Error inferring user ID: {str(e)}")
            return None