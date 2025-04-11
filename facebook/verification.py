"""
Facebook verification process handlers
"""

import re
import logging
import time
import random
from bs4 import BeautifulSoup
from utils.user_input import get_verification_info
from utils.helpers import simulate_typing_delay, simulate_submit_delay, simulate_field_delay

logger = logging.getLogger("FBAccountCreator")

class VerificationHandler:
    def __init__(self, session):
        """Initialize the verification handler"""
        self.session = session
    
    def handle_verification(self, response):
        """Handle Facebook verification steps"""
        logger.info("Handling verification process...")
        
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
            
            logger.info(f"Detected verification type: {verification_type}")
            
            if verification_type == "email":
                return self.handle_email_verification(response)
            elif verification_type in ["phone", "captcha"]:
                logger.warning(f"Cannot automatically handle {verification_type} verification")
                
                # For phone verification, notify the user
                if verification_type == "phone":
                    print("\n=== Phone Verification Required ===")
                    print("Facebook is requesting phone verification, which this script cannot handle automatically.")
                    print("You will need to complete this process manually.")
                    
                # For captcha verification, notify the user
                elif verification_type == "captcha":
                    print("\n=== Captcha Verification Required ===")
                    print("Facebook is requesting captcha verification, which this script cannot handle automatically.")
                    print("You will need to complete this process manually.")
                
                return False
            else:
                logger.warning("Unknown verification type. Trying generic approach...")
                
                # Look for a form we might be able to submit
                verification_form = soup.find('form')
                
                if not verification_form:
                    logger.error("No verification form found")
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
                    logger.info("Successfully passed verification!")
                    return True
                elif "checkpoint" in verification_submit.url or "confirm" in verification_submit.url:
                    logger.warning("Still in verification process after submission.")
                    return False
                else:
                    # Check for c_user cookie as a sign of success
                    if self.session.has_cookie('c_user'):
                        logger.info("Found c_user cookie after verification. Likely successful.")
                        return True
                    else:
                        logger.error("Verification likely failed.")
                        return False
                
        except Exception as e:
            logger.error(f"Error handling verification: {str(e)}")
            return False
    
    def handle_email_verification(self, response):
        """Handle email verification process"""
        logger.info("Handling email verification...")
        
        try:
            # Parse the current page to find if it's a code verification page
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text().lower()
            
            # Check if this is a code verification page
            is_code_page = any(phrase in page_text for phrase in [
                "confirmation code", "verification code", "code sent", "enter the code",
                "check your email", "fb-", "code from your email"
            ])
            
            logger.info(f"Is this a code verification page? {is_code_page}")
            
            if is_code_page:
                # Notify user to check email
                print("\n=== Email Verification Required ===")
                print("Facebook has sent a verification code to your email.")
                print("Please check your email and provide the verification code or link.")
                
                # Get verification code or link from user
                verification_info = get_verification_info()
                
                if not verification_info:
                    logger.error("No verification info provided by user")
                    return False
                
                # Check if we got a verification link or code
                if verification_info.startswith("http"):
                    # We got a verification link
                    logger.info("Using verification link...")
                    
                    # Add a small delay like a human would
                    simulate_field_delay()
                    
                    verification_response = self.session.get(
                        verification_info,
                        referer='https://m.facebook.com/',
                        allow_redirects=True
                    )
                    
                    logger.info(f"Verification link response: {verification_response.status_code}")
                    logger.info(f"Final URL after verification: {verification_response.url}")
                    
                    # Check if verification was successful
                    if "home.php" in verification_response.url or "welcome" in verification_response.url:
                        logger.info("Email verification successful!")
                        return True
                    else:
                        # Check for c_user cookie as a sign of success
                        if self.session.has_cookie('c_user'):
                            logger.info("Found c_user cookie after verification. Likely successful.")
                            return True
                        else:
                            logger.warning("Email verification link may not have worked.")
                            
                            # Try to find a form for code entry on the page
                            verification_soup = BeautifulSoup(verification_response.text, 'html.parser')
                            code_form = self._find_code_entry_form(verification_soup)
                            
                            if code_form:
                                logger.info("Found code entry form after following verification link")
                                
                                # Ask for a new code if needed
                                print("\nThe verification link didn't work completely. Facebook might be asking for the code directly.")
                                new_code = input("If you have a verification code, enter it now (or press Enter to skip): ").strip()
                                if new_code:
                                    return self._submit_verification_code(code_form, verification_response.url, new_code)
                            
                            # Try another approach
                            return False
                else:
                    # We got a verification code
                    logger.info(f"Using verification code: {verification_info}")
                    
                    # Find code input form
                    code_form = self._find_code_entry_form(soup)
                    
                    if code_form:
                        logger.info("Found code entry form")
                        return self._submit_verification_code(code_form, response.url, verification_info)
                    else:
                        logger.error("Could not find code input form")
                        print("\nCouldn't find a form to submit the verification code.")
                        print("The registration might still have succeeded. Try to login with your credentials.")
                        return False
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
                        
                        logger.info(f"Clicking email verification button: {button_url}")
                        
                        # Add a small delay like a human would
                        simulate_field_delay()
                        
                        button_response = self.session.get(
                            button_url,
                            referer=response.url,
                            allow_redirects=True
                        )
                        
                        logger.info(f"Button click response: {button_response.status_code}")
                        logger.info(f"Button click final URL: {button_response.url}")
                        
                        # Recursively handle this response
                        return self.handle_email_verification(button_response)
                    
                # If no buttons found, ask user for verification
                print("\n=== Email Verification ===")
                print("Facebook may have sent a verification email. Please check your email.")
                print("If you received an email, provide the verification code or link.")
                verification_info = get_verification_info()
                
                if verification_info and verification_info.startswith("http"):
                    # We got a verification link
                    logger.info("Using verification link...")
                    
                    verification_response = self.session.get(
                        verification_info,
                        referer='https://m.facebook.com/',
                        allow_redirects=True
                    )
                    
                    logger.info(f"Verification link response: {verification_response.status_code}")
                    logger.info(f"Final URL after verification: {verification_response.url}")
                    
                    # Check if verification was successful
                    if "home.php" in verification_response.url or "welcome" in verification_response.url:
                        logger.info("Email verification successful!")
                        return True
                    else:
                        # Check for c_user cookie as a sign of success
                        if self.session.has_cookie('c_user'):
                            logger.info("Found c_user cookie after verification. Likely successful.")
                            return True
                        else:
                            logger.warning("Email verification link may not have worked.")
                            return False
                else:
                    # No verification info or not a link
                    logger.info("No verification info found or not a link")
                    return False
                
        except Exception as e:
            logger.error(f"Error during email verification: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
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
    
    def _submit_verification_code(self, form, page_url, verification_code=None):
        """Submit a verification code form"""
        logger.info("Submitting verification code...")
        
        # If we don't have a code yet, ask the user
        if not verification_code:
            print("\n=== Verification Code Required ===")
            print("Please enter the verification code from your email:")
            verification_code = input("Code: ").strip()
            
            if not verification_code:
                logger.error("No verification code provided")
                return False
            
            # If we got a link instead of a code, use the link directly
            if verification_code.startswith("http"):
                logger.info("Received a verification link instead of a code, using the link...")
                
                verification_response = self.session.get(
                    verification_code,
                    referer=page_url,
                    allow_redirects=True
                )
                
                logger.info(f"Verification link response: {verification_response.status_code}")
                logger.info(f"Final URL after verification: {verification_response.url}")
                
                # Check if verification was successful
                if "home.php" in verification_response.url or "welcome" in verification_response.url:
                    logger.info("Email verification successful!")
                    return True
                elif self.session.has_cookie('c_user'):
                    logger.info("Found c_user cookie after verification. Likely successful.")
                    return True
                else:
                    logger.warning("Verification link may not have worked completely")
                    return False
        
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
        logger.info(f"Submitting verification code to {form_action}")
        
        verification_submit = self.session.post(
            form_action,
            data=form_data,
            referer=page_url,
            allow_redirects=True
        )
        
        # Check if we passed the verification
        logger.info(f"Code submission response: {verification_submit.status_code}")
        logger.info(f"Code submission final URL: {verification_submit.url}")
        
        if "home.php" in verification_submit.url or "welcome" in verification_submit.url:
            logger.info("Successfully verified with code!")
            return True
        else:
            # Check for c_user cookie as a sign of success
            if self.session.has_cookie('c_user'):
                logger.info("Found c_user cookie after code verification. Likely successful.")
                return True
            
            # Check if we're being asked for another verification
            if "checkpoint" in verification_submit.url or "confirm" in verification_submit.url:
                # We might need another verification step
                verification_soup = BeautifulSoup(verification_submit.text, 'html.parser')
                if "another code" in verification_soup.get_text().lower() or "new code" in verification_soup.get_text().lower():
                    logger.info("Facebook is asking for another code.")
                    print("\n=== Another Verification Code Required ===")
                    print("Facebook is asking for another verification code.")
                    print("Please check your email for a new code and enter it:")
                    
                    # Get new code from user
                    new_verification_code = input("Enter new verification code: ").strip()
                    
                    if new_verification_code:
                        # Find the new code form
                        new_code_form = self._find_code_entry_form(verification_soup)
                        
                        if new_code_form:
                            return self._submit_verification_code(new_code_form, verification_submit.url, new_verification_code)
                        else:
                            logger.error("Could not find new code entry form")
                            return False
                    else:
                        logger.error("No new verification code provided")
                        return False
            
            return False