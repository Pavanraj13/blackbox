import hashlib
from typing import Dict, Any, List
from playwright.async_api import Page

class ObserverService:
    @staticmethod
    async def observe_page(page: Page) -> Dict[str, Any]:
        url = page.url
        title = await page.title()

        # JS script to inspect visible interactive elements semantically
        inspection_js = """
        () => {
            const elements = [];
            const interactiveSelectors = 'a, button, input, select, textarea, [role="button"], [role="link"], [role="searchbox"]';
            const nodes = Array.from(document.querySelectorAll(interactiveSelectors));

            function isElementVisible(el) {
                if (!el) return false;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            }

            function getAccessibleName(el) {
                // Check aria-label, aria-labelledby, label element, or inner text/placeholder
                if (el.getAttribute('aria-label')) return el.getAttribute('aria-label').trim();

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
                return tag;
            }

            function buildCSSSelector(el) {
                if (el.id) return `#${CSS.escape(el.id)}`;
                const tag = el.tagName.toLowerCase();
                if (el.getAttribute('name')) return `${tag}[name="${CSS.escape(el.getAttribute('name'))}"]`;
                if (el.getAttribute('type')) return `${tag}[type="${CSS.escape(el.getAttribute('type'))}"]`;

                // Global index among all matching tag elements in document
                const allSameTag = Array.from(document.querySelectorAll(tag));
                if (allSameTag.length > 1) {
                    const globalIndex = allSameTag.indexOf(el) + 1;
                    return `${tag}:nth-of-type(${globalIndex})`;
                }
                return tag;
            }

            nodes.forEach((el) => {
                const rect = el.getBoundingClientRect();
                const visible = isElementVisible(el);
                const accName = getAccessibleName(el);
                const role = getRole(el);
                const tag = el.tagName.toLowerCase();

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
                    hasLabel = true; // non-inputs don't need input labels
                }

                elements.push({
                    tag: tag,
                    role: role,
                    text: (el.innerText || el.value || "").trim().slice(0, 80),
                    accessible_name: accName,
                    visible: visible,
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

            const bodyText = (document.body ? document.body.innerText : "").slice(0, 1500);

            return {
                elements: elements,
                visible_text: bodyText
            };
        }
        """

        raw_obs = await page.evaluate(inspection_js)

        # Filter elements & assign target indices
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
