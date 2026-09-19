import asyncio
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Any, Set
from playwright.async_api import async_playwright

EXCLUDE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
    ".pdf", ".zip", ".tar", ".gz", ".mp4", ".mp3",
    ".css", ".js", ".json", ".xml", ".txt", ".ico"
}

class SiteCrawler:
    """
    Lightweight, fast BFS web crawler to discover internal routes
    and interactive forms for multi-agent full-site auditing.
    """
    @staticmethod
    async def discover_pages(
        base_url: str,
        max_pages: int = 15,
        max_depth: int = 2,
        timeout_ms: int = 15000
    ) -> List[Dict[str, Any]]:
        parsed_base = urlparse(base_url)
        base_origin = f"{parsed_base.scheme}://{parsed_base.netloc}".lower()

        visited: Set[str] = set()
        discovered: List[Dict[str, Any]] = []
        queue: List[tuple[str, int]] = [(base_url, 0)]

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 BlackboxCrawler/2.0"
            )
            page = await context.new_page()

            while queue and len(discovered) < max_pages:
                current_url, depth = queue.pop(0)

                # Normalize URL
                clean_url = current_url.split("#")[0].rstrip("/")
                if clean_url in visited:
                    continue
                visited.add(clean_url)

                try:
                    resp = await page.goto(clean_url, wait_until="domcontentloaded", timeout=timeout_ms)
                    status_code = resp.status if resp else 200

                    title = await page.title()
                    # Check if page has forms or interactive inputs
                    has_form = await page.evaluate("() => document.querySelectorAll('form, input, textarea, select').length > 0")

                    discovered.append({
                        "url": clean_url,
                        "title": title or clean_url,
                        "depth": depth,
                        "status": status_code,
                        "has_form": bool(has_form)
                    })

                    # If not reached max depth, extract links
                    if depth < max_depth and len(discovered) + len(queue) < max_pages * 2:
                        hrefs = await page.evaluate("""() => {
                            const links = Array.from(document.querySelectorAll('a[href]'));
                            return links.map(a => a.getAttribute('href')).filter(Boolean);
                        }""")

                        for href in hrefs:
                            href_clean = href.strip()
                            if href_clean.startswith(("#", "javascript:", "mailto:", "tel:")):
                                continue

                            abs_url = urljoin(clean_url, href_clean).split("#")[0].rstrip("/")
                            parsed_target = urlparse(abs_url)
                            target_origin = f"{parsed_target.scheme}://{parsed_target.netloc}".lower()

                            # Only crawl within same origin
                            if target_origin == base_origin:
                                path_lower = parsed_target.path.lower()
                                if not any(path_lower.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
                                    if abs_url not in visited and not any(q[0] == abs_url for q in queue):
                                        queue.append((abs_url, depth + 1))
                except Exception as e:
                    print(f"[SiteCrawler] Error crawling {clean_url}: {e}")
                    discovered.append({
                        "url": clean_url,
                        "title": "Error / Unreachable",
                        "depth": depth,
                        "status": 500,
                        "has_form": False
                    })

            await context.close()
            await browser.close()

        # If no pages discovered, ensure base URL is at least in list
        if not discovered:
            discovered.append({
                "url": base_url,
                "title": "Home",
                "depth": 0,
                "status": 200,
                "has_form": False
            })

        return discovered
