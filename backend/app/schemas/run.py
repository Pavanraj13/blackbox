from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class RunCreate(BaseModel):
    goal: str = Field(..., example="Search for blue running shoes under $100 and complete guest checkout.")
    target_url: Optional[str] = Field(None, example="http://localhost:3001")

class RunResponse(BaseModel):
    run_id: str
    status: str
    goal: str
    target_url: str
    started_at: datetime

    class Config:
        from_attributes = True

class StepSchema(BaseModel):
    id: str
    step_number: int
    action: str
    target: Optional[str] = None
    reason: Optional[str] = None
    thinking: Optional[str] = None
    confidence: float
    url: str
    screenshot_path: Optional[str] = None
    state_signature: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class IssueSchema(BaseModel):
    id: str
    type: str
    severity: str
    title: str
    description: str
    step_number: int
    url: str
    element_summary: Optional[str] = None

    class Config:
        from_attributes = True

class PathSchema(BaseModel):
    id: str
    path_number: int
    steps_json: List[Any]
    destination: str

    class Config:
        from_attributes = True

class RunDetailResponse(BaseModel):
    id: str
    goal: str
    target_url: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    steps_count: int
    screens_count: int
    paths_count: int
    friction_score: float
    report_path: Optional[str] = None
    error_message: Optional[str] = None
    steps: List[StepSchema] = []
    issues: List[IssueSchema] = []
    paths: List[PathSchema] = []

    class Config:
        from_attributes = True
