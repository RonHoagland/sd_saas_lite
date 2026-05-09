import time
import urllib.request
import urllib.parse
import http.cookiejar
from html.parser import HTMLParser

# Configuration
BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BASE_URL}/accounts/login/"
USERNAME = "admin"
PASSWORD = "admin123"

# Setup Cookies
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

class CSRFParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.csrf_token = None

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            dict_attrs = dict(attrs)
            if dict_attrs.get("name") == "csrfmiddlewaretoken":
                self.csrf_token = dict_attrs.get("value")

def get_csrf_token():
    response = opener.open(LOGIN_URL)
    html = response.read().decode('utf-8')
    parser = CSRFParser()
    parser.feed(html)
    return parser.csrf_token

def login():
    print(f"Logging in as {USERNAME}...")
    csrf_token = get_csrf_token()
    
    data = urllib.parse.urlencode({
        "username": USERNAME,
        "password": PASSWORD,
        "csrfmiddlewaretoken": csrf_token
    }).encode('utf-8')
    
    headers = {
        "Referer": LOGIN_URL
    }
    
    req = urllib.request.Request(LOGIN_URL, data=data, headers=headers)
    response = opener.open(req)
    # Check if we were redirected to dashboard (or whatever DEFAULT_REDIRECT_URL is)
    print(f"Login Response: {response.getcode()} (Final URL: {response.geturl()})")

def measure(url_path):
    url = f"{BASE_URL}{url_path}"
    start_time = time.time()
    try:
        response = opener.open(url)
        content = response.read()
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        size_kb = len(content) / 1024
        print(f"GET {url_path:<25} : {duration_ms:>6.2f} ms | {size_kb:>6.2f} KB | Status: {response.getcode()}")
        return duration_ms
    except Exception as e:
        print(f"GET {url_path:<25} : FAILED ({str(e)})")
        return None

if __name__ == "__main__":
    try:
        login()
        
        print("\n--- Performance Metrics (TTFB + Download) ---")
        pages = [
            "/",
            "/admin-area/",
            "/identity/users/",
            "/audit/",
            "/backup/"
        ]
        
        results = []
        for p in pages:
            dur = measure(p)
            if dur:
                results.append(dur)
                
        if results:
            avg = sum(results) / len(results)
            print(f"\nAverage Page Load: {avg:.2f} ms")
            if avg < 500:
                print("PASS: Average < 500ms")
            else:
                print("WARN: Average > 500ms")
                
    except Exception as e:
        print(f"Performance test failed: {e}")
