import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Run(Base):
    __tablename__ = "runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    goal = Column(Text, nullable=False)
    target_url = Column(String, nullable=False)
    status = Column(String, default="RUNNING") # RUNNING, COMPLETED, FAILED, STOPPED
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    steps_count = Column(Integer, default=0)
    screens_count = Column(Integer, default=0)
    paths_count = Column(Integer, default=0)
    friction_score = Column(Float, default=100.0)
    report_path = Column(String, nullable=True)
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
    timestamp = Column(DateTime, default=datetime.utcnow)

    run = relationship("Run", back_populates="steps")

class Issue(Base):
    __tablename__ = "issues"

    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("runs.id"), nullable=False)
    type = Column(String, nullable=False) # ACCESSIBILITY, FRICTION
    severity = Column(String, nullable=False) # LOW, MEDIUM, HIGH
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
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
