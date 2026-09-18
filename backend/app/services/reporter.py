import json
from pathlib import Path
from typing import Dict, Any, List
from jinja2 import Template
from app.config import REPORTS_DIR, BACKEND_URL

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous UI/UX Audit Report - {{ run.id[:8] }}</title>
    <style>
        :root {
            --bg: #0f172a;
            --card-bg: #1e293b;
            --border: #334155;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
            --success: #22c55e;
            --warning: #eab308;
            --danger: #ef4444;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 30px;
        }
        .container {
            max-width: 1100px;
            margin: 0 auto;
        }
        .header {
            border-bottom: 2px solid var(--border);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0 0 10px 0;
            color: var(--accent);
            font-size: 28px;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 9999px;
            font-weight: bold;
            font-size: 14px;
            background-color: rgba(34, 197, 94, 0.2);
            color: var(--success);
            border: 1px solid var(--success);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
        }
        .card .title {
            font-size: 14px;
            color: var(--text-muted);
            margin-bottom: 8px;
        }
        .card .value {
            font-size: 28px;
            font-weight: bold;
        }
        .section-title {
            font-size: 20px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 10px;
            margin-top: 40px;
            margin-bottom: 20px;
            color: var(--accent);
        }
        .finding-card {
            background-color: var(--card-bg);
            border-left: 4px solid var(--accent);
            border: 1px solid var(--border);
            border-left-width: 4px;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 12px;
        }
        .finding-card.severity-HIGH { border-left-color: var(--danger); }
        .finding-card.severity-MEDIUM { border-left-color: var(--warning); }
        .finding-card.severity-LOW { border-left-color: var(--accent); }
        
        .finding-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }
        .finding-title {
            font-weight: bold;
            font-size: 16px;
        }
        .sev-tag {
            font-size: 11px;
            font-weight: bold;
            padding: 2px 8px;
            border-radius: 4px;
            text-transform: uppercase;
        }
        .sev-HIGH { background: rgba(239, 68, 68, 0.2); color: var(--danger); }
        .sev-MEDIUM { background: rgba(234, 179, 8, 0.2); color: var(--warning); }
        .sev-LOW { background: rgba(56, 189, 248, 0.2); color: var(--accent); }

        .trajectory {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .step-row {
            background-color: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            display: flex;
            gap: 20px;
            align-items: flex-start;
        }
        .step-row img {
            width: 240px;
            border-radius: 8px;
            border: 1px solid var(--border);
        }
        .step-meta {
            flex: 1;
        }
        .step-num {
            font-weight: bold;
            color: var(--accent);
            font-size: 14px;
            margin-bottom: 4px;
        }
        .step-action {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .step-reason {
            font-size: 14px;
            color: var(--text-muted);
            margin-bottom: 8px;
        }
        .step-url {
            font-family: monospace;
            font-size: 12px;
            color: #64748b;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Autonomous UI/UX & Accessibility Audit Report</h1>
            <p><strong>Goal:</strong> {{ run.goal }}</p>
            <p><strong>Target App:</strong> <a href="{{ run.target_url }}" style="color:var(--accent);">{{ run.target_url }}</a></p>
            <span class="status-badge">{{ run.status }}</span>
        </div>

        <div class="grid">
            <div class="card">
                <div class="title">Total Steps</div>
                <div class="value">{{ run.steps_count }}</div>
            </div>
            <div class="card">
                <div class="title">Screens Visited</div>
                <div class="value">{{ run.screens_count }}</div>
            </div>
            <div class="card">
                <div class="title">Discovered Paths</div>
                <div class="value">{{ run.paths_count }}</div>
            </div>
            <div class="card">
                <div class="title">Friction Score</div>
                <div class="value" style="color: {% if run.friction_score >= 80 %}var(--success){% elif run.friction_score >= 50 %}var(--warning){% else %}var(--danger){% endif %}">
                    {{ run.friction_score }}/100
                </div>
            </div>
        </div>

        <h2 class="section-title">Discovered Issues & Accessibility Findings</h2>
        {% if issues %}
            {% for issue in issues %}
            <div class="finding-card severity-{{ issue.severity }}">
                <div class="finding-header">
                    <span class="finding-title">[{{ issue.type }}] {{ issue.title }}</span>
                    <span class="sev-tag sev-{{ issue.severity }}">{{ issue.severity }}</span>
                </div>
                <p style="margin: 4px 0; font-size:14px;">{{ issue.description }}</p>
                <div style="font-size:12px; color:var(--text-muted); margin-top:6px;">
                    Step {{ issue.step_number }} | URL: <code>{{ issue.url }}</code>
                </div>
            </div>
            {% endfor %}
        {% else %}
            <p style="color:var(--text-muted);">No critical UX or accessibility issues detected during execution.</p>
        {% endif %}

        <h2 class="section-title">Execution Trajectory & Screenshots</h2>
        <div class="trajectory">
            {% for step in steps %}
            <div class="step-row">
                {% if step.screenshot_url %}
                <img src="{{ step.screenshot_url }}" alt="Step {{ step.step_number }}" />
                {% endif %}
                <div class="step-meta">
                    <div class="step-num">STEP {{ step.step_number }}</div>
                    <div class="step-action">{{ step.action }} {% if step.target %}- {{ step.target }}{% endif %}</div>
                    <div class="step-reason">{{ step.reason }}</div>
                    <div class="step-url">Confidence: {{ "%.2f"|format(step.confidence) }} | {{ step.url }}</div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

class ReporterService:
    @staticmethod
    def generate_report(run_data: Dict[str, Any], steps: List[Dict[str, Any]], issues: List[Dict[str, Any]], paths: List[Dict[str, Any]]) -> str:
        run_id = run_data["id"]
        report_filename = f"run_{run_id}.html"
        report_file_path = REPORTS_DIR / report_filename

        # Process step screenshot URLs for web display
        formatted_steps = []
        for s in steps:
            s_dict = dict(s)
            if s_dict.get("screenshot_path"):
                p = Path(s_dict["screenshot_path"])
                # Relative URL to backend static endpoint
                s_dict["screenshot_url"] = f"{BACKEND_URL}/screenshots/{p.parent.name}/{p.name}"
            else:
                s_dict["screenshot_url"] = None
            formatted_steps.append(s_dict)

        template = Template(HTML_TEMPLATE)
        rendered_html = template.render(
            run=run_data,
            steps=formatted_steps,
            issues=issues,
            paths=paths
        )

        with open(report_file_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        return str(report_file_path)
