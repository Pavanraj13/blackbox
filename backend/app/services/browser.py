import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

DESKTOP_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

class BrowserManager:
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
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
        self.context = await self.browser.new_context(
            viewport={'width': 1440, 'height': 900},
            device_scale_factor=1.25,
            user_agent=DESKTOP_USER_AGENT,
            locale="en-US"
        )
        self.page = await self.context.new_page()

        def _on_new_page(new_page: Page):
            self.page = new_page

        self.context.on("page", _on_new_page)

    async def _strip_target_blank(self):
        """Prevents links from opening unwanted new tabs, keeping navigation in the active tab."""
        if not self.page:
            return
        try:
            await self.page.evaluate("""() => {
                try {
                    document.querySelectorAll('a[target="_blank"]').forEach(a => a.removeAttribute('target'));
                } catch(e) {}
            }""")
        except Exception:
            pass

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
        await self._strip_target_blank()
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
                if await btn.is_visible(timeout=400):
                    await btn.click(timeout=800)
                    await self.page.wait_for_timeout(400)
                    break
            except Exception:
                pass

    async def take_screenshot(self, path: str, full_page: bool = False):
        if not self.page:
            raise RuntimeError("Browser page not initialized")
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=2000)
        except Exception:
            pass
        await self.page.wait_for_timeout(350)
        await self.page.screenshot(path=path, full_page=full_page)

    async def highlight_element(self, target_element: Optional[Dict[str, Any]], step_number: int, action: str):
        """Draws a visual target indicator and action label on the element for clear screenshot documentation."""
        if not self.page or not target_element:
            return
        selector = target_element.get("selector")
        x = target_element.get("x", 0)
        y = target_element.get("y", 0)
        w = target_element.get("width", 0)
        h = target_element.get("height", 0)
        try:
            await self.page.evaluate("""({ sel, x, y, w, h, step, act }) => {
                try {
                    document.querySelectorAll('.blackbox-action-overlay').forEach(el => el.remove());
                    let el = null;
                    if (sel) {
                        try { el = document.querySelector(sel); } catch(e) {}
                    }
                    if (!el && x !== undefined && y !== undefined && w > 0 && h > 0) {
                        try { el = document.elementFromPoint(x + w / 2, y + h / 2); } catch(e) {}
                    }

                    let rect = null;
                    if (el) {
                        try { el.scrollIntoView({ behavior: 'instant', block: 'center' }); } catch(e) {}
                        rect = el.getBoundingClientRect();
                        el.style.outline = '3px solid #2563eb';
                        el.style.outlineOffset = '2px';
                        el.style.boxShadow = '0 0 16px rgba(37, 99, 235, 0.7)';
                        el.setAttribute('data-blackbox-highlight', 'true');
                    } else if (w > 0 && h > 0) {
                        rect = { top: y, left: x, width: w, height: h };
                        const box = document.createElement('div');
                        box.className = 'blackbox-action-overlay';
                        box.style.position = 'fixed';
                        box.style.top = y + 'px';
                        box.style.left = x + 'px';
                        box.style.width = w + 'px';
                        box.style.height = h + 'px';
                        box.style.border = '3px solid #2563eb';
                        box.style.boxShadow = '0 0 16px rgba(37, 99, 235, 0.7)';
                        box.style.pointerEvents = 'none';
                        box.style.zIndex = '999998';
                        document.body.appendChild(box);
                    }

                    if (rect) {
                        const badge = document.createElement('div');
                        badge.className = 'blackbox-action-overlay';
                        badge.style.position = 'fixed';
                        badge.style.top = Math.max(6, rect.top - 28) + 'px';
                        badge.style.left = Math.max(6, rect.left) + 'px';
                        badge.style.backgroundColor = '#1d4ed8';
                        badge.style.color = '#ffffff';
                        badge.style.fontFamily = 'monospace';
                        badge.style.fontSize = '12px';
                        badge.style.fontWeight = 'bold';
                        badge.style.padding = '3px 8px';
                        badge.style.borderRadius = '4px';
                        badge.style.zIndex = '999999';
                        badge.style.boxShadow = '0 2px 8px rgba(0,0,0,0.4)';
                        badge.style.pointerEvents = 'none';
                        badge.innerText = `STEP ${step}: ${act}`;
                        document.body.appendChild(badge);
                    }
                } catch(e) {}
            }""", {"sel": selector, "x": x, "y": y, "w": w, "h": h, "step": step_number, "act": action})
            await self.page.wait_for_timeout(250)
        except Exception:
            pass

    async def clear_highlight(self):
        """Clears highlight markers from page after screenshot is captured."""
        if not self.page:
            return
        try:
            await self.page.evaluate("""() => {
                try {
                    document.querySelectorAll('.blackbox-action-overlay').forEach(el => el.remove());
                    document.querySelectorAll('[data-blackbox-highlight]').forEach(el => {
                        el.style.outline = '';
                        el.style.outlineOffset = '';
                        el.style.boxShadow = '';
                        el.removeAttribute('data-blackbox-highlight');
                    });
                } catch(e) {}
            }""")
        except Exception:
            pass


    async def execute_action(self, action_data: Dict[str, Any], target_element: Optional[Dict[str, Any]] = None) -> bool:
        if not self.page:
            return False

        # Ensure active tab is synchronized
        if self.context and len(self.context.pages) > 0:
            self.page = self.context.pages[-1]

        await self._strip_target_blank()
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

                        try:
                            await self.page.click(selector, timeout=2500)
                        except Exception:
                            # Try with force=True (handles overlay spans / transparent inputs like Amazon buttons)
                            await self.page.click(selector, timeout=2000, force=True)
                    except Exception:
                        # Fallback to coordinate click if selector fails
                        x = target_element.get("x", 0) + (target_element.get("width", 0) / 2)
                        y = target_element.get("y", 0) + (target_element.get("height", 0) / 2)
                        await self.page.mouse.click(x, y)
                elif target_element:
                    x = target_element.get("x", 0) + (target_element.get("width", 0) / 2)
                    y = target_element.get("y", 0) + (target_element.get("height", 0) / 2)
                    await self.page.mouse.click(x, y)

                await self.page.wait_for_timeout(1200)
                # Check if a new tab opened
                if self.context and len(self.context.pages) > 0:
                    self.page = self.context.pages[-1]
                await self._strip_target_blank()
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

                await self.page.wait_for_timeout(1500)
                if self.context and len(self.context.pages) > 0:
                    self.page = self.context.pages[-1]
                await self._strip_target_blank()
                return True

            elif action_type == "SCROLL":
                direction = action_data.get("direction", "down").lower()
                amount = action_data.get("amount", 600)
                delta_y = amount if direction == "down" else -amount
                await self.page.evaluate(f"window.scrollBy({{ top: {delta_y}, behavior: 'smooth' }})")
                await self.page.wait_for_timeout(800)
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
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
