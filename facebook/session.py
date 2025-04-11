"""
Session and cookie management for Facebook
"""

import requests
import logging
import time
import random
import sys
import re
import json
import gzip
import uuid
from urllib.parse import urlparse, urljoin, unquote, parse_qs, urlencode
from config import get_random_user_agent, REQUEST_TIMEOUT, MAX_RETRIES
from utils.helpers import simulate_page_load_delay

logger = logging.getLogger("FBAccountCreator")

class FacebookSession:
    def __init__(self, proxy=None):
        """Initialize a Facebook session with proxy support"""
        self.session = requests.Session()
        # Setup custom redirect handling
        self.session.hooks = {
            'response': [self._handle_fb_redirects]
        }
        
        self.user_agent = get_random_user_agent()
        self.proxy = proxy
        self.device_id = str(uuid.uuid4()).upper()
        self.base_headers = self._create_base_headers()
        
        # Important Facebook cookies
        self.fb_dtsg = None
        self.lsd = None
        self.datr_cookie = None
        
        # Set reasonable redirect limits
        self.session.max_redirects = 5  # Lower this to avoid infinite loops
        
        # Configure the session with proxy if provided
        if proxy:
            self._configure_proxy(proxy)
            
        # Setup initial browser-like state
        self._setup_browser_state()
    
    def _setup_browser_state(self):
        """Set up initial browser-like state with basic cookies and headers"""
        # Generate common browser fingerprinting values
        browser_language = "en-US,en;q=0.9"
        screen_width = random.choice([1280, 1366, 1440, 1920])
        screen_height = random.choice([720, 768, 900, 1080])
        color_depth = 24
        timezone_offset = random.choice([-480, -420, -360, -300, -240, -180, -120, -60, 0, 60, 120, 180])
        
        # Generate a Facebook-specific browser ID
        browser_id = f"{random.randint(100000, 999999)}.{random.randint(100000, 999999)}"
        
        # Set common cookies that browsers typically have
        self.session.cookies.set("locale", "en_US", domain=".facebook.com", path="/")
        self.session.cookies.set("wd", f"{screen_width}x{screen_height}", domain=".facebook.com", path="/")
        self.session.cookies.set("dpr", "1.5", domain=".facebook.com", path="/")
        self.session.cookies.set("fr", f"{browser_id}.{int(time.time())}.0.{random.random()}", domain=".facebook.com", path="/")
        
        # Generate a unique device ID that Facebook uses
        self.session.cookies.set("m_pixel_ratio", "1.5", domain=".facebook.com", path="/")
        
        # Additional headers that make the request more browser-like
        self.base_headers.update({
            "Accept-Language": browser_language,
            "Sec-Ch-Prefers-Color-Scheme": "light",
            "Sec-Ch-Ua-Platform-Version": "15.0.0",
            "Viewport-Width": str(screen_width),
            "Sec-Ch-Viewport-Height": str(screen_height),
            "Sec-Ch-Viewport-Width": str(screen_width),
            "Device-Memory": "8",
        })
    
    def _handle_fb_redirects(self, response, **kwargs):
        """Handle Facebook app redirects"""
        # Check if the redirect is to fbredirect:// protocol
        if response.is_redirect and 'location' in response.headers:
            redirect_url = response.headers['location']
            
            # Check for Facebook app redirect
            if redirect_url.startswith('fbredirect://'):
                logger.info(f"Detected Facebook app redirect: {redirect_url}")
                
                # Extract the actual URL
                try:
                    # Parse app redirect URL
                    parsed = urlparse(redirect_url)
                    params = parse_qs(parsed.query)
                    
                    # Extract the real URL from the uri parameter
                    if 'uri' in params:
                        real_url = unquote(params['uri'][0])
                        logger.info(f"Extracted web URL from app redirect: {real_url}")
                        
                        # Use normal URL but don't follow redirects on this one
                        # to avoid redirect loop
                        new_response = self.session.get(
                            real_url,
                            headers=self.base_headers,
                            allow_redirects=False,
                            timeout=REQUEST_TIMEOUT
                        )
                        
                        # Replace the original response with our new one
                        return new_response
                except Exception as e:
                    logger.error(f"Error handling app redirect: {str(e)}")
            
            # Check for Facebook mobile site redirects to desktop or other formats
            elif redirect_url.startswith('https://facebook.com/') or redirect_url.startswith('https://www.facebook.com/'):
                logger.info(f"Detected desktop redirect from mobile site: {redirect_url}")
                
                # Convert to mobile URL if needed
                if 'm.facebook.com' not in redirect_url and '/mobile/' not in redirect_url:
                    mobile_url = redirect_url.replace('www.facebook.com', 'm.facebook.com')
                    mobile_url = mobile_url.replace('facebook.com', 'm.facebook.com')
                    
                    logger.info(f"Converting to mobile URL: {mobile_url}")
                    
                    # Use mobile URL but don't follow redirects on this one
                    # to avoid redirect loop
                    try:
                        new_response = self.session.get(
                            mobile_url,
                            headers=self.base_headers,
                            allow_redirects=False,
                            timeout=REQUEST_TIMEOUT
                        )
                        
                        # Replace the original response with our new one
                        return new_response
                    except Exception as e:
                        logger.error(f"Error during mobile URL conversion: {str(e)}")
            
            # Handle checkpoint redirects
            elif 'checkpoint' in redirect_url:
                logger.info(f"Detected checkpoint redirect: {redirect_url}")
                
                # Just follow this one without changing anything
                try:
                    new_response = self.session.get(
                        redirect_url,
                        headers=self.base_headers,
                        allow_redirects=False,
                        timeout=REQUEST_TIMEOUT
                    )
                    
                    return new_response
                except Exception as e:
                    logger.error(f"Error following checkpoint redirect: {str(e)}")
        
        # Try to extract DTSG and LSD tokens from any response
        self._extract_facebook_tokens(response)
        
        # Monitor and store important cookies
        self._store_important_cookies()
        
        return response
    
    def _extract_facebook_tokens(self, response):
        """Extract Facebook DTSG and LSD tokens from response"""
        try:
            # Only parse HTML responses
            if 'text/html' in response.headers.get('Content-Type', ''):
                # Try to find fb_dtsg 
                dtsg_match = re.search(r'"fb_dtsg":"([^"]+)"', response.text)
                if dtsg_match:
                    self.fb_dtsg = dtsg_match.group(1)
                    logger.info(f"Found fb_dtsg token: {self.fb_dtsg[:10]}...")
                
                # Try to find LSD
                lsd_match = re.search(r'name="lsd" value="([^"]+)"', response.text)
                if lsd_match:
                    self.lsd = lsd_match.group(1)
                    logger.info(f"Found LSD token: {self.lsd[:10]}...")
        except Exception as e:
            logger.error(f"Error extracting Facebook tokens: {str(e)}")
    
    def _store_important_cookies(self):
        """Store important cookies for later use"""
        cookies = self.session.cookies.get_dict()
        
        # Store datr cookie which is important for Facebook sessions
        if 'datr' in cookies and not self.datr_cookie:
            self.datr_cookie = cookies['datr']
            logger.info(f"Stored datr cookie: {self.datr_cookie}")
    
    def _configure_proxy(self, proxy):
        """Configure the session to use a proxy"""
        if not proxy:
            logger.warning("No proxy provided to configure")
            return

        try:
            # Check if proxy is already formatted for requests
            if isinstance(proxy, dict) and ('http' in proxy or 'https' in proxy):
                # Already formatted
                self.session.proxies.update(proxy)
                logger.info(f"Session configured with pre-formatted proxy")
                return
                
            # Check if proxy has direct url property
            if isinstance(proxy, dict) and 'url' in proxy:
                proxy_url = proxy['url']
                self.session.proxies.update({
                    'http': proxy_url,
                    'https': proxy_url
                })
                logger.info(f"Session configured with proxy URL: {proxy_url}")
                return
                
            # Check if we have username/password + ip/port
            if isinstance(proxy, dict) and 'username' in proxy and 'password' in proxy and 'ip' in proxy and 'port' in proxy:
                proxy_dict = {
                    'http': f"http://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}",
                    'https': f"http://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
                }
                self.session.proxies.update(proxy_dict)
                logger.info(f"Session configured with authenticated proxy: {proxy['ip']}:{proxy['port']}")
                return
                
            # Check if we have just ip/port
            if isinstance(proxy, dict) and 'ip' in proxy and 'port' in proxy:
                proxy_dict = {
                    'http': f"http://{proxy['ip']}:{proxy['port']}",
                    'https': f"http://{proxy['ip']}:{proxy['port']}"
                }
                self.session.proxies.update(proxy_dict)
                logger.info(f"Session configured with simple proxy: {proxy['ip']}:{proxy['port']}")
                return
                
            logger.warning(f"Unrecognized proxy format: {proxy}")
        except Exception as e:
            logger.error(f"Error configuring proxy: {str(e)}")
    
    def _create_base_headers(self):
        """Create base headers for requests"""
        return {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none', 
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?1',  # Indicate mobile browser
            'Sec-Ch-Ua-Platform': '"Android"',  # Indicate Android platform
            'Referer': 'https://www.google.com/',
            'Dnt': '1'
        }
    
    def get(self, url, headers=None, allow_redirects=True, referer=None, timeout=None, max_redirects=5):
        """Make a GET request with retries and error handling"""
        if timeout is None:
            timeout = REQUEST_TIMEOUT
            
        if headers is None:
            headers = self.base_headers.copy()
            
        if referer:
            headers['Referer'] = referer
        
        # Set the correct host header based on the URL
        parsed_url = urlparse(url)
        headers['Host'] = parsed_url.netloc
        
        # Add Anti-detection parameters
        headers['X-FB-Friendly-Name'] = 'MobileFriendlyLoginPage'
        
        # Add Facebook-specific parameters
        self._add_facebook_specific_headers(headers, parsed_url)
        
        # Save current redirect setting
        original_max_redirects = self.session.max_redirects
        
        # Apply max_redirects for this request
        self.session.max_redirects = max_redirects
        
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    url,
                    headers=headers,
                    allow_redirects=allow_redirects,
                    timeout=timeout
                )
                
                # Log response info
                logger.info(f"GET {url} - Status: {response.status_code}")
                
                # Extract important Facebook tokens
                self._extract_facebook_tokens(response)
                
                # Store important cookies
                self._store_important_cookies()
                
                # Add a delay to simulate human behavior
                simulate_page_load_delay()
                
                # Restore original redirect setting
                self.session.max_redirects = original_max_redirects
                
                return response
                
            except requests.exceptions.TooManyRedirects as e:
                logger.warning(f"Too many redirects: {str(e)}")
                
                # Immediately fail this proxy and suggest to try another one
                logger.error(f"This proxy may be blocked or detected by Facebook")
                
                # Restore original redirect setting
                self.session.max_redirects = original_max_redirects
                
                raise
                
            except requests.exceptions.InvalidSchema as e:
                # This happens with fbredirect:// protocol
                logger.warning(f"Invalid schema error: {str(e)}")
                
                # Try to extract the actual URL from the error message
                match = re.search(r"'(fbredirect://[^']+)'", str(e))
                if match:
                    redirect_url = match.group(1)
                    logger.info(f"Detected app redirect URL: {redirect_url}")
                    
                    try:
                        # Parse app redirect URL
                        parsed = urlparse(redirect_url)
                        params = parse_qs(parsed.query)
                        
                        # Extract the real URL from the uri parameter
                        if 'uri' in params:
                            real_url = unquote(params['uri'][0])
                            logger.info(f"Extracted web URL from app redirect: {real_url}")
                            
                            # Try a direct approach - use the /reg/submit/ endpoint
                            bypass_url = "https://m.facebook.com/reg/submit/"
                            logger.info(f"Trying direct URL: {bypass_url}")
                            
                            # Try with the new URL
                            response = self.session.get(
                                bypass_url,
                                headers=headers,
                                allow_redirects=allow_redirects,
                                timeout=timeout
                            )
                            
                            # Restore original redirect setting
                            self.session.max_redirects = original_max_redirects
                            
                            return response
                    except Exception as nested_e:
                        logger.error(f"Error handling app redirect URL: {str(nested_e)}")
                
                # Try a direct approach for account creation if regular error handling failed
                try:
                    # Directly access the full version signup page as fallback
                    fallback_url = "https://m.facebook.com/r.php"
                    logger.info(f"Trying fallback URL: {fallback_url}")
                    
                    new_headers = headers.copy()
                    new_headers['Host'] = 'm.facebook.com'
                    
                    response = self.session.get(
                        fallback_url,
                        headers=new_headers,
                        allow_redirects=allow_redirects,
                        timeout=timeout
                    )
                    
                    # Restore original redirect setting
                    self.session.max_redirects = original_max_redirects
                    
                    return response
                except Exception as fallback_e:
                    logger.error(f"Fallback approach failed: {str(fallback_e)}")
                    
                    # Restore original redirect setting before re-raising
                    self.session.max_redirects = original_max_redirects
                    
                    raise e  # Re-raise the original error
                
            except (requests.RequestException, requests.ConnectionError, requests.Timeout) as e:
                logger.warning(f"Attempt {attempt+1}/{MAX_RETRIES} failed: {str(e)}")
                
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"All {MAX_RETRIES} attempts failed for URL: {url}")
                    
                    # Restore original redirect setting
                    self.session.max_redirects = original_max_redirects
                    
                    raise
                
                # Exponential backoff with jitter
                backoff_time = (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"Retrying in {backoff_time:.2f} seconds...")
                time.sleep(backoff_time)
        
        # Should not reach here, but just in case
        self.session.max_redirects = original_max_redirects
        return None
    
    def _add_facebook_specific_headers(self, headers, parsed_url):
        """Add Facebook-specific headers and parameters"""
        # Only add for Facebook domains
        if 'facebook.com' not in parsed_url.netloc:
            return
            
        # Add tokens if available
        if self.fb_dtsg:
            headers['X-FB-DTSG'] = self.fb_dtsg
        
        # Add device info
        headers['X-ASBD-ID'] = '129477'
        headers['X-FB-Connection-Type'] = 'MOBILE_UNKNOWN'
        headers['X-FB-Connection-Quality'] = 'EXCELLENT'
        headers['X-FB-Connection-Bandwidth'] = str(random.randint(5000000, 10000000))
        headers['X-FB-Device-Group'] = str(random.randint(1000, 9999))
        
        # Make it look like the Facebook app for login
        if 'login' in parsed_url.path:
            headers['X-FB-Friendly-Name'] = 'LoginStateController'
        elif 'reg' in parsed_url.path:
            headers['X-FB-Friendly-Name'] = 'RegMobilePage'
    
    def post(self, url, data=None, headers=None, allow_redirects=True, referer=None, timeout=None, max_redirects=5):
        """Make a POST request with retries and error handling"""
        if timeout is None:
            timeout = REQUEST_TIMEOUT
            
        if headers is None:
            headers = self.base_headers.copy()
            
        if referer:
            headers['Referer'] = referer
            
        # Add content type for POST requests
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        # Set the correct host header based on the URL
        parsed_url = urlparse(url)
        headers['Host'] = parsed_url.netloc
        
        # Set origin header
        origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
        headers['Origin'] = origin
        
        # Add anti-detection headers for Facebook
        headers['X-FB-Friendly-Name'] = 'MobileRegistrationCore'
        
        # Add Facebook tokens if available
        if self.fb_dtsg and 'fb_dtsg' not in data:
            if isinstance(data, dict):
                data['fb_dtsg'] = self.fb_dtsg
        
        if self.lsd and 'lsd' not in data:
            if isinstance(data, dict):
                data['lsd'] = self.lsd
                
        # Add device info
        self._add_facebook_specific_headers(headers, parsed_url)
        
        # Save current redirect setting
        original_max_redirects = self.session.max_redirects
        
        # Apply max_redirects for this request
        self.session.max_redirects = max_redirects
        
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.post(
                    url,
                    data=data,
                    headers=headers,
                    allow_redirects=allow_redirects,
                    timeout=timeout
                )
                
                # Log response info
                logger.info(f"POST {url} - Status: {response.status_code}")
                
                # Extract important Facebook tokens
                self._extract_facebook_tokens(response)
                
                # Store important cookies
                self._store_important_cookies()
                
                # Add a delay to simulate human behavior
                simulate_page_load_delay()
                
                # Restore original redirect setting
                self.session.max_redirects = original_max_redirects
                
                return response
                
            except requests.exceptions.TooManyRedirects as e:
                logger.warning(f"Too many redirects: {str(e)}")
                
                # Immediately fail this proxy and suggest to try another one
                logger.error(f"This proxy may be blocked or detected by Facebook")
                
                # Restore original redirect setting
                self.session.max_redirects = original_max_redirects
                
                raise
            
            except requests.exceptions.InvalidSchema as e:
                # This happens with fbredirect:// protocol
                logger.warning(f"Invalid schema error during POST: {str(e)}")
                
                # Try to directly post to the regular submission URL
                try:
                    submit_url = "https://www.facebook.com/reg/submit/"
                    logger.info(f"Trying direct submission to: {submit_url}")
                    
                    new_headers = headers.copy()
                    new_headers['Host'] = 'www.facebook.com'
                    new_headers['Origin'] = 'https://www.facebook.com'
                    
                    response = self.session.post(
                        submit_url,
                        data=data,
                        headers=new_headers,
                        allow_redirects=allow_redirects,
                        timeout=timeout
                    )
                    
                    # Restore original redirect setting
                    self.session.max_redirects = original_max_redirects
                    
                    return response
                except Exception as submit_e:
                    logger.error(f"Direct submission failed: {str(submit_e)}")
                    
                    # Restore original redirect setting before re-raising
                    self.session.max_redirects = original_max_redirects
                    
                    raise e  # Re-raise the original error
                
            except (requests.RequestException, requests.ConnectionError, requests.Timeout) as e:
                logger.warning(f"Attempt {attempt+1}/{MAX_RETRIES} failed: {str(e)}")
                
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"All {MAX_RETRIES} attempts failed for URL: {url}")
                    
                    # Restore original redirect setting
                    self.session.max_redirects = original_max_redirects
                    
                    raise
                
                # Exponential backoff with jitter
                backoff_time = (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"Retrying in {backoff_time:.2f} seconds...")
                time.sleep(backoff_time)
        
        # Should not reach here, but just in case
        self.session.max_redirects = original_max_redirects
        return None
    
    def resolve_relative_url(self, base_url, relative_url):
        """Resolve a relative URL against a base URL"""
        if relative_url.startswith('http'):
            return relative_url
        else:
            return urljoin(base_url, relative_url)
    
    def get_cookies_dict(self):
        """Get all cookies as a dictionary"""
        return self.session.cookies.get_dict()
    
    def has_cookie(self, cookie_name):
        """Check if a specific cookie exists"""
        return cookie_name in self.session.cookies.get_dict()
    
    def get_cookie(self, cookie_name):
        """Get a specific cookie value"""
        return self.session.cookies.get_dict().get(cookie_name)
    
    def set_cookie(self, name, value, domain='.facebook.com', path='/'):
        """Set a cookie in the session"""
        self.session.cookies.set(name, value, domain=domain, path=path)
        
    def clear_cookies(self):
        """Clear all cookies in the session"""
        self.session.cookies.clear()
        
    def update_user_agent(self, user_agent=None):
        """Update the user agent"""
        if user_agent is None:
            user_agent = get_random_user_agent()
            
        self.user_agent = user_agent
        self.base_headers['User-Agent'] = user_agent
        logger.info(f"Updated user agent: {user_agent}")
    
    def wait_after_creation(self, seconds=5):
        """Wait after account creation to let Facebook process changes"""
        logger.info(f"Waiting {seconds} seconds after account creation...")
        time.sleep(seconds)