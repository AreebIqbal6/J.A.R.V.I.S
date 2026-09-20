from playwright.sync_api import sync_playwright

def VisualWebAutomator(url: str, extraction_goal: str = ""):
    """
    Spawns a headless browser to visually parse a webpage and extract content, 
    bypassing traditional anti-scraping blockers.
    """
    print(f">> [VISION WEB ENGINE]: Deploying headless browser to {url}...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Stealth-like headers
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Allow time for JS frameworks to render
            page.wait_for_timeout(2000)
            
            # Extract all visible text
            body_text = page.locator("body").inner_text()
            title = page.title()
            
            browser.close()
            
            if not body_text.strip():
                return f"Successfully accessed {url}, but no visible text was found. The page might be rendering dynamically."
                
            # If the text is massive, we truncate it for the LLM context window
            snippet = body_text[:2000] + "\n...[TRUNCATED]" if len(body_text) > 2000 else body_text
            
            return (
                f"--- VISUAL PARSE REPORT for {title} ---\n"
                f"URL: {url}\n"
                f"Extraction Goal: {extraction_goal}\n\n"
                f"{snippet}\n"
                f"--- END OF REPORT ---"
            )

    except Exception as e:
        return f"Visual Web Automator failed to process {url}. Error: {str(e)}"
