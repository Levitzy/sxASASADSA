"""
Test proxies for Facebook connectivity
"""

import os
import sys
import time
import random
import logging
import requests
from pathlib import Path

# Add the parent directory to the Python path
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import USER_AGENTS
from proxies.proxy_manager import ProxyManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ProxyTester")

def test_proxy(proxy):
    """Test if a proxy can connect to Facebook"""
    
    # Create a session with the proxy
    session = requests.Session()
    
    # Format proxy for requests
    if 'username' in proxy and 'password' in proxy:
        proxy_dict = {
            'http': f"http://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}",
            'https': f"http://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
        }
    else:
        proxy_dict = {
            'http': f"http://{proxy['ip']}:{proxy['port']}",
            'https': f"http://{proxy['ip']}:{proxy['port']}"
        }
    
    session.proxies.update(proxy_dict)
    
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
        'Referer': 'https://www.google.com/'
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
            logger.info(f"✓ Proxy {proxy['ip']}:{proxy['port']} WORKS for Facebook (response: {response.status_code}, time: {end_time - start_time:.2f}s)")
            return True
        else:
            logger.warning(f"✗ Proxy {proxy['ip']}:{proxy['port']} FAILED for Facebook (response: {response.status_code})")
            return False
            
    except requests.exceptions.TooManyRedirects:
        logger.warning(f"✗ Proxy {proxy['ip']}:{proxy['port']} FAILED - Too many redirects")
        return False
    except requests.exceptions.RequestException as e:
        logger.warning(f"✗ Proxy {proxy['ip']}:{proxy['port']} FAILED - {str(e)}")
        return False

def test_all_proxies():
    """Test all proxies in the list"""
    proxy_manager = ProxyManager()
    
    if not proxy_manager.load_proxies():
        logger.error("Failed to load proxies")
        return
    
    logger.info(f"Testing {len(proxy_manager.proxies)} proxies for Facebook connectivity...")
    
    working_proxies = []
    
    for i, proxy in enumerate(proxy_manager.proxies):
        logger.info(f"Testing proxy {i+1}/{len(proxy_manager.proxies)}: {proxy['ip']}:{proxy['port']}")
        
        if test_proxy(proxy):
            working_proxies.append(proxy)
        
        # Small delay between tests to avoid rate limiting
        time.sleep(1)
    
    logger.info(f"\nTesting completed. {len(working_proxies)}/{len(proxy_manager.proxies)} proxies are working for Facebook.")
    
    if working_proxies:
        logger.info("Working proxies:")
        for i, proxy in enumerate(working_proxies):
            logger.info(f"{i+1}. {proxy['ip']}:{proxy['port']}")
    
    return working_proxies

if __name__ == "__main__":
    print("=== Facebook Proxy Tester ===")
    print("This script will test all proxies for Facebook connectivity")
    
    working_proxies = test_all_proxies()
    
    # Save working proxies to a file
    if working_proxies:
        working_proxies_file = Path(__file__).resolve().parent / "working_proxies.txt"
        
        with open(working_proxies_file, 'w') as f:
            for proxy in working_proxies:
                if 'username' in proxy and 'password' in proxy:
                    f.write(f"{proxy['ip']}:{proxy['port']}:{proxy['username']}:{proxy['password']}\n")
                else:
                    f.write(f"{proxy['ip']}:{proxy['port']}\n")
        
        print(f"\nSaved {len(working_proxies)} working proxies to {working_proxies_file}")