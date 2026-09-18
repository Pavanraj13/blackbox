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
                if el.get("y", 0) > 850: # Below initial 1280x800 viewport
                    # Only log if it's a primary CTA
                    name = (el.get("accessible_name") or el.get("text") or "").lower()
                    if "checkout" in name or "add to cart" in name or "clearance" in name:
                        issues.append({
                            "type": "FRICTION",
                            "severity": "LOW",
                            "title": "Key interactive control below viewport fold",
                            "description": f"Key control '{el.get('accessible_name')}' is positioned at y={el.get('y')}px, requiring page scroll to interact.",
                            "step_number": step_number,
                            "url": url,
                            "element_summary": f"<{el.get('tag')} y='{el.get('y')}'>{el.get('accessible_name')}</{el.get('tag')}>"
                        })
                        break # Limit to 1 per step

        return issues

    @staticmethod
    def calculate_friction_score(issues: List[Dict[str, Any]], steps_count: int) -> Dict[str, Any]:
        score = 100.0

        for issue in issues:
            severity = issue.get("severity", "LOW")
            issue_type = issue.get("type", "")

            if issue_type == "FRICTION":
                if severity == "HIGH":
                    score -= 15.0
                elif severity == "MEDIUM":
                    score -= 10.0
                else:
                    score -= 5.0
            elif issue_type == "ACCESSIBILITY":
                if severity == "HIGH":
                    score -= 10.0
                else:
                    score -= 5.0

        # Step count penalty if steps > 10
        if steps_count > 10:
            penalty = (steps_count - 10) * 2.0
            score -= penalty

        score = max(0.0, min(100.0, score))
        score = round(score, 1)

        if score >= 80:
            level = "Low Friction"
        elif score >= 50:
            level = "Moderate Friction"
        else:
            level = "High Friction"

        return {
            "score": score,
            "level": level
        }
