"""
Enhanced session and cookie management for Facebook
"""

import requests
import logging
import time
import random
import re
import uuid
import json
from urllib.parse import urlparse, urljoin, unquote, parse_qs
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
        self.current_url = None
        
        # Important Facebook cookies
        self.fb_dtsg = None
        self.lsd = None
        self.datr_cookie = None
        
        # Set higher redirect limits
        self.session.max_redirects = 10
        
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
        
        # Add additional browser characteristics
        self.session.cookies.set("presence", f"{random.randint(1000000, 9999999)}", domain=".facebook.com", path="/")
        self.session.cookies.set("sb", self._generate_random_cookie_value(24), domain=".facebook.com", path="/")
        
        # Create datr cookie which Facebook uses for browser identification
        self.datr_cookie = self._generate_random_cookie_value(24)
        self.session.cookies.set("datr", self.datr_cookie, domain=".facebook.com", path="/")
        
        # Set fr cookie with browser identification
        fr_cookie = f"{browser_id}.{int(time.time())}.0.{random.random()}"
        self.session.cookies.set("fr", fr_cookie, domain=".facebook.com", path="/")
    
    def _generate_random_cookie_value(self, length=24):
        """Generate a random cookie value similar to what Facebook uses"""
        charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        return ''.join(random.choice(charset) for _ in range(length))
    
    def _handle_fb_redirects(self, response, **kwargs):
        """Handle Facebook app redirects with improved handling"""
        # Update current URL
        self.current_url = response.url
        
        # Check if the redirect is to fbredirect:// protocol
        if response.is_redirect and 'location' in response.headers:
            redirect_url = response.headers['location']
            
            # Check for Facebook app redirect
            if redirect_url.startswith('fbredirect://'):
                # Try to extract the actual URL
                try:
                    # Parse app redirect URL
                    parsed = urlparse(redirect_url)
                    params = parse_qs(parsed.query)
                    
                    # Extract the real URL from the uri parameter
                    if 'uri' in params:
                        real_url = unquote(params['uri'][0])
                        
                        # Use normal URL but don't follow redirects on this one
                        # to avoid redirect loop
                        new_response = self.session.get(
                            real_url,
                            headers=self.base_headers,
                            allow_redirects=False,
                            timeout=REQUEST_TIMEOUT
                        )
                        
                        # Update current URL
                        self.current_url = new_response.url
                        
                        # Replace the original response with our new one
                        return new_response
                except Exception as e:
                    logger.debug(f"Error handling fbredirect: {str(e)}")
            
            # Check for Facebook mobile site redirects to desktop or other formats
            elif redirect_url.startswith('https://facebook.com/') or redirect_url.startswith('https://www.facebook.com/'):
                
                # Convert to mobile URL if needed
                if 'm.facebook.com' not in redirect_url and '/mobile/' not in redirect_url:
                    mobile_url = redirect_url.replace('www.facebook.com', 'm.facebook.com')
                    mobile_url = mobile_url.replace('facebook.com', 'm.facebook.com')
                    
                    # Use mobile URL but don't follow redirects on this one
                    # to avoid redirect loop
                    try:
                        new_response = self.session.get(
                            mobile_url,
                            headers=self.base_headers,
                            allow_redirects=False,
                            timeout=REQUEST_TIMEOUT
                        )
                        
                        # Update current URL
                        self.current_url = new_response.url
                        
                        # Replace the original response with our new one
                        return new_response
                    except Exception as e:
                        logger.debug(f"Error handling mobile redirect: {str(e)}")
            
            # Handle checkpoint redirects
            elif 'checkpoint' in redirect_url:
                
                # Just follow this one without changing anything
                try:
                    new_response = self.session.get(
                        redirect_url,
                        headers=self.base_headers,
                        allow_redirects=False,
                        timeout=REQUEST_TIMEOUT
                    )
                    
                    # Update current URL
                    self.current_url = new_response.url
                    
                    return new_response
                except Exception as e:
                    logger.debug(f"Error handling checkpoint redirect: {str(e)}")
        
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
                
                # Also try this pattern
                dtsg_alt_match = re.search(r'name="fb_dtsg" value="([^"]+)"', response.text)
                if dtsg_alt_match and not self.fb_dtsg:
                    self.fb_dtsg = dtsg_alt_match.group(1)
                
                # Try to find LSD
                lsd_match = re.search(r'name="lsd" value="([^"]+)"', response.text)
                if lsd_match:
                    self.lsd = lsd_match.group(1)
                
                # Alternate LSD pattern
                lsd_alt_match = re.search(r'"LSD",\[\],{"token":"([^"]+)"', response.text)
                if lsd_alt_match and not self.lsd:
                    self.lsd = lsd_alt_match.group(1)
                    
                # Try to extract tokens from script blocks
                for script_match in re.finditer(r'<script[^>]*>(.*?)</script>', response.text, re.DOTALL):
                    script_content = script_match.group(1)
                    
                    # Look for token definitions in JavaScript
                    if not self.fb_dtsg:
                        fb_dtsg_js = re.search(r'DTSGInitialData["\']?\s*,\s*(?:\{\s*token\s*:\s*|["\'])([^"\']+)', script_content)
                        if fb_dtsg_js:
                            self.fb_dtsg = fb_dtsg_js.group(1)
                    
                    if not self.lsd:
                        lsd_js = re.search(r'LSD["\']?\s*,\s*(?:\{\s*token\s*:\s*|["\'])([^"\']+)', script_content)
                        if lsd_js:
                            self.lsd = lsd_js.group(1)
        except Exception as e:
            logger.debug(f"Error extracting tokens: {str(e)}")
    
    def _store_important_cookies(self):
        """Store important cookies for later use"""
        cookies = self.session.cookies.get_dict()
        
        # Store datr cookie which is important for Facebook sessions
        if 'datr' in cookies and not self.datr_cookie:
            self.datr_cookie = cookies['datr']
    
    def _configure_proxy(self, proxy):
        """Configure the session to use a proxy with improved handling"""
        if not proxy:
            return

        try:
            # Fix: Ensure we're using a consistent proxy format
            if isinstance(proxy, dict):
                if 'url' in proxy:
                    # Direct URL format
                    proxy_url = proxy['url']
                    self.session.proxies.update({
                        'http': proxy_url,
                        'https': proxy_url
                    })
                elif 'username' in proxy and 'password' in proxy and 'ip' in proxy and 'port' in proxy:
                    # Username/password + IP/port format
                    proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
                    self.session.proxies.update({
                        'http': proxy_url,
                        'https': proxy_url
                    })
                elif 'ip' in proxy and 'port' in proxy:
                    # Simple IP/port format
                    proxy_url = f"http://{proxy['ip']}:{proxy['port']}"
                    self.session.proxies.update({
                        'http': proxy_url,
                        'https': proxy_url
                    })
                else:
                    # Try to extract from http/https keys if present
                    if 'http' in proxy or 'https' in proxy:
                        self.session.proxies.update(proxy)
            elif isinstance(proxy, str):
                # String format (URL)
                self.session.proxies.update({
                    'http': proxy,
                    'https': proxy
                })
                
            logger.debug(f"Configured proxy: {self.session.proxies}")
        except Exception as e:
            print(f"Error configuring proxy: {str(e)}")
    
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
    
    def get(self, url, headers=None, allow_redirects=True, referer=None, timeout=None, max_redirects=10):
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
                # Add jitter to request timing to seem more human
                time.sleep(random.uniform(0.1, 0.3))
                
                response = self.session.get(
                    url,
                    headers=headers,
                    allow_redirects=allow_redirects,
                    timeout=timeout
                )
                
                # Update current URL
                self.current_url = response.url
                
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
                logger.debug(f"Too many redirects for URL: {url}. Trying alternative approach.")
                
                # Try again with alternate approach for Facebook redirect issues
                try:
                    # Use a direct mobile URL approach
                    if 'facebook.com' in url:
                        # Use m.facebook.com instead
                        mobile_url = url.replace('www.facebook.com', 'm.facebook.com')
                        mobile_url = mobile_url.replace('facebook.com', 'm.facebook.com')
                        
                        # Only follow a single redirect
                        single_redirect_response = self.session.get(
                            mobile_url,
                            headers=headers,
                            allow_redirects=False,
                            timeout=timeout
                        )
                        
                        # Restore original redirect setting
                        self.session.max_redirects = original_max_redirects
                        
                        if single_redirect_response.status_code < 300 or single_redirect_response.status_code >= 400:
                            # Not a redirect, return this response
                            return single_redirect_response
                        
                        # Extract redirect URL and try one more time
                        if 'location' in single_redirect_response.headers:
                            redirect_url = single_redirect_response.headers['location']
                            final_response = self.session.get(
                                redirect_url,
                                headers=headers,
                                allow_redirects=False,
                                timeout=timeout
                            )
                            return final_response
                        
                        return single_redirect_response
                except Exception:
                    # Restore original redirect setting
                    self.session.max_redirects = original_max_redirects
                    # Re-raise original exception if our alternative approach fails
                    raise e
                
            except requests.exceptions.InvalidSchema as e:
                # This happens with fbredirect:// protocol
                
                # Try to extract the actual URL from the error message
                match = re.search(r"'(fbredirect://[^']+)'", str(e))
                if match:
                    redirect_url = match.group(1)
                    
                    try:
                        # Parse app redirect URL
                        parsed = urlparse(redirect_url)
                        params = parse_qs(parsed.query)
                        
                        # Extract the real URL from the uri parameter
                        if 'uri' in params:
                            real_url = unquote(params['uri'][0])
                            
                            # Try a direct approach - use the /reg/submit/ endpoint
                            bypass_url = "https://m.facebook.com/reg/submit/"
                            
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
                    except Exception:
                        pass
                
                # Try a direct approach for account creation if regular error handling failed
                try:
                    # Directly access the full version signup page as fallback
                    fallback_url = "https://m.facebook.com/r.php"
                    
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
                except Exception:
                    # Restore original redirect setting before re-raising
                    self.session.max_redirects = original_max_redirects
                    raise e  # Re-raise the original error
                
            except (requests.RequestException, requests.ConnectionError, requests.Timeout) as e:
                if attempt == MAX_RETRIES - 1:
                    # Restore original redirect setting
                    self.session.max_redirects = original_max_redirects
                    raise
                
                # Exponential backoff with jitter
                backoff_time = (2 ** attempt) + random.uniform(0, 1)
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
        headers['X-FB-Friendly-Name'] = 'unknown'
        
        # Facebook Android app specific headers
        headers['X-FB-Client-IP'] = 'True'
        headers['X-FB-Server-Cluster'] = 'True'
        
        # Make it look like the Facebook app for login
        if 'login' in parsed_url.path:
            headers['X-FB-Friendly-Name'] = 'LoginStateController'
        elif 'reg' in parsed_url.path:
            headers['X-FB-Friendly-Name'] = 'RegMobilePage'
    
    def post(self, url, data=None, headers=None, extra_headers=None, allow_redirects=True, referer=None, timeout=None, max_redirects=10):
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
        
        # Add any extra headers provided
        if extra_headers:
            headers.update(extra_headers)
        
        # Add Facebook tokens if available
        if self.fb_dtsg and isinstance(data, dict) and 'fb_dtsg' not in data:
            data['fb_dtsg'] = self.fb_dtsg
        
        if self.lsd and isinstance(data, dict) and 'lsd' not in data:
            data['lsd'] = self.lsd
                
        # Add device info
        self._add_facebook_specific_headers(headers, parsed_url)
        
        # Save current redirect setting
        original_max_redirects = self.session.max_redirects
        
        # Apply max_redirects for this request
        self.session.max_redirects = max_redirects
        
        for attempt in range(MAX_RETRIES):
            try:
                # Add jitter to request timing to seem more human
                time.sleep(random.uniform(0.1, 0.3))
                
                response = self.session.post(
                    url,
                    data=data,
                    headers=headers,
                    allow_redirects=allow_redirects,
                    timeout=timeout
                )
                
                # Update current URL
                self.current_url = response.url
                
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
                logger.debug(f"Too many redirects for POST to URL: {url}. Trying alternative approach.")
                
                # Try a different approach for Facebook redirect issues
                try:
                    # Use a direct mobile URL approach
                    if 'facebook.com' in url:
                        # Try direct API endpoint
                        if 'reg' in url:
                            direct_url = "https://m.facebook.com/reg/submit/?cid=103"
                        elif 'login' in url:
                            direct_url = "https://m.facebook.com/login/device-based/regular/login/?cid=103"
                        else:
                            direct_url = url
                            
                        new_headers = headers.copy()
                        new_headers['Host'] = urlparse(direct_url).netloc
                        
                        # Only follow a single redirect
                        single_redirect_response = self.session.post(
                            direct_url,
                            data=data,
                            headers=new_headers,
                            allow_redirects=False,
                            timeout=timeout
                        )
                        
                        # Restore original redirect setting
                        self.session.max_redirects = original_max_redirects
                        
                        return single_redirect_response
                except Exception:
                    # Restore original redirect setting
                    self.session.max_redirects = original_max_redirects
                    # Re-raise original exception if our alternative approach fails
                    raise e
            
            except requests.exceptions.InvalidSchema as e:
                # This happens with fbredirect:// protocol
                
                # Try to directly post to the regular submission URL
                try:
                    submit_url = "https://m.facebook.com/reg/submit/"
                    
                    new_headers = headers.copy()
                    new_headers['Host'] = 'm.facebook.com'
                    new_headers['Origin'] = 'https://m.facebook.com'
                    
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
                except Exception:
                    # Restore original redirect setting before re-raising
                    self.session.max_redirects = original_max_redirects
                    raise e  # Re-raise the original error
                
            except (requests.RequestException, requests.ConnectionError, requests.Timeout) as e:
                if attempt == MAX_RETRIES - 1:
                    # Restore original redirect setting
                    self.session.max_redirects = original_max_redirects
                    raise
                
                # Exponential backoff with jitter
                backoff_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(backoff_time)
        
        # Should not reach here, but just in case
        self.session.max_redirects = original_max_redirects
        return None
    
    def get_current_url(self):
        """Get the current URL of the session"""
        return self.current_url
    
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
        
    def clear_cookies(self, preserve_fingerprint=False):
        """Clear all cookies in the session but maintain browser fingerprint if requested"""
        if preserve_fingerprint:
            # Save important fingerprinting cookies
            fingerprint_cookies = {}
            for cookie_name in ['datr', 'sb', 'locale', 'wd', 'dpr', 'fr']:
                if self.has_cookie(cookie_name):
                    fingerprint_cookies[cookie_name] = self.get_cookie(cookie_name)
            
            # Clear all cookies
            self.session.cookies.clear()
            
            # Restore fingerprinting cookies
            for name, value in fingerprint_cookies.items():
                self.set_cookie(name, value)
        else:
            # Clear all cookies
            self.session.cookies.clear()
            
            # Setup browser state again
            self._setup_browser_state()
        
    def update_user_agent(self, user_agent=None):
        """Update the user agent"""
        if user_agent is None:
            user_agent = get_random_user_agent()
            
        self.user_agent = user_agent
        self.base_headers['User-Agent'] = user_agent
    
    def wait_after_creation(self, seconds=5):
        """Wait after account creation to let Facebook process changes"""
        # Add some jitter to the wait time to make it look more natural
        jittered_time = seconds + random.uniform(-0.5, 1.5)
        time.sleep(max(1, jittered_time))
        
    def get_cookies_json(self):
        """Return cookies in JSON format for saving"""
        cookies = []
        for cookie in self.session.cookies:
            cookies.append({
                'name': cookie.name,
                'value': cookie.value,
                'domain': cookie.domain,
                'path': cookie.path,
                'expires': cookie.expires,
                'secure': cookie.secure,
                'httpOnly': cookie.has_nonstandard_attr('httponly')
            })
        return json.dumps(cookies)