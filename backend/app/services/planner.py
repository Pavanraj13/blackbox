import json
import re
import httpx
from typing import Dict, Any, List, Optional
from app.config import (
    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_PLANNER_MODEL,
    OLLAMA_ANALYZER_MODEL,
    OPENAI_MODEL,
    OPENAI_BASE_URL,
    LLM_TIMEOUT,
    get_openai_api_key
)
from app.security import redact_sensitive

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
   - ONCE TYPED: NEVER type into search again! In subsequent steps, your next action MUST BE CLICK: click on the matching product card, product title, or 'Add to Cart'.
3. If a cookie banner, modal dialog, or popover appears, click 'Accept', 'Agree', or 'Close'.
4. If the goal is fulfilled (order placed, checkout reached, requested info displayed), return FINISH.
5. Return JSON only with "action", "target_index" (integer), and "reason"."""

ISSUE_SCORING_PROMPT = """You are a senior UI/UX & Web Accessibility Auditor.
Evaluate the following detected web defect and provide an expert severity score and practical remediation.

Requirements:
- dynamic_score: Float between 1.0 (minor visual nuisance) and 10.0 (critical blocker, WCAG A/AA violation, security flaw, or checkout barrier).
- severity: Exactly one of ["LOW", "MEDIUM", "HIGH", "CRITICAL"].
- impact: 1-2 concise sentences explaining the exact user, accessibility, or business impact.
- fix: Concrete, copy-pasteable HTML/CSS/JS code snippet or specific remediation advice for frontend engineers.

Respond STRICTLY in JSON format:
{
  "dynamic_score": 7.5,
  "severity": "HIGH",
  "impact": "...",
  "fix": "..."
}"""

EXECUTIVE_SUMMARY_PROMPT = """You are an executive digital product auditor.
Analyze the following test session results for an autonomous web audit and generate a concise, professional 2-3 paragraph executive summary covering:
1. Overall state of the web application and goal completion outcome.
2. Major UX friction points, accessibility compliance, or potential security/performance risks found.
3. Top 3 prioritized engineering recommendations for the team.
Do not use emojis. Write in professional, clear, direct language."""


class PlannerService:
    @staticmethod
    async def decide_next_action(
        goal: str,
        observation: Dict[str, Any],
        previous_steps: List[Dict[str, Any]],
        visited_states: List[str],
        model: Optional[str] = None,
        failed_targets: Optional[set] = None
    ) -> Dict[str, Any]:

        provider = LLM_PROVIDER.lower().strip()
        openai_key = get_openai_api_key()

        # 1. Try Ollama if configured or if no OpenAI key is set
        if provider == "ollama" or not openai_key:
            try:
                decision = await PlannerService._query_ollama(goal, observation, previous_steps, visited_states, model=model)
                if PlannerService._validate_decision(decision, observation, previous_steps, failed_targets=failed_targets):
                    return decision
            except Exception as e:
                print(f"[PlannerService] Ollama query failed ({e}). Attempting alternative / fallback...")

        # 2. Try OpenAI if key is present and provider is openai or fallback
        if openai_key:
            try:
                decision = await PlannerService._query_openai(goal, observation, previous_steps, visited_states, openai_key)
                if PlannerService._validate_decision(decision, observation, previous_steps, failed_targets=failed_targets):
                    return decision
            except Exception as e:
                print(f"[PlannerService] OpenAI query failed ({e}). Falling back to generalized semantic planner.")

        # 3. Fallback to domain-agnostic generalized semantic planner
        return PlannerService._generalized_fallback_planner(goal, observation, previous_steps, visited_states, failed_targets=failed_targets)

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

            # Redact sensitive data from visible element texts
            name = redact_sensitive(name)

            meta_tags = []
            if el.get("is_primary_action"):
                meta_tags.append("[PRIMARY ACTION]")
            if el.get("is_external"):
                meta_tags.append("[EXTERNAL LINK]")
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

        clean_goal = redact_sensitive(goal)
        clean_text = redact_sensitive(observation.get("visible_text", "")[:350])

        return json.dumps({
            "goal": clean_goal,
            "current_url": observation.get("url"),
            "page_title": observation.get("title"),
            "is_product_page": is_product,
            "page_text_summary": clean_text,
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
        visited_states: List[str],
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        user_content = PlannerService._build_observation_prompt(goal, observation, previous_steps)
        effective_model = model or OLLAMA_PLANNER_MODEL or OLLAMA_MODEL

        payload = {
            "model": effective_model,
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
    def _validate_decision(
        decision: Dict[str, Any],
        observation: Dict[str, Any],
        previous_steps: Optional[List[Dict[str, Any]]] = None,
        failed_targets: Optional[set] = None
    ) -> bool:
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

            chosen_elem = elements[idx]
            chosen_name = (chosen_elem.get("accessible_name") or chosen_elem.get("text") or "").strip().lower()

            # Disallow choosing blacklisted failed/unreachable targets
            if chosen_elem.get("is_failed") or (failed_targets and chosen_name in failed_targets):
                return False

            # Anti-repetition guardrails:
            if previous_steps:
                last_step = previous_steps[-1]
                last_action = last_step.get("action")
                last_target = (last_step.get("target") or "").strip().lower()

                # 1. Disallow back-to-back TYPE
                if action == "TYPE" and last_action == "TYPE":
                    return False

                # 2. Disallow back-to-back duplicate CLICK on same element when state is unchanged
                if action == "CLICK" and last_action == "CLICK" and chosen_name and chosen_name == last_target:
                    prev_sig = last_step.get("state_signature")
                    curr_sig = observation.get("state_signature")
                    if prev_sig and curr_sig and prev_sig == curr_sig:
                        return False

        return True

    @staticmethod
    async def score_issue(
        issue_title: str,
        issue_description: str,
        element_summary: Optional[str] = None,
        page_url: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dynamically evaluates an issue using LLM to calculate severity score (1-10),
        impact summary, and concrete code remediation.
        """
        # Clean sensitive data
        clean_title = redact_sensitive(issue_title)
        clean_desc = redact_sensitive(issue_description)
        clean_elem = redact_sensitive(element_summary or "N/A")

        prompt = f"""Detected Issue:
- Title: {clean_title}
- Description: {clean_desc}
- Element / Selector: {clean_elem}
- URL: {page_url or 'N/A'}"""

        effective_model = model or OLLAMA_ANALYZER_MODEL or OLLAMA_MODEL
        openai_key = get_openai_api_key()

        # Try LLM Scoring
        if LLM_PROVIDER.lower().strip() == "ollama" or not openai_key:
            try:
                payload = {
                    "model": effective_model,
                    "messages": [
                        {"role": "system", "content": ISSUE_SCORING_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "format": "json",
                    "stream": False,
                    "think": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 350
                    }
                }
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    content = data.get("message", {}).get("content", "")
                    parsed, _ = PlannerService._extract_json_and_thinking(content)
                    if "dynamic_score" in parsed:
                        score = float(parsed["dynamic_score"])
                        score = max(1.0, min(10.0, score))
                        return {
                            "dynamic_score": round(score, 1),
                            "severity": parsed.get("severity", "MEDIUM").upper(),
                            "impact_summary": parsed.get("impact", "").strip(),
                            "fix_suggestion": parsed.get("fix", "").strip()
                        }
            except Exception as e:
                print(f"[PlannerService] LLM issue scoring failed ({e}). Using deterministic rubric.")

        # Deterministic Fallback Rubric
        title_lower = clean_title.lower()
        score = 5.0
        severity = "MEDIUM"
        impact = "Affects user experience or accessibility for assistive technology users."
        fix = "Ensure standard HTML5 semantics and ARIA attributes are configured correctly."

        if "missing label" in title_lower or "unlabeled" in title_lower:
            score = 7.5
            severity = "HIGH"
            impact = "Screen readers cannot announce this interactive control, preventing blind users from operating it."
            fix = "Add an aria-label attribute, e.g. <button aria-label='Action Name'> or associate with a <label for='...'>."
        elif "contrast" in title_lower:
            score = 6.0
            severity = "MEDIUM"
            impact = "Low contrast ratio makes text difficult to read for users with low vision or in bright lighting."
            fix = "Increase color contrast to meet WCAG AA minimum 4.5:1 ratio against the background."
        elif "touch target" in title_lower or "small" in title_lower:
            score = 5.5
            severity = "MEDIUM"
            impact = "Small interactive target (<44x44px) causes misclicks and friction on touchscreens and mobile devices."
            fix = "Add min-width: 44px; min-height: 44px or expand padding to satisfy WCAG 2.5.5 target size."
        elif "broken" in title_lower or "404" in title_lower or "500" in title_lower:
            score = 9.0
            severity = "CRITICAL"
            impact = "Users encounter a dead end or server failure when trying to view requested content."
            fix = "Fix routing configuration or update the hyperlink to point to a valid active endpoint."
        elif "security" in title_lower or "insecure" in title_lower:
            score = 8.5
            severity = "CRITICAL"
            impact = "Transmitting form data or passwords over unencrypted HTTP exposes credentials to interception."
            fix = "Ensure all form actions point to https:// endpoints and apply secure transmission policies."

        return {
            "dynamic_score": score,
            "severity": severity,
            "impact_summary": impact,
            "fix_suggestion": fix
        }

    @staticmethod
    async def generate_executive_summary(
        goal: str,
        target_url: str,
        steps_count: int,
        issues: List[Dict[str, Any]],
        friction_score: float
    ) -> str:
        """Generate a high-level executive summary of the entire test run."""
        issues_summary = "\n".join([
            f"- [{i.get('severity', 'MEDIUM')}] {i.get('title')}: {i.get('impact_summary', '')}"
            for i in issues[:10]
        ]) or "No major defects identified."

        prompt = f"""Target URL: {target_url}
Goal: {goal}
Steps Executed: {steps_count}
Overall Friction Score: {round(friction_score, 1)} / 100
Issues Detected:
{issues_summary}"""

        model = OLLAMA_ANALYZER_MODEL or OLLAMA_MODEL
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": EXECUTIVE_SUMMARY_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "think": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 400
                }
            }
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
                summary = data.get("message", {}).get("content", "").strip()
                if summary:
                    # Strip any lingering thinking tags
                    summary = re.sub(r"<think>.*?</think>", "", summary, flags=re.DOTALL).strip()
                    return summary
        except Exception:
            pass

        # Fallback summary
        issue_count = len(issues)
        status_eval = "good condition" if friction_score >= 85 else "moderate friction" if friction_score >= 60 else "significant accessibility and UX hurdles"
        return (
            f"The autonomous testing agent completed an audit of {target_url} across {steps_count} steps. "
            f"The application achieved an overall friction score of {round(friction_score, 1)}/100, indicating {status_eval}. "
            f"A total of {issue_count} issues were detected during the session. "
            "Key recommendations include adding accessible labels to interactive controls, addressing touch target dimensions, and verifying form submission handlers."
        )

    @staticmethod
    def _generalized_fallback_planner(
        goal: str,
        observation: Dict[str, Any],
        previous_steps: List[Dict[str, Any]],
        visited_states: List[str],
        failed_targets: Optional[set] = None
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
        is_search_page = ("/s?" in url or "search" in url or "/s/" in url)
        if is_search_page and last_action != "CLICK":
            for el in elements:
                if not el.get("visible", True) or el.get("role") != "link":
                    continue
                name = (el.get("accessible_name") or el.get("text") or "").lower()
                if any(t in name for t in tokens) and len(name) > 12:
                    return {
                        "action": "CLICK",
                        "target_index": el["index"],
                        "reason": f"Select matching product '{name[:45]}' from search results.",
                        "confidence": 0.95
                    }

        # 6. SEARCH INPUT
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
            if el.get("is_failed"):
                continue
            name = (el.get("accessible_name") or el.get("text") or "").lower().strip()
            if not name:
                continue
            if failed_targets and name in failed_targets:
                continue

            score = 0
            for token in tokens:
                if token in name:
                    score += 2

            if el.get("in_viewport"):
                score += 1

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

        # 10. Click first unvisited prominent visible link or button in viewport
        recent_clicked_targets = {
            (s.get("target") or "").strip().lower()
            for s in previous_steps
            if s.get("action") == "CLICK" and s.get("target")
        }

        for el in elements:
            if el.get("visible", True) and el.get("in_viewport") and el.get("role") in ["button", "link"]:
                if el.get("is_external") or el.get("is_failed"):
                    continue
                name = (el.get("accessible_name") or el.get("text") or "").strip()
                name_lower = name.lower()
                if failed_targets and name_lower in failed_targets:
                    continue
                if name and len(name) > 3 and name_lower not in recent_clicked_targets:
                    return {
                        "action": "CLICK",
                        "target_index": el["index"],
                        "reason": f"Explore promising navigation element '{name}'.",
                        "confidence": 0.70
                    }

        # 11. If all visible candidates have been clicked, scroll down to reveal new content
        last_action = previous_steps[-1].get("action") if previous_steps else None
        if last_action != "SCROLL":
            return {
                "action": "SCROLL",
                "direction": "down",
                "amount": 700,
                "reason": "Scroll down to reveal unexplored elements on page.",
                "confidence": 0.75
            }

        # 12. If already scrolled and no new interactive elements, conclude gracefully
        return {
            "action": "FINISH",
            "reason": "All available interactive elements have been explored on this page.",
            "confidence": 0.95
        }
