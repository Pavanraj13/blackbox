import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from app.config import REPORTS_DIR
from app.database import get_db
from app.models import Run, Issue, Step
from app.security import cipher

router = APIRouter(prefix="/api/runs", tags=["reports"])

def _resolve_report_file(report_path: str) -> Optional[Path]:
    if not report_path:
        return None
    if report_path.startswith("enc:"):
        report_path = cipher.decrypt(report_path)

    # Could be /reports/run_xxx.html or absolute path
    if report_path.startswith("/reports/"):
        filename = report_path.replace("/reports/", "")
        p = REPORTS_DIR / filename
        if p.exists():
            return p

    p = Path(report_path)
    if p.exists():
        return p

    return None

@router.get("/{run_id}/report")
def get_run_report(run_id: str, db: Session = Depends(get_db)):
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    file_path = _resolve_report_file(run.report_path)
    if not file_path:
        # Check standard location by run_id
        std_path = REPORTS_DIR / f"run_{run_id}.html"
        if std_path.exists():
            file_path = std_path
        else:
            raise HTTPException(status_code=404, detail="Audit report not generated yet")

    return FileResponse(
        str(file_path),
        media_type="text/html",
        filename=f"audit_report_{run_id[:8]}.html"
    )

@router.get("/{run_id}/summary")
def get_run_summary(run_id: str, db: Session = Depends(get_db)):
    """Returns structured JSON report for dashboard and extension integration."""
    json_path = REPORTS_DIR / f"run_{run_id}.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Reconstruct summary from DB if JSON file doesn't exist
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    issues = db.query(Issue).filter(Issue.run_id == run_id).all()
    steps = db.query(Step).filter(Step.run_id == run_id).order_by(Step.step_number.asc()).all()

    issues_data = [
        {
            "id": i.id,
            "type": i.type,
            "category": i.category,
            "severity": i.severity,
            "dynamic_score": i.dynamic_score,
            "title": i.title,
            "description": i.description,
            "impact_summary": i.impact_summary,
            "fix_suggestion": i.fix_suggestion,
            "step_number": i.step_number,
            "url": i.url,
            "element_summary": i.element_summary
        }
        for i in issues
    ]

    return {
        "run_id": run.id,
        "goal": run.goal,
        "target_url": run.target_url,
        "mode": run.mode or "FOCUSED",
        "status": run.status,
        "scores": {
            "overall": run.friction_score,
            "category_breakdown": run.category_scores or {}
        },
        "executive_summary": run.llm_summary,
        "metrics": {
            "steps_count": run.steps_count,
            "screens_count": run.screens_count,
            "paths_count": run.paths_count,
            "issues_count": len(issues_data)
        },
        "issues": issues_data,
        "improvement_roadmap": sorted(
            issues_data,
            key=lambda x: float(x.get("dynamic_score") or 5.0),
            reverse=True
        ),
        "steps_count": len(steps)
    }

@router.get("/{run_id}/export")
def export_run_report(run_id: str, format: str = "html", db: Session = Depends(get_db)):
    """Export report as downloadable file attachment."""
    if format.lower() == "json":
        json_path = REPORTS_DIR / f"run_{run_id}.json"
        if json_path.exists():
            return FileResponse(
                str(json_path),
                media_type="application/json",
                filename=f"audit_report_{run_id[:8]}.json"
            )
        raise HTTPException(status_code=404, detail="JSON export not found")

    file_path = _resolve_report_file(None) or (REPORTS_DIR / f"run_{run_id}.html")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(
        str(file_path),
        media_type="application/octet-stream",
        filename=f"blackbox_audit_{run_id[:8]}.html"
    )
