import hashlib
from typing import Dict, Any, List
from playwright.async_api import Page

class ObserverService:
    @staticmethod
    async def observe_page(page: Page) -> Dict[str, Any]:
        url = page.url
        title = await page.title()

        # JS script to inspect visible interactive elements semantically across arbitrary modern websites
        inspection_js = """
        () => {
            const elements = [];
            const interactiveSelectors = [
                'a', 'button', 'input', 'select', 'textarea',
                '[role="button"]', '[role="link"]', '[role="searchbox"]',
                '[role="tab"]', '[role="menuitem"]', '[role="option"]',
                '[role="combobox"]', '[role="checkbox"]', '[role="radio"]',
                '[onclick]', '[tabindex="0"]', 'summary',
                '.a-button', '[id*="buy-now"]', '[id*="add-to-cart"]'
            ].join(', ');

            // Find all semantic interactive nodes
            const rawNodes = Array.from(document.querySelectorAll(interactiveSelectors));
            
            // Also inspect clickable styled divs/spans on modern SPAs
            const allElements = Array.from(document.querySelectorAll('div, span, li, p'));
            for (let i = 0; i < Math.min(allElements.length, 300); i++) {
                const el = allElements[i];
                if (el.getAttribute('onclick') || (window.getComputedStyle(el).cursor === 'pointer' && el.children.length === 0 && (el.innerText || '').trim().length > 0)) {
                    if (!rawNodes.includes(el)) {
                        rawNodes.push(el);
                    }
                }
            }

            function isElementVisible(el) {
                if (!el) return false;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') return false;
                // Permit transparent button overlay inputs like Amazon's a-button-input
                const elId = (el.id || '').toLowerCase();
                const isOverlayButton = elId.includes('buy') || elId.includes('cart') || elId.includes('btn') || elId.includes('button');
                if (style.opacity === '0' && !isOverlayButton) return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 4 && rect.height > 4;
            }

            function getAccessibleName(el) {
                // 1. Check aria-label
                if (el.getAttribute('aria-label') && el.getAttribute('aria-label').trim()) {
                    return el.getAttribute('aria-label').trim();
                }

                // 2. Check aria-labelledby
                if (el.getAttribute('aria-labelledby')) {
                    const ref = document.getElementById(el.getAttribute('aria-labelledby'));
                    if (ref && ref.innerText.trim()) return ref.innerText.trim();
                }

                // 3. For input buttons / submit inputs / inputs with value
                if (el.value && typeof el.value === 'string' && el.value.trim().length > 0) {
                    const val = el.value.trim();
                    if (val.length < 100 && !val.includes('{') && !val.includes('function')) {
                        return val;
                    }
                }

                // 4. Check associated label
                if (el.id) {
                    const labelEl = document.querySelector(`label[for="${el.id}"]`);
                    if (labelEl && labelEl.innerText.trim()) return labelEl.innerText.trim();
                }
                const parentLabel = el.closest('label');
                if (parentLabel && parentLabel.innerText.trim()) return parentLabel.innerText.trim();

                // 5. Check title attribute
                if (el.title && el.title.trim()) return el.title.trim();

                // 6. Check inner text of headers or strong tags inside links/cards (e.g. Amazon product titles)
                const headingInside = el.querySelector('h1, h2, h3, h4, h5, span.a-size-medium, span.a-text-normal');
                if (headingInside && headingInside.innerText.trim()) {
                    return headingInside.innerText.trim();
                }

                // 7. Direct inner text
                if (el.innerText && el.innerText.trim()) {
                    return el.innerText.trim();
                }

                // 8. Child image with alt text (e.g. product card image link)
                const img = el.querySelector('img[alt]');
                if (img && img.alt && img.alt.trim()) {
                    return img.alt.trim();
                }

                if (el.placeholder && el.placeholder.trim()) return el.placeholder.trim();
                if (el.alt && el.alt.trim()) return el.alt.trim();
                
                return "";
            }

            function getRole(el) {
                if (el.getAttribute('role')) return el.getAttribute('role');
                const tag = el.tagName.toLowerCase();
                if (tag === 'button') return 'button';
                if (tag === 'a') return 'link';
                if (tag === 'input') {
                    const type = (el.type || '').toLowerCase();
                    if (type === 'submit' || type === 'button') return 'button';
                    return type || 'input';
                }
                if (tag === 'select') return 'select';
                if (tag === 'textarea') return 'textarea';
                if (tag === 'summary') return 'button';
                return tag;
            }

            function buildCSSSelector(el) {
                if (el.id) return `#${CSS.escape(el.id)}`;
                if (el.getAttribute('data-testid')) return `[data-testid="${CSS.escape(el.getAttribute('data-testid'))}"]`;
                
                const tag = el.tagName.toLowerCase();
                if (el.getAttribute('name')) return `${tag}[name="${CSS.escape(el.getAttribute('name'))}"]`;
                if (el.getAttribute('type')) return `${tag}[type="${CSS.escape(el.getAttribute('type'))}"]`;
                if (el.getAttribute('aria-label')) return `${tag}[aria-label="${CSS.escape(el.getAttribute('aria-label'))}"]`;

                // Global index among all matching tag elements in document
                const allSameTag = Array.from(document.querySelectorAll(tag));
                if (allSameTag.length > 1) {
                    const globalIndex = allSameTag.indexOf(el) + 1;
                    return `${tag}:nth-of-type(${globalIndex})`;
                }
                return tag;
            }

            const viewportHeight = window.innerHeight || 800;
            const seenKeys = new Set();

            rawNodes.forEach((el) => {
                if (!isElementVisible(el)) return;

                const rect = el.getBoundingClientRect();
                const accName = getAccessibleName(el);
                const role = getRole(el);
                const tag = el.tagName.toLowerCase();

                // Prevent duplicate elements at exact same visual location and name
                const dedupeKey = `${tag}_${Math.round(rect.left)}_${Math.round(rect.top)}_${accName.slice(0, 25)}`;
                if (seenKeys.has(dedupeKey)) return;
                seenKeys.add(dedupeKey);

                let hasLabel = false;
                if (tag === 'input' || tag === 'select' || tag === 'textarea') {
                    if (el.id && document.querySelector(`label[for="${el.id}"]`)) {
                        hasLabel = true;
                    } else if (el.closest('label')) {
                        hasLabel = true;
                    } else if (el.getAttribute('aria-label') || el.getAttribute('aria-labelledby')) {
                        hasLabel = true;
                    }
                } else {
                    hasLabel = true;
                }

                // In-viewport calculation
                const inViewport = (rect.top >= -50 && rect.top <= viewportHeight + 100);

                // Detect primary high-intent action buttons (Buy Now, Add to Cart, Checkout, etc.)
                const nameLower = accName.toLowerCase();
                const elId = (el.id || '').toLowerCase();
                let isPrimaryAction = [
                    'buy now', 'buy with 1-click', 'add to cart', 'proceed to buy',
                    'proceed to checkout', 'place your order', 'place order',
                    'complete purchase', 'pay now'
                ].some(k => nameLower.includes(k) || elId.includes(k.replace(/\s+/g, '-')) || elId.includes(k.replace(/\s+/g, '')));

                if (!isPrimaryAction && (elId.includes('buy-now') || elId.includes('buynow') || elId.includes('add-to-cart') || elId.includes('addtocart'))) {
                    isPrimaryAction = true;
                }

                if (isPrimaryAction && !accName) {
                    if (elId.includes('buy') || nameLower.includes('buy')) accName = 'Buy Now';
                    else if (elId.includes('cart') || nameLower.includes('cart')) accName = 'Add to Cart';
                    else accName = 'Buy Now / Add to Cart';
                }

                elements.push({
                    tag: tag,
                    role: role,
                    text: (el.innerText || el.value || "").trim().slice(0, 90),
                    accessible_name: accName.slice(0, 90),
                    visible: true,
                    in_viewport: inViewport,
                    is_primary_action: isPrimaryAction,
                    x: Math.round(rect.left),
                    y: Math.round(rect.top),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    has_label: hasLabel,
                    input_type: el.type || null,
                    placeholder: el.placeholder || null,
                    disabled: el.disabled || false,
                    selector: buildCSSSelector(el)
                });
            });

            // Sorting logic:
            // 1. Primary action buttons (Buy Now, Add to Cart) first!
            // 2. In-viewport elements in visual reading order (top-to-bottom, left-to-right)
            // 3. Out-of-viewport elements last
            elements.sort((a, b) => {
                if (a.is_primary_action && !b.is_primary_action) return -1;
                if (!a.is_primary_action && b.is_primary_action) return 1;

                if (a.in_viewport && !b.in_viewport) return -1;
                if (!a.in_viewport && b.in_viewport) return 1;

                if (Math.abs(a.y - b.y) > 25) return a.y - b.y;
                return a.x - b.x;
            });

            const bodyText = (document.body ? document.body.innerText : "").slice(0, 2500);

            return {
                elements: elements,
                visible_text: bodyText
            };
        }
        """

        raw_obs = await page.evaluate(inspection_js)

        # Assign indices sequentially based on priority sorted list
        elements_list = []
        for idx, el in enumerate(raw_obs.get("elements", [])):
            el["index"] = idx
            elements_list.append(el)

        # Calculate state signature hash
        state_str = f"{url}|{title}|" + "|".join([f"{e['role']}:{e['accessible_name']}" for e in elements_list[:20]])
        state_sig = hashlib.sha256(state_str.encode('utf-8')).hexdigest()[:16]

        observation = {
            "url": url,
            "title": title,
            "viewport": {"width": 1280, "height": 800},
            "elements": elements_list,
            "visible_text": raw_obs.get("visible_text", ""),
            "state_signature": state_sig
        }

        return observation
