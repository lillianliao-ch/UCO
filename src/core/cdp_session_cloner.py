import json
import os
import argparse
from playwright.sync_api import sync_playwright

def clone_session(cdp_url="http://localhost:9222", output_file="session_state.json"):
    print(f"🔄 Connecting to existing Chrome instance at {cdp_url} ...")
    try:
        with sync_playwright() as p:
            # Connect to existing Chrome over CDP
            browser = p.chromium.connect_over_cdp(cdp_url)
            
            # Get the default context (where the user's tabs and cookies live)
            contexts = browser.contexts
            if not contexts:
                print("❌ No browser contexts found.")
                return False
                
            context = contexts[0]
            
            # Extract cookies
            cookies = context.cookies()
            print(f"🍪 Extracted {len(cookies)} cookies.")
            
            # Since Playwright's state extraction handles both cookies and origins' localStorage,
            # we can use the built-in storage_state method.
            state = context.storage_state()
            
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", output_file)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=4)
                
            print(f"✅ Session state successfully cloned to {output_path}")
            
            # Detach gracefully (do not close the user's browser)
            browser.close()
            return True
            
    except Exception as e:
        print(f"❌ Failed to connect or extract session: {e}")
        print("💡 Ensure Chrome is running with: --remote-debugging-port=9222")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract Cookies and LocalStorage via CDP")
    parser.add_argument("--port", type=int, default=9222, help="CDP debugging port")
    parser.add_argument("--out", type=str, default="session_state.json", help="Output JSON file name in root directory")
    args = parser.parse_args()
    
    clone_session(cdp_url=f"http://localhost:{args.port}", output_file=args.out)
