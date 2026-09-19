import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base, engine

def generate_uuid():
    return str(uuid.uuid4())

class Run(Base):
    __tablename__ = "runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    goal = Column(Text, nullable=False)
    target_url = Column(String, nullable=False)
    status = Column(String, default="RUNNING") # RUNNING, COMPLETED, FAILED, STOPPED
    mode = Column(String, default="FOCUSED") # FOCUSED, FULL_SITE
    model = Column(String, default="qwen3.6:35b")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    steps_count = Column(Integer, default=0)
    screens_count = Column(Integer, default=0)
    paths_count = Column(Integer, default=0)
    friction_score = Column(Float, default=100.0)
    category_scores = Column(JSON, nullable=True) # {accessibility: 90, friction: 85, security: 95, performance: 80, broken_links: 100}
    report_path = Column(String, nullable=True)
    llm_summary = Column(Text, nullable=True) # Holistic narrative assessment
    sub_runs = Column(JSON, nullable=True) # List of sub-agent summaries for FULL_SITE mode
    error_message = Column(Text, nullable=True)

    steps = relationship("Step", back_populates="run", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="run", cascade="all, delete-orphan")
    paths = relationship("PathModel", back_populates="run", cascade="all, delete-orphan")

class Step(Base):
    __tablename__ = "steps"

    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("runs.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    action = Column(String, nullable=False) # CLICK, TYPE, SCROLL, BACK, WAIT, FINISH
    target = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    thinking = Column(Text, nullable=True)
    confidence = Column(Float, default=1.0)
    url = Column(String, nullable=False)
    screenshot_path = Column(String, nullable=True)
    state_signature = Column(String, nullable=True)
    duration_ms = Column(Float, default=0.0)
    http_status = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    run = relationship("Run", back_populates="steps")

class Issue(Base):
    __tablename__ = "issues"

    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("runs.id"), nullable=False)
    type = Column(String, nullable=False) # ACCESSIBILITY, FRICTION, SECURITY, PERFORMANCE, BROKEN_LINK
    category = Column(String, default="ACCESSIBILITY") # Grouping category
    severity = Column(String, nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    dynamic_score = Column(Float, default=5.0) # 0.0 to 10.0 impact score assessed by LLM
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    impact_summary = Column(Text, nullable=True) # One-sentence UX/security impact
    fix_suggestion = Column(Text, nullable=True) # Actionable code fix recommendation
    step_number = Column(Integer, nullable=False)
    url = Column(String, nullable=False)
    element_summary = Column(Text, nullable=True)

    run = relationship("Run", back_populates="issues")

class PathModel(Base):
    __tablename__ = "paths"

    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("runs.id"), nullable=False)
    path_number = Column(Integer, nullable=False)
    steps_json = Column(JSON, nullable=False) # list of URLs/titles in route
    destination = Column(String, nullable=False)

    run = relationship("Run", back_populates="paths")

def migrate_db():
    """Ensure newly added columns exist in existing SQLite databases."""
    from sqlalchemy import text
    with engine.connect() as conn:
        run_cols = [
            ("mode", "TEXT DEFAULT 'FOCUSED'"),
            ("model", "TEXT DEFAULT 'qwen3.6:35b'"),
            ("llm_summary", "TEXT"),
            ("sub_runs", "JSON"),
            ("category_scores", "JSON"),
        ]
        for col_name, col_type in run_cols:
            try:
                conn.execute(text(f"ALTER TABLE runs ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception:
                pass

        issue_cols = [
            ("dynamic_score", "REAL DEFAULT 5.0"),
            ("impact_summary", "TEXT"),
            ("fix_suggestion", "TEXT"),
            ("category", "TEXT DEFAULT 'ACCESSIBILITY'"),
        ]
        for col_name, col_type in issue_cols:
            try:
                conn.execute(text(f"ALTER TABLE issues ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception:
                pass

        step_cols = [
            ("duration_ms", "REAL DEFAULT 0.0"),
            ("http_status", "INTEGER"),
        ]
        for col_name, col_type in step_cols:
            try:
                conn.execute(text(f"ALTER TABLE steps ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception:
                pass
