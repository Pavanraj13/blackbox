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
                '[onclick]', '[tabindex="0"]', 'summary'
            ].join(', ');

            // Find all semantic interactive nodes
            const rawNodes = Array.from(document.querySelectorAll(interactiveSelectors));
            
            // Also include clickable styled divs/spans on modern SPAs
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
                if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 3 && rect.height > 3;
            }

            function getAccessibleName(el) {
                if (el.getAttribute('aria-label')) return el.getAttribute('aria-label').trim();
                if (el.getAttribute('aria-labelledby')) {
                    const ref = document.getElementById(el.getAttribute('aria-labelledby'));
                    if (ref && ref.innerText.trim()) return ref.innerText.trim();
                }

                if (el.id) {
                    const labelEl = document.querySelector(`label[for="${el.id}"]`);
                    if (labelEl && labelEl.innerText.trim()) return labelEl.innerText.trim();
                }
                const parentLabel = el.closest('label');
                if (parentLabel && parentLabel.innerText.trim()) return parentLabel.innerText.trim();

                if (el.innerText && el.innerText.trim()) return el.innerText.trim();
                if (el.value && el.value.trim()) return el.value.trim();
                if (el.placeholder && el.placeholder.trim()) return el.placeholder.trim();
                if (el.title && el.title.trim()) return el.title.trim();
                if (el.alt && el.alt.trim()) return el.alt.trim();
                
                return "";
            }

            function getRole(el) {
                if (el.getAttribute('role')) return el.getAttribute('role');
                const tag = el.tagName.toLowerCase();
                if (tag === 'button') return 'button';
                if (tag === 'a') return 'link';
                if (tag === 'input') return el.type || 'input';
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

                // Prevent duplicates at exact same visual coordinate and text
                const dedupeKey = `${tag}_${Math.round(rect.left)}_${Math.round(rect.top)}_${accName.slice(0, 20)}`;
                if (seenKeys.has(dedupeKey)) return;
                seenKeys.add(dedupeKey);

                // Determine if form input has dedicated label
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

                const inViewport = rect.top >= 0 && rect.top <= viewportHeight;

                elements.push({
                    tag: tag,
                    role: role,
                    text: (el.innerText || el.value || "").trim().slice(0, 80),
                    accessible_name: accName.slice(0, 80),
                    visible: true,
                    in_viewport: inViewport,
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

            // Sort elements by reading order: top-to-bottom, then left-to-right
            elements.sort((a, b) => {
                if (Math.abs(a.y - b.y) > 20) return a.y - b.y;
                return a.x - b.x;
            });

            const bodyText = (document.body ? document.body.innerText : "").slice(0, 2000);

            return {
                elements: elements,
                visible_text: bodyText
            };
        }
        """

        raw_obs = await page.evaluate(inspection_js)

        # Assign indices sequentially
        elements_list = []
        for idx, el in enumerate(raw_obs.get("elements", [])):
            el["index"] = idx
            elements_list.append(el)

        # Calculate state signature hash
        state_str = f"{url}|{title}|" + "|".join([f"{e['role']}:{e['accessible_name']}" for e in elements_list[:15]])
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
