import asyncio
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from app.config import SCREENSHOTS_DIR, TARGET_URL
from app.database import SessionLocal
from app.models import Run, Step, Issue, PathModel
from app.services.browser import BrowserManager
from app.services.observer import ObserverService
from app.services.planner import PlannerService
from app.services.accessibility import AccessibilityAnalyzer
from app.services.friction import FrictionAnalyzer
from app.services.reporter import ReporterService

class AutonomousAgentService:
    @staticmethod
    async def execute_run(run_id: str):
        db = SessionLocal()
        browser = BrowserManager()
        try:
            run = db.query(Run).filter(Run.id == run_id).first()
            if not run:
                print(f"[AutonomousAgent] Run {run_id} not found.")
                return

            run.status = "RUNNING"
            run.started_at = datetime.utcnow()
            db.commit()

            run_screenshot_dir = SCREENSHOTS_DIR / f"run_{run_id}"
            run_screenshot_dir.mkdir(parents=True, exist_ok=True)

            step_number = 0
            max_steps = 30
            visited_states: List[str] = []
            previous_steps_data: List[Dict[str, Any]] = []
            all_issues: List[Dict[str, Any]] = []
            visited_urls: set = set()

            await browser.start(headless=True)
            target = run.target_url or TARGET_URL
            await browser.navigate(target)

            finished = False
            while not finished and step_number < max_steps:
                # Check if run was requested to stop
                db.refresh(run)
                if run.status == "STOPPED":
                    print(f"[AutonomousAgent] Run {run_id} stopped by user.")
                    break

                step_number += 1
                
                # 1. Observe current browser state
                observation = await ObserverService.observe_page(browser.page)
                current_url = observation["url"]
                state_sig = observation["state_signature"]
                visited_states.append(state_sig)
                visited_urls.add(current_url)

                # 2. Accessibility Analysis
                a11y_issues = AccessibilityAnalyzer.analyze_observation(observation, step_number)
                for issue in a11y_issues:
                    # Avoid duplicate titles on same step
                    if not any(i["title"] == issue["title"] and i["step_number"] == step_number for i in all_issues):
                        all_issues.append(issue)
                        db_issue = Issue(
                            run_id=run_id,
                            type=issue["type"],
                            severity=issue["severity"],
                            title=issue["title"],
                            description=issue["description"],
                            step_number=step_number,
                            url=current_url,
                            element_summary=issue.get("element_summary")
                        )
                        db.add(db_issue)

                # 3. Plan next action using LLM / Fallback
                decision = await PlannerService.decide_next_action(
                    goal=run.goal,
                    observation=observation,
                    previous_steps=previous_steps_data,
                    visited_states=visited_states
                )

                action_type = decision.get("action", "WAIT").upper()
                target_idx = decision.get("target_index")
                reason = decision.get("reason", "")
                thinking = decision.get("thinking")
                confidence = float(decision.get("confidence", 0.90))

                # Resolve target element representation
                target_element = None
                target_desc = ""
                elements = observation.get("elements", [])
                if target_idx is not None and 0 <= target_idx < len(elements):
                    target_element = elements[target_idx]
                    target_desc = target_element.get("accessible_name") or target_element.get("text") or f"Element #{target_idx}"

                # 4. Friction Analysis
                friction_issues = FrictionAnalyzer.analyze_step(
                    observation=observation,
                    step_number=step_number,
                    action_data=decision,
                    visited_signatures=visited_states,
                    previous_actions=previous_steps_data
                )
                for issue in friction_issues:
                    all_issues.append(issue)
                    db_issue = Issue(
                        run_id=run_id,
                        type=issue["type"],
                        severity=issue["severity"],
                        title=issue["title"],
                        description=issue["description"],
                        step_number=step_number,
                        url=current_url,
                        element_summary=issue.get("element_summary")
                    )
                    db.add(db_issue)

                # 5. Execute Action
                executed = await browser.execute_action(decision, target_element)

                # 6. Capture Screenshot
                screenshot_filename = f"step_{step_number:03d}.png"
                screenshot_path = run_screenshot_dir / screenshot_filename
                await browser.take_screenshot(str(screenshot_path))

                # 7. Record Step in Database
                db_step = Step(
                    run_id=run_id,
                    step_number=step_number,
                    action=action_type,
                    target=target_desc,
                    reason=reason,
                    thinking=thinking,
                    confidence=confidence,
                    url=current_url,
                    screenshot_path=str(screenshot_path),
                    state_signature=state_sig,
                    timestamp=datetime.utcnow()
                )
                db.add(db_step)
                db.commit()

                step_record = {
                    "step_number": step_number,
                    "action": action_type,
                    "target": target_desc,
                    "reason": reason,
                    "thinking": thinking,
                    "confidence": confidence,
                    "url": current_url,
                    "screenshot_path": str(screenshot_path)
                }
                previous_steps_data.append(step_record)

                if action_type == "FINISH":
                    finished = True
                    break

            # End of loop processing
            run.completed_at = datetime.utcnow()
            run.steps_count = step_number
            run.screens_count = len(visited_urls)
            run.status = "COMPLETED" if finished else "STOPPED"

            # Record path discovery
            path_record = PathModel(
                run_id=run_id,
                path_number=1,
                steps_json=list(visited_urls),
                destination=current_url
            )
            db.add(path_record)
            run.paths_count = 1

            # Calculate Friction Score
            friction_result = FrictionAnalyzer.calculate_friction_score(all_issues, step_number)
            run.friction_score = friction_result["score"]

            db.commit()

            # Build Report
            report_data = {
                "id": run.id,
                "goal": run.goal,
                "target_url": run.target_url,
                "status": run.status,
                "steps_count": run.steps_count,
                "screens_count": run.screens_count,
                "paths_count": run.paths_count,
                "friction_score": run.friction_score
            }
            report_file = ReporterService.generate_report(report_data, previous_steps_data, all_issues, [{"destination": current_url}])
            run.report_path = report_file
            db.commit()

        except asyncio.CancelledError:
            print(f"[AutonomousAgent] Run {run_id} cancelled / server reloaded.")
            try:
                run.status = "STOPPED"
                run.error_message = "Run was cancelled or interrupted by server reload."
                db.commit()
            except Exception:
                pass
            raise
        except Exception as e:
            print(f"[AutonomousAgent] Fatal error during run execution: {e}")
            traceback.print_exc()
            run.status = "FAILED"
            run.error_message = str(e) or type(e).__name__
            db.commit()

        finally:
            await browser.close()
            db.close()
