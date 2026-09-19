import sys
import asyncio
import threading
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Run
from app.schemas.run import RunCreate, RunResponse
from app.services.agent import AutonomousAgentService

router = APIRouter(prefix="/api/runs", tags=["agent"])

def _execute_run_thread(run_id: str):
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(AutonomousAgentService.execute_run(run_id))
    except Exception as e:
        print(f"[RunThread] Execution ended with: {e}")
    finally:
        loop.close()

@router.post("", response_model=RunResponse)
async def create_run(payload: RunCreate, db: Session = Depends(get_db)):
    target_url = payload.target_url or "http://localhost:3001"
    
    new_run = Run(
        goal=payload.goal,
        target_url=target_url,
        status="RUNNING"
    )
    db.add(new_run)
    db.commit()
    db.refresh(new_run)

    # Launch autonomous agent task in dedicated thread with Windows Proactor loop
    worker = threading.Thread(target=_execute_run_thread, args=(new_run.id,), daemon=True)
    worker.start()

    return RunResponse(
        run_id=new_run.id,
        status=new_run.status,
        goal=new_run.goal,
        target_url=new_run.target_url,
        started_at=new_run.started_at
    )

@router.post("/{run_id}/stop")
async def stop_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    run.status = "STOPPED"
    db.commit()
    return {"message": "Run stop requested", "run_id": run_id}
