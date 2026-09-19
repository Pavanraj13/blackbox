import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, Playwright

DESKTOP_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

class BrowserManager:
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def start(self, headless: bool = True):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            device_scale_factor=1,
            user_agent=DESKTOP_USER_AGENT,
            locale="en-US"
        )
        self.page = await context.new_page()

    async def navigate(self, url: str):
        if not self.page:
            raise RuntimeError("Browser page not initialized")
        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            if "localhost" in url or "127.0.0.1" in url:
                url = f"http://{url}"
            else:
                url = f"https://{url}"

        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=25000)
        except Exception:
            try:
                await self.page.goto(url, timeout=15000)
            except Exception as e:
                print(f"[BrowserManager] Navigate warning for {url}: {e}")

        await self.page.wait_for_timeout(1200)
        await self._auto_dismiss_cookie_popups()

    async def _auto_dismiss_cookie_popups(self):
        """Attempts to auto-dismiss prominent cookie banners so they don't block interaction on public sites."""
        if not self.page:
            return
        cookie_selectors = [
            '#onetrust-accept-btn-handler',
            '#accept-cookie-notification',
            'button#didomi-notice-agree-button',
            'button[id*="cookie-accept"]',
            'button[class*="cookie-accept"]',
            'a[id*="cookie-accept"]',
            'button[aria-label="Accept all"]',
            'button[aria-label="Accept cookies"]'
        ]
        for sel in cookie_selectors:
            try:
                btn = self.page.locator(sel).first
                if await btn.is_visible(timeout=500):
                    await btn.click(timeout=1000)
                    await self.page.wait_for_timeout(500)
                    break
            except Exception:
                pass

    async def take_screenshot(self, path: str):
        if not self.page:
            raise RuntimeError("Browser page not initialized")
        await self.page.screenshot(path=path, full_page=False)

    async def execute_action(self, action_data: Dict[str, Any], target_element: Optional[Dict[str, Any]] = None) -> bool:
        if not self.page:
            return False

        action_type = action_data.get("action", "").upper()

        try:
            if action_type == "CLICK":
                if target_element and target_element.get("selector"):
                    selector = target_element["selector"]
                    try:
                        # Scroll element into view first
                        await self.page.evaluate("""(sel) => {
                            try {
                                const el = document.querySelector(sel);
                                if (el) el.scrollIntoView({ behavior: 'instant', block: 'center' });
                            } catch(e) {}
                        }""", selector)
                        await self.page.wait_for_timeout(200)

                        await self.page.click(selector, timeout=3500)
                    except Exception:
                        # Fallback to coordinate click if selector fails
                        x = target_element.get("x", 0) + (target_element.get("width", 0) / 2)
                        y = target_element.get("y", 0) + (target_element.get("height", 0) / 2)
                        await self.page.mouse.click(x, y)
                elif target_element:
                    x = target_element.get("x", 0) + (target_element.get("width", 0) / 2)
                    y = target_element.get("y", 0) + (target_element.get("height", 0) / 2)
                    await self.page.mouse.click(x, y)

                await self.page.wait_for_timeout(1000)
                await self._auto_dismiss_cookie_popups()
                return True

            elif action_type == "TYPE":
                text_to_type = action_data.get("text", "")
                if target_element and target_element.get("selector"):
                    selector = target_element["selector"]
                    try:
                        await self.page.evaluate("""(sel) => {
                            try {
                                const el = document.querySelector(sel);
                                if (el) el.scrollIntoView({ behavior: 'instant', block: 'center' });
                            } catch(e) {}
                        }""", selector)
                        await self.page.wait_for_timeout(200)

                        await self.page.fill(selector, text_to_type, timeout=3000)
                        await self.page.keyboard.press("Enter")
                    except Exception:
                        await self.page.click(selector, timeout=3000)
                        await self.page.keyboard.type(text_to_type)
                        await self.page.keyboard.press("Enter")
                elif target_element:
                    x = target_element.get("x", 0) + (target_element.get("width", 0) / 2)
                    y = target_element.get("y", 0) + (target_element.get("height", 0) / 2)
                    await self.page.mouse.click(x, y)
                    await self.page.keyboard.type(text_to_type)
                    await self.page.keyboard.press("Enter")
                else:
                    await self.page.keyboard.type(text_to_type)
                    await self.page.keyboard.press("Enter")

                await self.page.wait_for_timeout(1000)
                return True

            elif action_type == "SCROLL":
                direction = action_data.get("direction", "down").lower()
                amount = action_data.get("amount", 600)
                delta_y = amount if direction == "down" else -amount
                await self.page.evaluate(f"window.scrollBy({{ top: {delta_y}, behavior: 'smooth' }})")
                await self.page.wait_for_timeout(700)
                return True

            elif action_type == "BACK":
                try:
                    await self.page.go_back(wait_until="domcontentloaded", timeout=10000)
                except Exception:
                    pass
                await self.page.wait_for_timeout(800)
                return True

            elif action_type == "WAIT":
                await self.page.wait_for_timeout(1500)
                return True

            elif action_type == "FINISH":
                return True

        except Exception as e:
            print(f"[BrowserManager] Action error executing {action_type}: {e}")
            return False

        return False

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.page = None
        self.browser = None
        self.playwright = None
