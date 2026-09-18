import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Run

router = APIRouter(prefix="/api/runs", tags=["reports"])

@router.get("/{run_id}/report")
def get_run_report(run_id: str, db: Session = Depends(get_db)):
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if not run.report_path or not os.path.exists(run.report_path):
        raise HTTPException(status_code=404, detail="Audit report not generated yet")

    return FileResponse(
        run.report_path,
        media_type="text/html",
        filename=f"audit_report_{run_id[:8]}.html"
    )
