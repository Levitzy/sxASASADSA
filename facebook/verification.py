"""
Facebook verification process handlers
"""

import re
import logging
import time
import random
from bs4 import BeautifulSoup
from utils.helpers import simulate_typing_delay, simulate_submit_delay, simulate_field_delay

logger = logging.getLogger("FBAccountCreator")

class VerificationHandler:
    def __init__(self, session):
        """Initialize the verification handler"""
        self.session = session
    
    def handle_verification(self, response):
        """Handle Facebook verification steps"""
        print("Handling verification process...")
        
        # First check if it's a simple email verification
        if "email" in response.url.lower() and ("confirm" in response.url.lower() or "verify" in response.url.lower()):
            return self.handle_email_verification(response)
        
        try:
            # Parse the verification page
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text().lower()
            
            # Try to determine what type of verification is needed
            verification_type = "unknown"
            
            if re.search(r"(confirm.*email|verify.*email|check.*inbox)", page_text, re.IGNORECASE):
                verification_type = "email"
            elif re.search(r"(phone|mobile|text|sms)", page_text, re.IGNORECASE):
                verification_type = "phone"
            elif re.search(r"(captcha|security.check|confirm.*not.*robot)", page_text, re.IGNORECASE):
                verification_type = "captcha"
            
            print(f"Detected verification type: {verification_type}")
            
            if verification_type == "email":
                return self.handle_email_verification(response)
            elif verification_type in ["phone", "captcha"]:
                print(f"Cannot automatically handle {verification_type} verification")
                return False
            else:
                print("Unknown verification type. Trying generic approach...")
                
                # Look for a form we might be able to submit
                verification_form = soup.find('form')
                
                if not verification_form:
                    print("No verification form found")
                    return False
                    
                # Extract form data
                form_data = {}
                for input_field in verification_form.find_all('input'):
                    name = input_field.get('name')
                    value = input_field.get('value', '')
                    if name:
                        form_data[name] = value
                
                # Get form action
                form_action = verification_form.get('action', '')
                if not form_action.startswith('http'):
                    # Handle relative URLs
                    if form_action.startswith('/'):
                        form_action = f"https://m.facebook.com{form_action}"
                    else:
                        form_action = f"https://m.facebook.com/{form_action}"
                
                # If no action, use current URL
                if not form_action:
                    form_action = response.url
                
                # Find submit button
                submit_button = verification_form.find('button', {'type': 'submit'}) or verification_form.find('input', {'type': 'submit'})
                if submit_button:
                    name = submit_button.get('name')
                    value = submit_button.get('value', '')
                    if name:
                        form_data[name] = value
                
                # Check if there's a "skip" or "continue" button
                skip_buttons = [
                    button for button in verification_form.find_all('button') 
                    if re.search(r"(skip|continue|next|later|not now)", button.text, re.IGNORECASE)
                ]
                
                if skip_buttons:
                    skip_button = skip_buttons[0]
                    name = skip_button.get('name')
                    value = skip_button.get('value', '')
                    if name:
                        form_data[name] = value
                
                # Add a small delay
                simulate_field_delay()
                
                # Submit the form
                verification_submit = self.session.post(
                    form_action,
                    data=form_data,
                    referer=response.url,
                    allow_redirects=True
                )
                
                # Check if we passed the verification
                if "home.php" in verification_submit.url or "welcome" in verification_submit.url:
                    print("Successfully passed verification!")
                    return True
                elif "checkpoint" in verification_submit.url or "confirm" in verification_submit.url:
                    print("Still in verification process after submission.")
                    return False
                else:
                    # Check for c_user cookie as a sign of success
                    if self.session.has_cookie('c_user'):
                        print("Found c_user cookie after verification. Likely successful.")
                        return True
                    else:
                        print("Verification likely failed.")
                        return False
                
        except Exception as e:
            print(f"Error handling verification: {str(e)}")
            return False
    
    def handle_verification_code(self, code):
        """Handle verification with a code provided directly"""
        print(f"Processing verification code: {code}")
        
        try:
            # First, try to find any checkpoint or confirmation pages in the session
            current_url = self.session.get_current_url()
            
            # If we don't have a current URL, try to visit the homepage to trigger verification
            if not current_url or 'facebook.com' not in current_url:
                print("No verification page detected. Visiting Facebook homepage...")
                response = self.session.get('https://m.facebook.com/', max_redirects=5)
                current_url = response.url
            
            # Check if we're already at a verification page
            if 'checkpoint' in current_url or 'confirm' in current_url or 'verification' in current_url:
                print("Found verification page. Submitting code...")
                response = self.session.get(current_url, max_redirects=5)
                
                # Find the code entry form
                soup = BeautifulSoup(response.text, 'html.parser')
                code_form = self._find_code_entry_form(soup)
                
                if code_form:
                    return self._submit_verification_code(code_form, current_url, code)
                else:
                    print("Couldn't find code entry form on the page")
            
            # If we're not on a verification page, try to find a general checkpoint
            print("Trying general checkpoint page...")
            checkpoint_response = self.session.get('https://m.facebook.com/checkpoint/', max_redirects=5)
            
            # Check if we got a verification form
            soup = BeautifulSoup(checkpoint_response.text, 'html.parser')
            code_form = self._find_code_entry_form(soup)
            
            if code_form:
                return self._submit_verification_code(code_form, checkpoint_response.url, code)
            
            # If we still can't find a form, try a more general approach
            print("Trying a more general approach for code entry...")
            
            # Try several common verification URLs
            verification_urls = [
                'https://m.facebook.com/confirmemail.php',
                'https://m.facebook.com/checkpoint/?next',
                'https://m.facebook.com/login/checkpoint/',
                'https://m.facebook.com/login/reauth.php'
            ]
            
            for url in verification_urls:
                try:
                    print(f"Trying URL: {url}")
                    response = self.session.get(url, max_redirects=5)
                    
                    # Check if we found a form
                    soup = BeautifulSoup(response.text, 'html.parser')
                    code_form = self._find_code_entry_form(soup)
                    
                    if code_form:
                        return self._submit_verification_code(code_form, response.url, code)
                except Exception:
                    continue
            
            # Last resort: try to directly send a POST request to common verification endpoints
            print("Trying direct code submission as last resort...")
            
            # Common verification endpoints
            verification_endpoints = [
                'https://m.facebook.com/checkpoint/submit/',
                'https://m.facebook.com/confirmemail.php',
                'https://m.facebook.com/confirm/submit/'
            ]
            
            for endpoint in verification_endpoints:
                try:
                    # Create a generic form submission
                    form_data = {
                        'code': code,
                        'verification_code': code,
                        'confirmation_code': code,
                        'submit': 'Confirm',
                        'fb_dtsg': self.session.fb_dtsg if self.session.fb_dtsg else '',
                        'lsd': self.session.lsd if self.session.lsd else ''
                    }
                    
                    print(f"Trying direct submission to: {endpoint}")
                    
                    # Submit the code
                    response = self.session.post(
                        endpoint,
                        data=form_data,
                        referer='https://m.facebook.com/',
                        allow_redirects=True
                    )
                    
                    # Check if we succeeded
                    if self.session.has_cookie('c_user'):
                        print("✅ Verification successful! Found c_user cookie.")
                        return True
                    
                    if "home.php" in response.url or "welcome" in response.url:
                        print("✅ Verification successful based on redirect!")
                        return True
                except Exception:
                    continue
            
            print("❌ Could not complete verification with the provided code.")
            return False
            
        except Exception as e:
            print(f"Error processing verification code: {str(e)}")
            return False
    
    def handle_email_verification(self, response):
        """Handle email verification process"""
        print("Handling email verification...")
        
        try:
            # Parse the current page to find if it's a code verification page
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text().lower()
            
            # Check if this is a code verification page
            is_code_page = any(phrase in page_text for phrase in [
                "confirmation code", "verification code", "code sent", "enter the code",
                "check your email", "fb-", "code from your email"
            ])
            
            print(f"Is this a code verification page? {is_code_page}")
            
            if is_code_page:
                # We need a code, but we'll return account info with a callback
                return "verification_required"
            else:
                # Not a code page, so check for other verification options
                verification_buttons = []
                
                # Look for email verification buttons/links
                for link in soup.find_all(['a', 'button']):
                    link_text = link.get_text().lower()
                    if any(term in link_text for term in ["email", "mail", "inbox", "confirm"]):
                        verification_buttons.append(link)
                        
                if verification_buttons:
                    # Click the first email verification button
                    button = verification_buttons[0]
                    button_url = button.get('href')
                    
                    if button_url:
                        if not button_url.startswith('http'):
                            if button_url.startswith('/'):
                                button_url = f"https://m.facebook.com{button_url}"
                            else:
                                button_url = f"https://m.facebook.com/{button_url}"
                        
                        print(f"Clicking email verification button: {button_url}")
                        
                        # Add a small delay like a human would
                        simulate_field_delay()
                        
                        button_response = self.session.get(
                            button_url,
                            referer=response.url,
                            allow_redirects=True
                        )
                        
                        # Recursively handle this response
                        return self.handle_email_verification(button_response)
                
                # If no buttons found, we need a code from the user
                return "verification_required"
                
        except Exception as e:
            print(f"Error during email verification: {str(e)}")
            return "verification_required"
    
    def _find_code_entry_form(self, soup):
        """Find a form for entering a verification code"""
        # First try to find a form with code input fields
        for form in soup.find_all('form'):
            has_code_field = False
            
            # Look for input fields that might be for codes
            for input_field in form.find_all('input'):
                input_type = input_field.get('type', '')
                input_name = input_field.get('name', '').lower()
                input_id = input_field.get('id', '').lower()
                input_placeholder = input_field.get('placeholder', '').lower()
                
                # Check if this looks like a code input field
                if (input_type == 'text' or input_type == 'number') and (
                    'code' in input_name or 'code' in input_id or 
                    'code' in input_placeholder or 'confirm' in input_name or
                    'confirm' in input_id or 'confirm' in input_placeholder):
                    has_code_field = True
                    break
            
            if has_code_field:
                return form
        
        # If no specific code form found, look for any form
        return soup.find('form')
    
    def _submit_verification_code(self, form, page_url, verification_code):
        """Submit a verification code form"""
        print("Submitting verification code...")
        
        # Extract form data
        form_data = {}
        for input_field in form.find_all('input'):
            name = input_field.get('name')
            if not name:
                continue
                
            value = input_field.get('value', '')
            
            # Check if this is a code input field
            input_type = input_field.get('type', '')
            is_code_field = input_type in ['text', 'number'] or 'code' in name.lower() or 'confirm' in name.lower()
            
            if is_code_field:
                # Check if we need to handle FB- prefix
                if "fb-" in page_url.lower() or "fb-" in form.get_text().lower():
                    # Facebook may be expecting the code with or without the FB- prefix
                    if verification_code.startswith("FB-"):
                        form_data[name] = verification_code
                    else:
                        form_data[name] = verification_code
                else:
                    # Regular code field
                    form_data[name] = verification_code
            else:
                # Non-code field, use the default value
                form_data[name] = value
        
        # Check if no code field was found
        if not any('code' in field.lower() or 'confirm' in field.lower() for field in form_data.keys()):
            # Find the first text/number input field as a fallback
            for input_field in form.find_all('input'):
                name = input_field.get('name')
                if input_field.get('type') in ['text', 'number'] and name and name not in form_data:
                    form_data[name] = verification_code
                    break
        
        # Get form action
        form_action = form.get('action', '')
        if not form_action.startswith('http'):
            # Handle relative URLs
            if form_action.startswith('/'):
                form_action = f"https://m.facebook.com{form_action}"
            else:
                form_action = f"https://m.facebook.com/{form_action}"
        
        # If no action, use current URL
        if not form_action:
            form_action = page_url
        
        # Find submit button
        submit_button = form.find('button', {'type': 'submit'}) or form.find('input', {'type': 'submit'})
        if submit_button:
            name = submit_button.get('name')
            value = submit_button.get('value', '')
            if name and name not in form_data:
                form_data[name] = value
        
        # Simulate typing delay
        simulate_typing_delay(verification_code)
        simulate_submit_delay()
        
        # Submit the form
        print(f"Submitting verification code to {form_action}")
        
        verification_submit = self.session.post(
            form_action,
            data=form_data,
            referer=page_url,
            allow_redirects=True
        )
        
        # Check if we passed the verification
        if "home.php" in verification_submit.url or "welcome" in verification_submit.url:
            print("✅ Successfully verified with code!")
            return True
        else:
            # Check for c_user cookie as a sign of success
            if self.session.has_cookie('c_user'):
                print("✅ Found c_user cookie after code verification. Success!")
                return True
            
            # Check if we're being asked for another verification
            if "checkpoint" in verification_submit.url or "confirm" in verification_submit.url:
                # We might need another verification step
                verification_soup = BeautifulSoup(verification_submit.text, 'html.parser')
                if "another code" in verification_soup.get_text().lower() or "new code" in verification_soup.get_text().lower():
                    print("Facebook is asking for another code.")
                    return False
            
            print("❌ Code verification did not fully succeed.")
            return False