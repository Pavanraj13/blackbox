from typing import Dict, Any, List

class FrictionAnalyzer:
    @staticmethod
    def analyze_step(
        observation: Dict[str, Any],
        step_number: int,
        action_data: Dict[str, Any],
        visited_signatures: List[str],
        previous_actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        issues = []
        url = observation.get("url", "")
        sig = observation.get("state_signature", "")
        action_type = action_data.get("action", "").upper()

        # 1. Navigation loop / repeated state detection
        if visited_signatures.count(sig) >= 2:
            issues.append({
                "type": "FRICTION",
                "category": "FRICTION",
                "severity": "HIGH",
                "title": "Navigation loop detected",
                "description": f"The agent re-visited state '{sig}' multiple times at step {step_number}, indicating potential user confusion or a circular flow.",
                "step_number": step_number,
                "url": url,
                "element_summary": f"Repeated State Signature: {sig}"
            })

        # 2. Backtracking detection
        if action_type == "BACK":
            back_count = sum(1 for a in previous_actions if a.get("action") == "BACK") + 1
            if back_count >= 2:
                issues.append({
                    "type": "FRICTION",
                    "category": "FRICTION",
                    "severity": "MEDIUM",
                    "title": "Navigation backtracking",
                    "description": f"Agent was forced to execute BACK action {back_count} times, indicating non-intuitive page hierarchy.",
                    "step_number": step_number,
                    "url": url,
                    "element_summary": "Action: BACK"
                })

        # 3. Excessive scrolling
        if action_type == "SCROLL":
            scroll_count = sum(1 for a in previous_actions if a.get("action") == "SCROLL") + 1
            if scroll_count >= 3:
                issues.append({
                    "type": "FRICTION",
                    "category": "FRICTION",
                    "severity": "LOW",
                    "title": "Excessive page scrolling required",
                    "description": f"Agent scrolled {scroll_count} times to discover actionable controls below the initial viewport fold.",
                    "step_number": step_number,
                    "url": url,
                    "element_summary": f"Direction: {action_data.get('direction', 'down')}"
                })

        # 4. Off-screen interactive controls
        elements = observation.get("elements", [])
        for el in elements:
            if el.get("visible", True) and el.get("role") in ["button", "link"]:
                if el.get("y", 0) > 850:
                    name = (el.get("accessible_name") or el.get("text") or "").lower()
                    if "checkout" in name or "add to cart" in name or "clearance" in name:
                        issues.append({
                            "type": "FRICTION",
                            "category": "FRICTION",
                            "severity": "LOW",
                            "title": "Key interactive control below viewport fold",
                            "description": f"Key control '{el.get('accessible_name')}' is positioned at y={el.get('y')}px, requiring page scroll to interact.",
                            "step_number": step_number,
                            "url": url,
                            "element_summary": f"<{el.get('tag')} y='{el.get('y')}'>{el.get('accessible_name')}</{el.get('tag')}>"
                        })
                        break

        return issues

    @staticmethod
    def calculate_friction_score(issues: List[Dict[str, Any]], steps_count: int = 0) -> Dict[str, Any]:
        """
        Calculates dynamic health scores for overall site and per-category breakdowns
        (Accessibility, Friction, Security, Performance, Broken Links).
        Uses LLM dynamic_score (1-10) for proportional impact deduction.
        """
        # Category base scores
        categories = {
            "ACCESSIBILITY": 100.0,
            "FRICTION": 100.0,
            "SECURITY": 100.0,
            "PERFORMANCE": 100.0,
            "BROKEN_LINK": 100.0,
        }

        for issue in issues:
            cat = (issue.get("category") or issue.get("type") or "ACCESSIBILITY").upper()
            if cat not in categories:
                cat = "ACCESSIBILITY"

            # Dynamic impact rating from LLM (1.0 to 10.0)
            dyn_score = issue.get("dynamic_score")
            if dyn_score is None:
                sev = issue.get("severity", "MEDIUM").upper()
                dyn_score = 8.5 if sev in ("HIGH", "CRITICAL") else 5.0 if sev == "MEDIUM" else 2.5
            else:
                dyn_score = float(dyn_score)

            # Weight deduction by severity rating
            deduction = dyn_score * 1.5
            categories[cat] = max(0.0, categories[cat] - deduction)

        # Apply minor step efficiency penalty if steps > 12 in focused run
        if steps_count > 12:
            efficiency_penalty = min(15.0, (steps_count - 12) * 1.5)
            categories["FRICTION"] = max(0.0, categories["FRICTION"] - efficiency_penalty)

        # Round category scores
        category_scores = {
            "accessibility": round(categories["ACCESSIBILITY"], 1),
            "friction": round(categories["FRICTION"], 1),
            "security": round(categories["SECURITY"], 1),
            "performance": round(categories["PERFORMANCE"], 1),
            "broken_links": round(categories["BROKEN_LINK"], 1),
        }

        # Weighted overall composite score
        # 30% Accessibility, 25% Friction, 20% Security, 15% Broken Links, 10% Performance
        overall = (
            category_scores["accessibility"] * 0.30 +
            category_scores["friction"] * 0.25 +
            category_scores["security"] * 0.20 +
            category_scores["broken_links"] * 0.15 +
            category_scores["performance"] * 0.10
        )
        overall = round(max(0.0, min(100.0, overall)), 1)

        if overall >= 85:
            level = "Optimal"
        elif overall >= 70:
            level = "Moderate Friction"
        elif overall >= 50:
            level = "High Friction"
        else:
            level = "Critical Issues"

        return {
            "score": overall,
            "level": level,
            "category_scores": category_scores
        }
