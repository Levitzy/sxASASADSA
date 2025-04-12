"""
Proxy handling and rotation
"""

import os
import sys
import random
import logging
import requests
import time
from pathlib import Path
from config import PROXY_API_URL, PROXY_FILE, USER_AGENTS

# Configure logger
logger = logging.getLogger("FBAccountCreator")

class ProxyManager:
    def __init__(self):
        """Initialize the proxy manager"""
        self.proxies = []
        self.working_proxies = []
        self.current_proxy = None
        self.proxy_file = PROXY_FILE
        self.working_proxies_file = Path(__file__).resolve().parent / "working_proxies.txt"
    
    def load_proxies(self):
        """Load proxies from API or local file"""
        # First try to load working proxies if available
        if os.path.exists(self.working_proxies_file):
            working_loaded = self._load_working_proxies()
            if working_loaded and len(self.working_proxies) > 0:
                print(f"Loaded {len(self.working_proxies)} working proxies")
                
                # Also load all proxies as backup
                if os.path.exists(self.proxy_file):
                    self._load_proxies_from_file()
                    print(f"Also loaded {len(self.proxies)} backup proxies")
                
                return True
        
        # If no working proxies, try to load from standard file
        if os.path.exists(self.proxy_file):
            print(f"Loading proxies from local file")
            return self._load_proxies_from_file()
        
        # If no local cache, fetch from API
        print("Fetching proxies from API")
        return self._fetch_proxies_from_api()
    
    def _load_working_proxies(self):
        """Load working proxies from file"""
        try:
            with open(self.working_proxies_file, 'r') as file:
                lines = file.readlines()
                
            # Parse each line to extract proxy information
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(':')
                    
                    # Handle different proxy formats
                    if len(parts) == 4:
                        # Format: IP:Port:Username:Password
                        ip, port, username, password = parts
                        
                        self.working_proxies.append({
                            'ip': ip,
                            'port': port,
                            'username': username,
                            'password': password,
                            'url': f"http://{username}:{password}@{ip}:{port}"
                        })
                    elif len(parts) == 2:
                        # Format: IP:Port
                        ip, port = parts
                        self.working_proxies.append({
                            'ip': ip,
                            'port': port,
                            'url': f"http://{ip}:{port}"
                        })
            
            logger.debug(f"Loaded {len(self.working_proxies)} working proxies from file")
            return len(self.working_proxies) > 0
            
        except Exception as e:
            logger.error(f"Error loading working proxies from file: {str(e)}")
            return False
    
    def _load_proxies_from_file(self):
        """Load proxies from local file"""
        try:
            with open(self.proxy_file, 'r') as file:
                lines = file.readlines()
                
            # Parse each line to extract proxy information
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(':')
                    
                    # Handle different proxy formats
                    if len(parts) == 4:
                        # Format: IP:Port:Username:Password
                        ip, port, username, password = parts
                        
                        self.proxies.append({
                            'ip': ip,
                            'port': port,
                            'username': username,
                            'password': password,
                            'url': f"http://{username}:{password}@{ip}:{port}"
                        })
                    elif len(parts) == 2:
                        # Format: IP:Port
                        ip, port = parts
                        self.proxies.append({
                            'ip': ip,
                            'port': port,
                            'url': f"http://{ip}:{port}"
                        })
                    elif '@' in line:
                        # Format: username:password@ip:port
                        auth, server = line.split('@')
                        username, password = auth.split(':')
                        ip, port = server.split(':')
                        
                        self.proxies.append({
                            'ip': ip,
                            'port': port,
                            'username': username,
                            'password': password,
                            'url': f"http://{username}:{password}@{ip}:{port}"
                        })
            
            logger.debug(f"Loaded {len(self.proxies)} proxies from file")
            return len(self.proxies) > 0
            
        except Exception as e:
            logger.error(f"Error loading proxies from file: {str(e)}")
            return False
    
    def _fetch_proxies_from_api(self):
        """Fetch proxies from the API"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.proxy_file), exist_ok=True)
            
            # Fetch the proxy list
            response = requests.get(PROXY_API_URL)
            response.raise_for_status()
            
            # Save the response to a file
            with open(self.proxy_file, 'wb') as file:
                file.write(response.content)
            
            logger.debug(f"Saved proxy list to {self.proxy_file}")
            
            # Now load the proxies from the file
            return self._load_proxies_from_file()
            
        except Exception as e:
            logger.error(f"Error fetching proxies from API: {str(e)}")
            return False
    
    def get_proxy(self):
        """Get a random proxy preferring working proxies if available"""
        # Use working proxies if available
        if self.working_proxies:
            self.current_proxy = random.choice(self.working_proxies)
            return self.current_proxy
        
        # Otherwise use any proxy
        if self.proxies:
            self.current_proxy = random.choice(self.proxies)
            return self.current_proxy
        
        print("No proxies available")
        return None
    
    def get_next_proxy(self):
        """Get the next proxy in the list"""
        # Use working proxies if available
        if self.working_proxies:
            # If no current proxy, get a random one
            if not self.current_proxy:
                return self.get_proxy()
            
            # Try to find current proxy in working proxies
            try:
                current_index = self.working_proxies.index(self.current_proxy)
                next_index = (current_index + 1) % len(self.working_proxies)
                self.current_proxy = self.working_proxies[next_index]
                return self.current_proxy
            except ValueError:
                # Current proxy not found in working proxies, get a random one
                return self.get_proxy()
        
        # Otherwise use regular proxies
        if self.proxies:
            # If no current proxy, get a random one
            if not self.current_proxy:
                return self.get_proxy()
            
            # Try to find current proxy in the list
            try:
                current_index = self.proxies.index(self.current_proxy)
                next_index = (current_index + 1) % len(self.proxies)
                self.current_proxy = self.proxies[next_index]
                return self.current_proxy
            except ValueError:
                # If current proxy not found, get a random one
                return self.get_proxy()
        
        print("No proxies available")
        return None
    
    def format_for_requests(self, proxy=None):
        """Format the proxy for use with requests library"""
        if not proxy:
            proxy = self.current_proxy
            
        if not proxy:
            return None
        
        # Check if proxy has authentication
        if 'username' in proxy and 'password' in proxy:
            return {
                'http': f"http://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}",
                'https': f"http://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
            }
        else:
            return {
                'http': f"http://{proxy['ip']}:{proxy['port']}",
                'https': f"http://{proxy['ip']}:{proxy['port']}"
            }
    
    def remove_current_proxy(self):
        """Remove the current proxy from the lists if it's not working"""
        if not self.current_proxy:
            return False
            
        removed = False
        
        # Remove from working proxies if present
        if self.current_proxy in self.working_proxies:
            self.working_proxies.remove(self.current_proxy)
            logger.debug(f"Removed non-working proxy from working list: {self.current_proxy['ip']}:{self.current_proxy['port']}")
            removed = True
            
            # Update working proxies file
            self._save_working_proxies()
        
        # Remove from main proxies if present
        if self.current_proxy in self.proxies:
            self.proxies.remove(self.current_proxy)
            logger.debug(f"Removed non-working proxy from main list: {self.current_proxy['ip']}:{self.current_proxy['port']}")
            removed = True
        
        self.current_proxy = None
        return removed
    
    def _save_working_proxies(self):
        """Save working proxies to file"""
        try:
            with open(self.working_proxies_file, 'w') as f:
                for proxy in self.working_proxies:
                    if 'username' in proxy and 'password' in proxy:
                        f.write(f"{proxy['ip']}:{proxy['port']}:{proxy['username']}:{proxy['password']}\n")
                    else:
                        f.write(f"{proxy['ip']}:{proxy['port']}\n")
            
            logger.debug(f"Saved {len(self.working_proxies)} working proxies to {self.working_proxies_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving working proxies: {str(e)}")
            return False
    
    def test_proxy(self, proxy, silent=False):
        """Test if a proxy can connect to Facebook"""
        # Create a session with the proxy
        session = requests.Session()
        
        # Format proxy for requests
        formatted_proxy = self.format_for_requests(proxy)
        session.proxies.update(formatted_proxy)
        
        # Set a random user agent
        user_agent = random.choice(USER_AGENTS)
        
        # Set session headers
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.google.com/',
            'Host': 'm.facebook.com'
        }
        
        # Limit redirects to avoid loops
        session.max_redirects = 5
        
        try:
            # Test connection to Facebook
            start_time = time.time()
            response = session.get(
                'https://m.facebook.com/favicon.ico',  # Just fetch the favicon to test connectivity
                headers=headers,
                timeout=10,
                allow_redirects=True
            )
            end_time = time.time()
            
            # Check if the request was successful (status code 2xx)
            if response.status_code >= 200 and response.status_code < 300:
                if not silent:
                    print(f"✓ Proxy {proxy['ip']}:{proxy['port']} WORKS for Facebook ({response.status_code}, {end_time - start_time:.2f}s)")
                return True
            else:
                if not silent:
                    print(f"✗ Proxy {proxy['ip']}:{proxy['port']} FAILED ({response.status_code})")
                return False
                
        except requests.exceptions.TooManyRedirects:
            if not silent:
                print(f"✗ Proxy {proxy['ip']}:{proxy['port']} FAILED - Too many redirects")
            return False
        except requests.exceptions.RequestException as e:
            if not silent:
                print(f"✗ Proxy {proxy['ip']}:{proxy['port']} FAILED - {str(e)}")
            return False
    
    def find_working_proxies(self, max_to_test=None, silent=False):
        """Test proxies and save working ones"""
        all_proxies = self.proxies.copy()
        random.shuffle(all_proxies)  # Randomize order
        
        if max_to_test and max_to_test < len(all_proxies):
            proxies_to_test = all_proxies[:max_to_test]
            if not silent:
                print(f"Testing {max_to_test} proxies out of {len(all_proxies)}")
        else:
            proxies_to_test = all_proxies
            if not silent:
                print(f"Testing all {len(all_proxies)} proxies")
        
        self.working_proxies = []
        
        for i, proxy in enumerate(proxies_to_test):
            if not silent:
                print(f"Testing proxy {i+1}/{len(proxies_to_test)}: {proxy['ip']}:{proxy['port']}")
            
            if self.test_proxy(proxy, silent=silent):
                self.working_proxies.append(proxy)
            
            # Small delay between tests to avoid rate limiting
            time.sleep(0.5)
        
        if not silent:
            print(f"Testing completed. Found {len(self.working_proxies)} working proxies.")
        
        # Save working proxies to file
        if self.working_proxies:
            self._save_working_proxies()
        
        return len(self.working_proxies) > 0