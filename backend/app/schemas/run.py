from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class RunCreate(BaseModel):
    goal: Optional[str] = Field(None, example="Search for blue running shoes under $100 and complete guest checkout.")
    target_url: Optional[str] = Field(None, example="http://localhost:3001")
    mode: Optional[str] = Field("FOCUSED", example="FOCUSED") # FOCUSED or FULL_SITE
    model: Optional[str] = Field("qwen3.6:35b", example="qwen3.6:35b")

class RunResponse(BaseModel):
    run_id: str
    status: str
    goal: str
    target_url: str
    mode: str
    model: Optional[str] = "qwen3.6:35b"
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
    duration_ms: Optional[float] = 0.0
    timestamp: datetime

    class Config:
        from_attributes = True

class IssueSchema(BaseModel):
    id: str
    type: str
    category: Optional[str] = "ACCESSIBILITY"
    severity: str
    dynamic_score: Optional[float] = 5.0
    title: str
    description: str
    impact_summary: Optional[str] = None
    fix_suggestion: Optional[str] = None
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
    mode: Optional[str] = "FOCUSED"
    model: Optional[str] = "qwen3.6:35b"
    started_at: datetime
    completed_at: Optional[datetime] = None
    steps_count: int
    screens_count: int
    paths_count: int
    friction_score: float
    category_scores: Optional[Dict[str, Any]] = None
    llm_summary: Optional[str] = None
    sub_runs: Optional[List[Any]] = None
    report_path: Optional[str] = None
    error_message: Optional[str] = None
    steps: List[StepSchema] = []
    issues: List[IssueSchema] = []
    paths: List[PathSchema] = []

    class Config:
        from_attributes = True
