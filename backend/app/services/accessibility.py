from typing import Dict, Any, List

class AccessibilityAnalyzer:
    @staticmethod
    def analyze_observation(observation: Dict[str, Any], step_number: int) -> List[Dict[str, Any]]:
        issues = []
        url = observation.get("url", "")
        elements = observation.get("elements", [])

        for el in elements:
            if not el.get("visible", True):
                continue

            role = el.get("role", "")
            tag = el.get("tag", "")
            acc_name = (el.get("accessible_name") or "").strip()
            text = (el.get("text") or "").strip()
            has_label = el.get("has_label", True)
            width = el.get("width", 0)
            height = el.get("height", 0)

            # Check 1: Icon-only or unlabeled interactive button/link
            if role in ["button", "link"] or tag in ["button", "a"]:
                if not acc_name and not text:
                    issues.append({
                        "type": "ACCESSIBILITY",
                        "severity": "HIGH",
                        "title": "Unlabeled interactive control",
                        "description": f"An interactive <{tag}> element (role='{role}') has no accessible name or visible text label. Screen readers cannot describe this control.",
                        "step_number": step_number,
                        "url": url,
                        "element_summary": f"<{tag} role='{role}' selector='{el.get('selector', '')}'>"
                    })

            # Check 2: Form input without accessible label
            if tag in ["input", "select", "textarea"]:
                input_type = el.get("input_type", "")
                if input_type not in ["hidden", "submit", "button", "reset"]:
                    if not has_label or (not acc_name and not el.get("placeholder")):
                        issues.append({
                            "type": "ACCESSIBILITY",
                            "severity": "HIGH" if input_type in ["email", "text", "password"] else "MEDIUM",
                            "title": "Input without accessible label",
                            "description": f"Form field <{tag} type='{input_type}'> is missing an associated <label> tag or aria-label attribute.",
                            "step_number": step_number,
                            "url": url,
                            "element_summary": f"<{tag} type='{input_type}' name='{el.get('selector', '')}' placeholder='{el.get('placeholder', '')}'>"
                        })

            # Check 3: Non-descriptive link label
            if role == "link" or tag == "a":
                if acc_name.lower() in ["click here", "more", "link", "here", "read more"]:
                    issues.append({
                        "type": "ACCESSIBILITY",
                        "severity": "LOW",
                        "title": "Non-descriptive link text",
                        "description": f"Link contains vague label '{acc_name}', which lacks context when navigated by screen readers.",
                        "step_number": step_number,
                        "url": url,
                        "element_summary": f"<a href='...'>{acc_name}</a>"
                    })

            # Check 4: Small touch target (<24x24px)
            if role in ["button", "link"] and (width < 24 or height < 24) and width > 0:
                issues.append({
                    "type": "ACCESSIBILITY",
                    "severity": "LOW",
                    "title": "Small touch target size",
                    "description": f"Interactive element bounding box is only {width}x{height}px, which violates minimum touch target guidelines (24x24px).",
                    "step_number": step_number,
                    "url": url,
                    "element_summary": f"<{tag} width='{width}' height='{height}'>"
                })

        return issues
