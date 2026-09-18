import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, Playwright

class BrowserManager:
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def start(self, headless: bool = True):
        self.playwright = await async_playwright().start()
        # Launch Chromium with standard desktop viewport
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            device_scale_factor=1
        )
        self.page = await context.new_page()

    async def navigate(self, url: str):
        if not self.page:
            raise RuntimeError("Browser page not initialized")
        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=20000)
        except Exception:
            try:
                await self.page.goto(url, timeout=15000)
            except Exception as e:
                print(f"[BrowserManager] Navigate warning: {e}")
        await self.page.wait_for_timeout(1000)

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
                    try:
                        await self.page.click(target_element["selector"], timeout=3000)
                    except Exception:
                        # Fallback to coordinate click if selector fails
                        x = target_element.get("x", 0) + (target_element.get("width", 0) / 2)
                        y = target_element.get("y", 0) + (target_element.get("height", 0) / 2)
                        await self.page.mouse.click(x, y)
                elif target_element:
                    x = target_element.get("x", 0) + (target_element.get("width", 0) / 2)
                    y = target_element.get("y", 0) + (target_element.get("height", 0) / 2)
                    await self.page.mouse.click(x, y)
                await self.page.wait_for_timeout(800)
                return True

            elif action_type == "TYPE":
                text_to_type = action_data.get("text", "")
                if target_element and target_element.get("selector"):
                    try:
                        await self.page.fill(target_element["selector"], text_to_type, timeout=3000)
                        await self.page.keyboard.press("Enter")
                    except Exception:
                        await self.page.click(target_element["selector"], timeout=3000)
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
                await self.page.wait_for_timeout(800)
                return True

            elif action_type == "SCROLL":
                direction = action_data.get("direction", "down").lower()
                amount = action_data.get("amount", 600)
                delta_y = amount if direction == "down" else -amount
                await self.page.evaluate(f"window.scrollBy(0, {delta_y})")
                await self.page.wait_for_timeout(500)
                return True

            elif action_type == "BACK":
                try:
                    await self.page.go_back(wait_until="domcontentloaded", timeout=10000)
                except Exception:
                    pass
                await self.page.wait_for_timeout(500)
                return True

            elif action_type == "WAIT":
                await self.page.wait_for_timeout(1000)
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
