import os
import json
import time
from playwright.sync_api import sync_playwright

class PlaywrightInterceptEngine:
    def __init__(self, state_file="session_state.json", headless=True):
        self.state_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", state_file)
        self.headless = headless
        
    def execute_with_interception(self, url, api_pattern, wait_for_selector=None):
        """
        Navigates to URL, intercepts the chosen API network request (XHR/Fetch),
        returns its JSON response without needing DOM parsing.
        """
        if not os.path.exists(self.state_file):
            raise FileNotFoundError(f"State file {self.state_file} missing. Run cdp_session_cloner.py first.")
            
        intercepted_data = None
        
        def handle_response(response):
            nonlocal intercepted_data
            if api_pattern in response.url and response.status == 200:
                try:
                    # Some responses might not be JSON or might fail parsing
                    intercepted_data = response.json()
                except Exception:
                    pass

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(storage_state=self.state_file)
                page = context.new_page()
                
                # Listen to network responses
                page.on("response", handle_response)
                
                print(f"🌐 Navigating to {url} ...")
                page.goto(url, wait_until="networkidle")
                
                if wait_for_selector:
                    page.wait_for_selector(wait_for_selector)
                    
                # Give it a small buffer to finish resolving API
                time.sleep(3)
                
                browser.close()
                return intercepted_data
                
        except Exception as e:
            print(f"❌ Playwright Engine Error: {e}")
            return None

if __name__ == "__main__":
    # Test example
    engine = PlaywrightInterceptEngine(headless=True)
    # The URL and API pattern would be replaced by actual target (e.g. XHS user profile / Twitter timeline)
    # This is just an illustrative test layout
    print("Engine Ready. To intercept, call execute_with_interception(url, api_pattern)")
