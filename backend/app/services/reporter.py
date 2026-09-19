import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from jinja2 import Template
from app.config import REPORTS_DIR, BACKEND_URL

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audit Report &mdash; {{ run.id[:8] }}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #09090b;
            --surface: #121215;
            --surface-elevated: #18181b;
            --border: #27272a;
            --border-hover: #3f3f46;
            --text: #fafafa;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            --accent: #3b82f6;
            --accent-soft: rgba(59, 130, 246, 0.12);
            --danger: #ef4444;
            --danger-soft: rgba(239, 68, 68, 0.12);
            --warning: #f59e0b;
            --warning-soft: rgba(245, 158, 11, 0.12);
            --success: #10b981;
            --success-soft: rgba(16, 185, 129, 0.12);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            line-height: 1.5;
            padding: 40px 24px;
            -webkit-font-smoothing: antialiased;
        }

        .container {
            max-width: 1040px;
            margin: 0 auto;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            padding-bottom: 28px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 32px;
        }

        .header-title {
            font-size: 22px;
            font-weight: 600;
            letter-spacing: -0.02em;
            color: var(--text);
            margin-bottom: 6px;
        }

        .header-sub {
            font-size: 13px;
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
        }

        .mode-badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            background: var(--accent-soft);
            color: var(--accent);
            border: 1px solid rgba(59, 130, 246, 0.3);
        }

        .executive-summary {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 32px;
        }

        .summary-label {
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--accent);
            margin-bottom: 10px;
        }

        .summary-text {
            font-size: 14px;
            color: var(--text-secondary);
            line-height: 1.7;
        }

        .scores-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 12px;
            margin-bottom: 32px;
        }

        .score-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
        }

        .score-label {
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .score-val {
            font-size: 26px;
            font-weight: 700;
            letter-spacing: -0.02em;
        }

        .score-val.high { color: var(--success); }
        .score-val.med { color: var(--warning); }
        .score-val.low { color: var(--danger); }

        .section-header {
            font-size: 16px;
            font-weight: 600;
            letter-spacing: -0.01em;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .issue-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 14px;
            transition: border-color 0.15s ease;
        }

        .issue-card:hover {
            border-color: var(--border-hover);
        }

        .issue-top {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 8px;
        }

        .issue-title {
            font-size: 15px;
            font-weight: 600;
            color: var(--text);
        }

        .score-pill {
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
        }

        .pill-critical { background: var(--danger-soft); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.3); }
        .pill-high { background: var(--warning-soft); color: var(--warning); border: 1px solid rgba(245, 158, 11, 0.3); }
        .pill-medium { background: var(--accent-soft); color: var(--accent); border: 1px solid rgba(59, 130, 246, 0.3); }
        .pill-low { background: rgba(161, 161, 170, 0.1); color: var(--text-secondary); border: 1px solid var(--border); }

        .issue-desc {
            font-size: 13px;
            color: var(--text-secondary);
            margin-bottom: 12px;
        }

        .issue-box {
            background: var(--surface-elevated);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 12px 14px;
            margin-top: 10px;
        }

        .box-title {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 4px;
        }

        .box-content {
            font-size: 13px;
            color: var(--text);
        }

        .code-box {
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            color: #93c5fd;
            background: #000000;
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 10px 12px;
            overflow-x: auto;
            margin-top: 6px;
        }

        .timeline-step {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            display: grid;
            grid-template-columns: 80px 1fr 180px;
            gap: 16px;
            align-items: center;
        }

        .step-badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            color: var(--text-muted);
        }

        .step-action {
            font-weight: 600;
            font-size: 14px;
            color: var(--text);
            margin-bottom: 4px;
        }

        .step-reason {
            font-size: 12px;
            color: var(--text-muted);
        }

        .step-thumb {
            width: 180px;
            height: 95px;
            object-fit: cover;
            border-radius: 4px;
            border: 1px solid var(--border);
        }

        footer {
            margin-top: 60px;
            padding-top: 24px;
            border-top: 1px solid var(--border);
            font-size: 12px;
            color: var(--text-muted);
            display: flex;
            justify-content: space-between;
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div>
                <h1 class="header-title">Autonomous UI/UX &amp; Security Audit</h1>
                <div class="header-sub">TARGET: {{ run.target_url }} &bull; RUN: {{ run.id }}</div>
            </div>
            <div>
                <span class="mode-badge">{{ run.mode or 'FOCUSED' }}</span>
            </div>
        </header>

        {% if run.llm_summary %}
        <section class="executive-summary">
            <div class="summary-label">Executive Audit Summary</div>
            <div class="summary-text">{{ run.llm_summary }}</div>
        </section>
        {% endif %}

        <section class="scores-grid">
            <div class="score-card">
                <div class="score-label">Overall Health</div>
                <div class="score-val {% if run.friction_score >= 80 %}high{% elif run.friction_score >= 50 %}med{% else %}low{% endif %}">
                    {{ run.friction_score }}
                </div>
            </div>
            {% if run.category_scores %}
            <div class="score-card">
                <div class="score-label">Accessibility</div>
                <div class="score-val {% if run.category_scores.accessibility >= 80 %}high{% elif run.category_scores.accessibility >= 50 %}med{% else %}low{% endif %}">
                    {{ run.category_scores.accessibility }}
                </div>
            </div>
            <div class="score-card">
                <div class="score-label">UX Friction</div>
                <div class="score-val {% if run.category_scores.friction >= 80 %}high{% elif run.category_scores.friction >= 50 %}med{% else %}low{% endif %}">
                    {{ run.category_scores.friction }}
                </div>
            </div>
            <div class="score-card">
                <div class="score-label">Security</div>
                <div class="score-val {% if run.category_scores.security >= 80 %}high{% elif run.category_scores.security >= 50 %}med{% else %}low{% endif %}">
                    {{ run.category_scores.security }}
                </div>
            </div>
            <div class="score-card">
                <div class="score-label">Broken Links</div>
                <div class="score-val {% if run.category_scores.broken_links >= 80 %}high{% elif run.category_scores.broken_links >= 50 %}med{% else %}low{% endif %}">
                    {{ run.category_scores.broken_links }}
                </div>
            </div>
            <div class="score-card">
                <div class="score-label">Performance</div>
                <div class="score-val {% if run.category_scores.performance >= 80 %}high{% elif run.category_scores.performance >= 50 %}med{% else %}low{% endif %}">
                    {{ run.category_scores.performance }}
                </div>
            </div>
            {% endif %}
        </section>

        <section style="margin-bottom: 40px;">
            <div class="section-header">
                <span>Detected Issues &amp; Dynamic Remediation ({{ issues|length }})</span>
            </div>

            {% for issue in issues %}
            <div class="issue-card">
                <div class="issue-top">
                    <span class="issue-title">{{ issue.title }}</span>
                    <span class="score-pill {% if issue.dynamic_score and issue.dynamic_score >= 8.0 %}pill-critical{% elif issue.dynamic_score and issue.dynamic_score >= 6.0 %}pill-high{% else %}pill-medium{% endif %}">
                        Severity {{ issue.dynamic_score or 5.0 }} &bull; {{ issue.severity }}
                    </span>
                </div>
                <div class="issue-desc">{{ issue.description }}</div>

                {% if issue.impact_summary %}
                <div class="issue-box">
                    <div class="box-title">User / Business Impact</div>
                    <div class="box-content">{{ issue.impact_summary }}</div>
                </div>
                {% endif %}

                {% if issue.fix_suggestion %}
                <div class="issue-box">
                    <div class="box-title">Remediation Suggestion</div>
                    <pre class="code-box"><code>{{ issue.fix_suggestion }}</code></pre>
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </section>

        <section>
            <div class="section-header">
                <span>Execution Timeline &amp; Visual Trace ({{ steps|length }})</span>
            </div>

            {% for step in steps %}
            <div class="timeline-step">
                <div class="step-badge">STEP {{ step.step_number }}</div>
                <div>
                    <div class="step-action">{{ step.action }} &mdash; {{ step.target or 'Browser Event' }}</div>
                    <div class="step-reason">{{ step.reason }}</div>
                </div>
                <div>
                    {% if step.screenshot_path %}
                    <img class="step-thumb" src="{{ step.screenshot_url }}" alt="Step screenshot" loading="lazy" />
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </section>

        <footer>
            <div>Blackbox Autonomous Agent Engine v2.0</div>
            <div>Generated {{ run.completed_at or 'Recently' }}</div>
        </footer>
    </div>
</body>
</html>
"""

class ReporterService:
    @staticmethod
    def generate_rich_report(
        report_data: Dict[str, Any],
        steps_data: List[Dict[str, Any]],
        issues_data: List[Dict[str, Any]],
        paths_data: List[Dict[str, Any]],
        pages_tested: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Generates structured JSON report and sleek minimalist HTML report.
        Returns the relative filepath to the generated HTML report.
        """
        run_id = report_data["id"]
        html_filename = f"run_{run_id}.html"
        json_filename = f"run_{run_id}.json"

        html_filepath = REPORTS_DIR / html_filename
        json_filepath = REPORTS_DIR / json_filename

        # Normalize steps for HTML template
        formatted_steps = []
        for step in steps_data:
            screenshot = step.get("screenshot_path", "")
            screenshot_url = ""
            if screenshot:
                p = Path(screenshot)
                screenshot_url = f"/screenshots/{p.parent.name}/{p.name}"

            formatted_steps.append({
                "step_number": step.get("step_number"),
                "action": step.get("action"),
                "target": step.get("target"),
                "reason": step.get("reason"),
                "url": step.get("url"),
                "duration_ms": step.get("duration_ms", 0.0),
                "screenshot_path": screenshot,
                "screenshot_url": screenshot_url
            })

        # Render HTML
        template = Template(HTML_TEMPLATE)
        rendered_html = template.render(
            run=report_data,
            steps=formatted_steps,
            issues=issues_data,
            paths=paths_data,
            pages=pages_tested or []
        )

        with open(html_filepath, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        # Build structured JSON report payload
        structured_json = {
            "run_id": run_id,
            "goal": report_data.get("goal"),
            "target_url": report_data.get("target_url"),
            "mode": report_data.get("mode", "FOCUSED"),
            "status": report_data.get("status"),
            "scores": {
                "overall": report_data.get("friction_score", 100.0),
                "category_breakdown": report_data.get("category_scores", {})
            },
            "executive_summary": report_data.get("llm_summary"),
            "metrics": {
                "steps_count": len(steps_data),
                "issues_count": len(issues_data),
                "pages_tested_count": len(pages_tested or [])
            },
            "issues": issues_data,
            "improvement_roadmap": sorted(
                issues_data,
                key=lambda x: float(x.get("dynamic_score") or 5.0),
                reverse=True
            ),
            "pages_tested": pages_tested or [],
            "steps": formatted_steps
        }

        with open(json_filepath, "w", encoding="utf-8") as f:
            json.dump(structured_json, f, indent=2)

        return f"/reports/{html_filename}"

    @staticmethod
    def generate_report(
        report_data: Dict[str, Any],
        steps_data: List[Dict[str, Any]],
        issues_data: List[Dict[str, Any]],
        paths_data: List[Dict[str, Any]]
    ) -> str:
        """Backward compatible wrapper."""
        return ReporterService.generate_rich_report(
            report_data=report_data,
            steps_data=steps_data,
            issues_data=issues_data,
            paths_data=paths_data
        )
