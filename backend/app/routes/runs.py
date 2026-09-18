from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Run, Step, Issue, PathModel
from app.schemas.run import RunDetailResponse, StepSchema, IssueSchema

router = APIRouter(prefix="/api/runs", tags=["runs"])

@router.get("", response_model=List[RunDetailResponse])
def list_runs(db: Session = Depends(get_db)):
    runs = db.query(Run).order_by(Run.started_at.desc()).all()
    return runs

@router.get("/{run_id}", response_model=RunDetailResponse)
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@router.get("/{run_id}/steps", response_model=List[StepSchema])
def get_run_steps(run_id: str, db: Session = Depends(get_db)):
    steps = db.query(Step).filter(Step.run_id == run_id).order_by(Step.step_number.asc()).all()
    return steps

@router.get("/{run_id}/issues", response_model=List[IssueSchema])
def get_run_issues(run_id: str, db: Session = Depends(get_db)):
    issues = db.query(Issue).filter(Issue.run_id == run_id).order_by(Issue.step_number.asc()).all()
    return issues
