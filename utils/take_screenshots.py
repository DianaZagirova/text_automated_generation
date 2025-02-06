import os
import hashlib
from typing import Optional
from playwright.sync_api import sync_playwright, Response
import requests

def take_screenshots(url: str, screenshots_dir: str) -> Optional[str]:
    """
    Takes a screenshot of the given URL in a Chromium browser using Playwright.
    Skips pages that have HTTP errors (403, 404, etc.) or obvious error messages,
    removes pop-ups/cookie banners, and saves an informative screenshot.
    Returns the file path to the screenshot on success, or None on failure.
    """
    # 1. Construct unique screenshot filename
    url_hash = hashlib.md5(url.encode()).hexdigest()
    filepath = os.path.join(screenshots_dir, f"{url_hash}.png")
    if os.path.exists(filepath):
        # If we already have a screenshot for this URL, return that path
        return filepath

    try:
        with sync_playwright() as p:
            # 2. Launch the browser
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36"
                )
            )
            
            # 3. Block common ad networks and trackers
            def block_ads(route):
                route.abort()
            ad_patterns = [
                "**/*analytics*",
                "**/*ads*",
                "**/*doubleclick*",
                "**/*facebook*",
                "**/*tracking*",
                "**/*metrics*",
            ]
            for pattern in ad_patterns:
                context.route(pattern, block_ads)

            # 4. Create a new page
            page = context.new_page()

            try:
                # 5. Navigate to the URL, capture the response to check status code
                response: Response = page.goto(
                    url, wait_until="networkidle", timeout=30000
                )
                
                if not response:
                    print(f"[ERROR] No response received for URL: {url}")
                    return None

                if response.status >= 400:
                    print(f"[ERROR] HTTP {response.status} for URL: {url}")
                    return None

                # 6. Wait for the page to settle a bit (extra time for JS or lazy loading)
                page.wait_for_timeout(2000)

                # 7. Check for obvious textual errors on the page
                error_selectors = [
                    "text=Access Denied",
                    "text=403 Forbidden",
                    "text=404 Not Found",
                    "text=Error",
                    "text=Page Not Found",
                    "text=Service Unavailable",
                    "text=Bad Gateway",
                    "text=Gateway Timeout"
                ]
                for selector in error_selectors:
                    try:
                        if page.locator(selector).count() > 0:
                            print(f"[ERROR] Found error text on page: {selector}")
                            return None
                    except Exception:
                        # Continue safely if locator logic fails
                        continue

                # 8. Remove common cookie banners, modals, popups, etc.
                page.evaluate(
                    """() => {
                        const removeElementsBySelectors = (selectors) => {
                            selectors.forEach(sel => {
                                document.querySelectorAll(sel).forEach(el => el.remove());
                            });
                        };

                        const popupSelectors = [
                            '[class*="cookie"]',
                            '[class*="consent"]',
                            '[class*="popup"]',
                            '[class*="modal"]',
                            '[class*="banner"]',
                            '[class*="notification"]',
                            '[class*="subscribe"]',
                            '[class*="newsletter"]',
                            '[id*="cookie"]',
                            '[id*="consent"]',
                            '[id*="popup"]',
                            '[id*="modal"]',
                            '[id*="banner"]',
                            '[id*="notification"]',
                            '[id*="subscribe"]',
                            '[id*="newsletter"]'
                        ];
                        removeElementsBySelectors(popupSelectors);
                    }"""
                )

                # 9. Wait an additional second for any transitions/animations
                page.wait_for_timeout(1000)

                # 10. Take the screenshot
                page.screenshot(path=filepath)

                # 11. Quick check for file size to ensure it's not an empty placeholder
                if os.path.getsize(filepath) < 5000:  # threshold in bytes
                    print(f"[WARNING] Screenshot too small, indicating possible error page for {url}")
                    os.remove(filepath)
                    return None

                return filepath

            except Exception as e:
                print(f"[ERROR] Exception taking screenshot of {url}: {e}")
                return None

            finally:
                browser.close()

    except Exception as e:
        print(f"[ERROR] Exception in screenshot process for {url}: {e}")
        return None