from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Run, Step, Issue, PathModel
from app.schemas.run import RunDetailResponse, StepSchema, IssueSchema
from app.security import cipher

router = APIRouter(prefix="/api/runs", tags=["runs"])

def _format_run(run: Run) -> Run:
    if run and run.report_path and run.report_path.startswith("enc:"):
        run.report_path = cipher.decrypt(run.report_path)
    return run

@router.get("", response_model=List[RunDetailResponse])
def list_runs(db: Session = Depends(get_db)):
    runs = db.query(Run).order_by(Run.started_at.desc()).all()
    return [_format_run(r) for r in runs]

@router.get("/{run_id}", response_model=RunDetailResponse)
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return _format_run(run)

@router.get("/{run_id}/steps", response_model=List[StepSchema])
def get_run_steps(run_id: str, db: Session = Depends(get_db)):
    steps = db.query(Step).filter(Step.run_id == run_id).order_by(Step.step_number.asc()).all()
    return steps

@router.get("/{run_id}/issues", response_model=List[IssueSchema])
def get_run_issues(run_id: str, db: Session = Depends(get_db)):
    issues = db.query(Issue).filter(Issue.run_id == run_id).order_by(Issue.step_number.asc()).all()
    return issues

@router.delete("/{run_id}")
def delete_run(run_id: str, db: Session = Depends(get_db)):
    import shutil
    from app.config import SCREENSHOTS_DIR, REPORTS_DIR

    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    db.query(Issue).filter(Issue.run_id == run_id).delete()
    db.query(Step).filter(Step.run_id == run_id).delete()
    db.query(PathModel).filter(PathModel.run_id == run_id).delete()
    db.query(Run).filter(Run.id == run_id).delete()
    db.commit()

    run_dir = SCREENSHOTS_DIR / f"run_{run_id}"
    if run_dir.exists():
        shutil.rmtree(run_dir, ignore_errors=True)

    (REPORTS_DIR / f"run_{run_id}.html").unlink(missing_ok=True)
    (REPORTS_DIR / f"run_{run_id}.json").unlink(missing_ok=True)

    return {"status": "deleted", "run_id": run_id}

@router.delete("")
def delete_all_runs(db: Session = Depends(get_db)):
    import shutil
    from app.config import SCREENSHOTS_DIR, REPORTS_DIR

    runs = db.query(Run).all()
    count = len(runs)
    db.query(Issue).delete()
    db.query(Step).delete()
    db.query(PathModel).delete()
    db.query(Run).delete()
    db.commit()

    for item in SCREENSHOTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith("run_"):
            shutil.rmtree(item, ignore_errors=True)
    for report_file in REPORTS_DIR.glob("run_*"):
        report_file.unlink(missing_ok=True)

    return {"status": "cleared", "deleted_count": count}

