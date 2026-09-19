import json
import re
import httpx
from typing import Dict, Any, List, Optional
from app.config import (
    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OPENAI_MODEL,
    OPENAI_BASE_URL,
    LLM_TIMEOUT,
    get_openai_api_key
)

SYSTEM_PROMPT = """You are an autonomous black-box web testing and navigation agent.
You are given a high-level user goal and real-time observation of any web page.
The web application is a black box. You have zero source code access and must reason strictly from visible DOM and accessibility elements.

Your goal is to choose the single most logical next action to progress toward the user's objective on ANY website.

Allowed Actions:
1. CLICK:
   {"action": "CLICK", "target_index": <int>, "reason": "...", "confidence": 0.95}
2. TYPE:
   {"action": "TYPE", "target_index": <int>, "text": "...", "reason": "...", "confidence": 0.95}
3. SCROLL:
   {"action": "SCROLL", "direction": "down"|"up", "amount": 600, "reason": "...", "confidence": 0.85}
4. BACK:
   {"action": "BACK", "reason": "...", "confidence": 0.90}
5. WAIT:
   {"action": "WAIT", "reason": "...", "confidence": 0.80}
6. FINISH:
   {"action": "FINISH", "reason": "...", "confidence": 0.99}

Crucial Decision Rules:
1. If the goal mentions "buy", "order", "purchase", or "cart":
   - Once a product page is reached or if 'Buy Now' / 'Add to Cart' is visible (elements tagged [PRIMARY ACTION]), YOUR TOP PRIORITY IS TO CLICK 'Buy Now' or 'Add to Cart'.
   - NEVER click the product title, product image, or re-type in search when you are already viewing the product!
2. When searching:
   - Initial step: TYPE search query into search input.
   - On search results page: CLICK the title link of the relevant product.
   - On product page: CLICK 'Buy Now' or 'Add to Cart'.
3. If a cookie banner, modal dialog, or popover appears, click 'Accept', 'Agree', or 'Close'.
4. If the goal is fulfilled (order placed, checkout reached, requested info displayed), return FINISH.
5. Return JSON only with "action", "target_index" (integer), and "reason"."""

class PlannerService:
    @staticmethod
    async def decide_next_action(
        goal: str,
        observation: Dict[str, Any],
        previous_steps: List[Dict[str, Any]],
        visited_states: List[str]
    ) -> Dict[str, Any]:

        provider = LLM_PROVIDER.lower().strip()
        openai_key = get_openai_api_key()

        # 1. Try Ollama if configured or if no OpenAI key is set
        if provider == "ollama" or not openai_key:
            try:
                decision = await PlannerService._query_ollama(goal, observation, previous_steps, visited_states)
                if PlannerService._validate_decision(decision, observation):
                    return decision
            except Exception as e:
                print(f"[PlannerService] Ollama query failed ({e}). Attempting alternative / fallback...")

        # 2. Try OpenAI if key is present and provider is openai or fallback
        if openai_key:
            try:
                decision = await PlannerService._query_openai(goal, observation, previous_steps, visited_states, openai_key)
                if PlannerService._validate_decision(decision, observation):
                    return decision
            except Exception as e:
                print(f"[PlannerService] OpenAI query failed ({e}). Falling back to generalized semantic planner.")

        # 3. Fallback to domain-agnostic generalized semantic planner
        return PlannerService._generalized_fallback_planner(goal, observation, previous_steps, visited_states)

    @staticmethod
    def _extract_json_and_thinking(raw_text: str) -> tuple[Dict[str, Any], str]:
        """Extracts JSON object and thinking traces from raw model output."""
        thinking = ""
        think_match = re.search(r"<think>(.*?)</think>", raw_text, re.DOTALL | re.IGNORECASE)
        if think_match:
            thinking = think_match.group(1).strip()
            raw_text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL | re.IGNORECASE).strip()

        parsed = None
        try:
            parsed = json.loads(raw_text.strip())
        except Exception:
            pass

        if not parsed:
            fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
            if fenced_match:
                try:
                    parsed = json.loads(fenced_match.group(1).strip())
                except Exception:
                    pass

        if not parsed:
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    parsed = json.loads(raw_text[start:end+1])
                except Exception:
                    pass

        if parsed and isinstance(parsed, dict):
            if "index" in parsed and "target_index" not in parsed:
                try:
                    parsed["target_index"] = int(parsed["index"])
                except Exception:
                    pass
            return parsed, thinking

        raise ValueError(f"Unable to parse valid JSON from text: {raw_text[:200]}")

    @staticmethod
    def _build_observation_prompt(
        goal: str,
        observation: Dict[str, Any],
        previous_steps: List[Dict[str, Any]]
    ) -> str:
        url = (observation.get("url") or "").lower()
        is_product = any(p in url for p in ["/dp/", "/gp/", "/product/", "/item/"])

        compact_elements = []
        for el in observation.get("elements", []):
            name = (el.get("accessible_name") or el.get("text") or el.get("placeholder") or "").strip()
            if not name:
                continue

            meta_tags = []
            if el.get("is_primary_action"):
                meta_tags.append("[PRIMARY ACTION]")
            if el.get("in_viewport"):
                meta_tags.append("[IN VIEWPORT]")
            
            tag_str = " ".join(meta_tags)
            name_with_meta = f"{name[:70]} {tag_str}".strip()

            compact_elements.append({
                "index": el["index"],
                "role": el["role"],
                "name": name_with_meta
            })
            if len(compact_elements) >= 50:
                break

        return json.dumps({
            "goal": goal,
            "current_url": observation.get("url"),
            "page_title": observation.get("title"),
            "is_product_page": is_product,
            "page_text_summary": observation.get("visible_text", "")[:350],
            "observed_interactive_elements": compact_elements,
            "recent_actions": [
                f"Step {s.get('step_number')}: {s.get('action')} {s.get('target', '')}"
                for s in previous_steps[-5:]
            ]
        }, indent=2)

    @staticmethod
    async def _query_ollama(
        goal: str,
        observation: Dict[str, Any],
        previous_steps: List[Dict[str, Any]],
        visited_states: List[str]
    ) -> Dict[str, Any]:
        user_content = PlannerService._build_observation_prompt(goal, observation, previous_steps)

        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Current Web Page Observation:\n{user_content}"}
            ],
            "format": "json",
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 512
            }
        }

        async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            message = data.get("message", {})
            raw_content = message.get("content", "")
            thinking = message.get("thinking", "")

            decision, parsed_thinking = PlannerService._extract_json_and_thinking(raw_content)
            final_thinking = thinking or parsed_thinking
            if final_thinking and "thinking" not in decision:
                decision["thinking"] = final_thinking[:800]

            return decision

    @staticmethod
    async def _query_openai(
        goal: str,
        observation: Dict[str, Any],
        previous_steps: List[Dict[str, Any]],
        visited_states: List[str],
        api_key: str
    ) -> Dict[str, Any]:
        user_content = PlannerService._build_observation_prompt(goal, observation, previous_steps)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Current Web Page Observation:\n{user_content}"}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(f"{OPENAI_BASE_URL}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            result = resp.json()
            content = result["choices"][0]["message"]["content"]
            decision, thinking = PlannerService._extract_json_and_thinking(content)
            if thinking:
                decision["thinking"] = thinking
            return decision

    @staticmethod
    def _validate_decision(decision: Dict[str, Any], observation: Dict[str, Any]) -> bool:
        if not isinstance(decision, dict):
            return False

        if "index" in decision and "target_index" not in decision:
            try:
                decision["target_index"] = int(decision["index"])
            except Exception:
                pass

        action = decision.get("action", "").upper()
        if action not in ["CLICK", "TYPE", "SCROLL", "BACK", "WAIT", "FINISH"]:
            return False

        if action in ["CLICK", "TYPE"]:
            idx = decision.get("target_index")
            if idx is None or not isinstance(idx, int):
                return False
            elements = observation.get("elements", [])
            if idx < 0 or idx >= len(elements):
                return False

        return True

    @staticmethod
    def _generalized_fallback_planner(
        goal: str,
        observation: Dict[str, Any],
        previous_steps: List[Dict[str, Any]],
        visited_states: List[str]
    ) -> Dict[str, Any]:
        """
        Domain-agnostic fallback planner that works dynamically on ANY website,
        with deep handling for E-Commerce flows (Search -> Product -> Buy Now/Cart -> Checkout).
        """
        url = observation.get("url", "").lower()
        title = observation.get("title", "").lower()
        visible_text = observation.get("visible_text", "").lower()
        elements = observation.get("elements", [])
        goal_lower = goal.lower()

        last_step = previous_steps[-1] if previous_steps else {}
        last_action = last_step.get("action")

        # 1. Goal Completion Check
        completion_terms = ["order confirmation", "thank you for your order", "order placed", "confirmed", "receipt"]
        if any(term in visible_text or term in title for term in completion_terms):
            return {
                "action": "FINISH",
                "reason": "Order confirmation / success state detected on page.",
                "confidence": 0.99
            }

        # 2. Cookie / Modal Banner Dismissal Check
        cookie_keywords = ["accept", "agree", "allow all", "accept all cookies", "dismiss", "got it"]
        for el in elements:
            if not el.get("visible", True):
                continue
            name = (el.get("accessible_name") or el.get("text") or "").lower().strip()
            if any(name == ck or name.startswith(ck) for ck in cookie_keywords):
                return {
                    "action": "CLICK",
                    "target_index": el["index"],
                    "reason": f"Dismiss cookie banner or modal dialog ({name}).",
                    "confidence": 0.95
                }

        # 3. Extract semantic keywords from goal
        stop_words = {
            "a", "an", "the", "in", "on", "at", "to", "for", "and", "or", "of", "with",
            "is", "are", "complete", "search", "find", "open", "go", "get", "by", "under", "buy"
        }
        tokens = [w for w in re.findall(r"\b[a-z0-9]+\b", goal_lower) if w not in stop_words and len(w) > 1]
        search_phrase = " ".join(tokens[:4]) if tokens else "products"

        # 4. PRIMARY E-COMMERCE PURCHASE BUTTONS (Buy Now, Add to Cart, Proceed to Buy, Place Order)
        # If user wants to buy/purchase or is on a product page, check for instant purchase buttons
        buy_action_keywords = [
            "buy now", "buy with 1-click", "add to cart", "proceed to buy",
            "proceed to checkout", "place your order", "place order", "complete purchase"
        ]
        if "buy" in goal_lower or "cart" in goal_lower or "/dp/" in url or "/gp/" in url or "product" in url:
            for kw in buy_action_keywords:
                for el in elements:
                    if not el.get("visible", True):
                        continue
                    name = (el.get("accessible_name") or el.get("text") or "").lower()
                    if kw in name:
                        return {
                            "action": "CLICK",
                            "target_index": el["index"],
                            "reason": f"Click primary purchasing button '{name}' to proceed with purchase.",
                            "confidence": 0.98
                        }

        # 5. PRODUCT SELECTION FROM SEARCH RESULTS
        # If on a search results page (e.g. Amazon search), click on the top matching product card
        is_search_page = ("/s?" in url or "search" in url or "/s/" in url)
        if is_search_page and last_action != "CLICK":
            for el in elements:
                if not el.get("visible", True) or el.get("role") != "link":
                    continue
                name = (el.get("accessible_name") or el.get("text") or "").lower()
                # If product link matches any goal tokens and is a descriptive title (>15 chars)
                if any(t in name for t in tokens) and len(name) > 12:
                    return {
                        "action": "CLICK",
                        "target_index": el["index"],
                        "reason": f"Select matching product '{name[:45]}' from search results.",
                        "confidence": 0.95
                    }

        # 6. SEARCH INPUT (if goal asks to search or buy and we haven't typed yet)
        if ("search" in goal_lower or "buy" in goal_lower) and last_action != "TYPE" and not is_search_page:
            for el in elements:
                if el.get("visible", True) and el.get("tag") == "input":
                    inp_type = (el.get("input_type") or "").lower()
                    name = (el.get("accessible_name") or el.get("placeholder") or "").lower()
                    if inp_type in ["search", "text"] and ("search" in name or "query" in name or inp_type == "search"):
                        return {
                            "action": "TYPE",
                            "target_index": el["index"],
                            "text": search_phrase,
                            "reason": f"Type query '{search_phrase}' into search input.",
                            "confidence": 0.94
                        }

        # 7. Form inputs (email, name, phone)
        if last_action != "TYPE":
            for el in elements:
                if el.get("visible", True) and el.get("tag") == "input":
                    inp_type = (el.get("input_type") or "").lower()
                    place = (el.get("placeholder") or "").lower()
                    name = (el.get("accessible_name") or "").lower()

                    if inp_type == "email" or "email" in place or "email" in name:
                        return {
                            "action": "TYPE",
                            "target_index": el["index"],
                            "text": "guest.shopper@example.com",
                            "reason": "Fill email address in required form field.",
                            "confidence": 0.92
                        }

        # 8. Semantic Keyword Matching across all visible interactive elements
        best_candidate = None
        best_score = 0

        for el in elements:
            if not el.get("visible", True) or el.get("role") not in ["button", "link", "searchbox", "tab", "menuitem"]:
                continue
            name = (el.get("accessible_name") or el.get("text") or "").lower()
            if not name:
                continue

            score = 0
            for token in tokens:
                if token in name:
                    score += 2
            
            # Bonus for elements in current viewport
            if el.get("in_viewport"):
                score += 1

            # Penalize recently clicked targets
            recent_targets = [s.get("target", "").lower() for s in previous_steps[-3:]]
            if any(name in rt for rt in recent_targets):
                score -= 3

            if score > best_score:
                best_score = score
                best_candidate = el

        if best_candidate and best_score > 0:
            name = best_candidate.get("accessible_name") or best_candidate.get("text")
            return {
                "action": "CLICK",
                "target_index": best_candidate["index"],
                "reason": f"Click relevant element '{name}' matching goal keywords.",
                "confidence": 0.88
            }

        # 9. Loop prevention: If repeated state detected, scroll down
        if len(visited_states) >= 2 and visited_states[-1] == visited_states[-2]:
            return {
                "action": "SCROLL",
                "direction": "down",
                "amount": 600,
                "reason": "Scroll down to reveal unexplored elements and escape visual loop.",
                "confidence": 0.82
            }

        # 10. Click first prominent visible link or button in viewport
        for el in elements:
            if el.get("visible", True) and el.get("in_viewport") and el.get("role") in ["button", "link"]:
                name = (el.get("accessible_name") or el.get("text") or "").strip()
                if name and len(name) > 3:
                    return {
                        "action": "CLICK",
                        "target_index": el["index"],
                        "reason": f"Explore promising navigation element '{name}'.",
                        "confidence": 0.70
                    }

        # Default fallback
        return {
            "action": "WAIT",
            "reason": "Waiting for web page dynamic components to render.",
            "confidence": 0.50
        }
