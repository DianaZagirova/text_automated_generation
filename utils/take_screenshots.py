import os
import hashlib
from typing import Optional
from playwright.sync_api import sync_playwright, Response
import requests


def is_valid_screenshot(path: str) -> bool:
    """Validate screenshot content using basic image analysis."""
    try:
        from PIL import Image
        with Image.open(path) as img:
            # Check for dominant color indicating blank page
            extrema = img.convert("L").getextrema()
            if extrema[0] == extrema[1]:  # Solid color
                return False
            
            # Check reasonable dimensions
            return img.width >= 1024 and img.height >= 768
    except Exception:
        return False

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
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://www.google.com/'
                },
                # Enable adblocker
                bypass_csp=True
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
                # Track network responses for errors
                status_code = [None]
                def check_response(response):
                    if 400 <= response.status < 600:
                        status_code[0] = response.status

                page.on("response", check_response)

                # Navigate with extended timeout and wait for DOM stability
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Check for HTTP errors first
                if status_code[0] and status_code[0] >= 400:
                    print(f"HTTP Error {status_code[0]} for {url}")
                    return None

                # Wait for content stabilization
                page.wait_for_load_state("networkidle", timeout=30000)
                page.wait_for_function(
                    "() => document.readyState === 'complete'",
                    timeout=30000
                )

                # Check for common error pages using XPath
                error_texts = [
                    "403", "404", "forbidden", "not found", "error",
                    "service unavailable", "access denied", "gateway timeout"
                ]
                error_xpath = "|".join([f"contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')" 
                                      for text in error_texts])
                error_element = page.query_selector(f"xpath=//*[{error_xpath}]")
                if error_element:
                    print(f"Error content detected on {url}")
                    return None


                # Remove unwanted elements with multiple passes
                for _ in range(3):  # Multiple attempts to catch dynamic elements
                    page.evaluate("""() => {
                        const selectors = [
                            'div[class*="cookie"], div[class*="consent"], div[class*="popup"], div[class*="modal"]',
                            'div[class*="banner"], div[class*="notice"], div[class*="overlay"]',
                            'iframe[src*="cookie"], iframe[src*="consent"]',
                            'button[class*="close"], svg[class*="close"], [aria-label*="close"]',
                            '[class*="gdpr"], [class*="cc_banner"], #cookieConsent',
                            'div[class*="advertisement"], div[class*="marketing"]'
                        ].join(',');
                        
                        document.querySelectorAll(selectors).forEach(element => {
                            element.remove();
                        });
                        
                        // Hide scrollbars for consistent screenshots
                        document.documentElement.style.overflow = 'hidden';
                        document.body.style.overflow = 'hidden';
                    }""")
                    page.wait_for_timeout(800)  # Wait between removal passes

                # Ensure main content visibility
                page.evaluate("""() => {
                    const mainContent = document.querySelector('main, article, .main-content') 
                                     || document.body;
                    mainContent.style.visibility = 'visible';
                    mainContent.style.opacity = '1';
                }""")

                # Take full-page screenshot with quality adjustments
                screenshot_params = {
                    'path': filepath,
                    'full_page': True,
                    'quality': 90,
                    'animations': 'disabled',
                    'mask': page.query_selector_all('[aria-hidden="true"]')
                }
                page.screenshot(**screenshot_params)

                # Verify screenshot content
                if not is_valid_screenshot(filepath):
                    os.remove(filepath)
                    return None

                return filepath
            except PlaywrightTimeoutError:
                print(f"Timeout loading {url}")
                return None
            except Exception as e:
                print(f"Error capturing {url}: {str(e)}")
                return None
            finally:
                context.close()
                browser.close()

    except Exception as e:
        print(f"[ERROR] Exception in screenshot process for {url}: {e}")
        return None