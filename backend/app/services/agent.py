import asyncio
import os
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from urllib.parse import urlparse
from sqlalchemy.orm import Session
from app.config import SCREENSHOTS_DIR, TARGET_URL, ENCRYPT_AT_REST
from app.database import SessionLocal
from app.models import Run, Step, Issue, PathModel
from app.security import cipher
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

            run_model = getattr(run, "model", None)
            run_screenshot_dir = SCREENSHOTS_DIR / f"run_{run_id}"
            run_screenshot_dir.mkdir(parents=True, exist_ok=True)

            max_steps = 15
            step_number = 0
            all_issues = []
            visited_states = []
            previous_steps_data = []
            visited_urls: set = set()
            failed_targets: set = set()

            await browser.start(headless=True)
            target = run.target_url or TARGET_URL
            target_parsed = urlparse(target)
            target_host = target_parsed.netloc.lower().split(':')[0] if target_parsed.netloc else ""

            # Track HTTP errors with subresource filtering and deduplication
            http_errors = []
            seen_error_urls = set()
            ASSET_EXTENSIONS = (
                '.webp', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.bmp',
                '.css', '.js', '.map', '.woff', '.woff2', '.ttf', '.eot', '.mp4', '.mp3'
            )

            async def handle_response(response):
                try:
                    status_code = response.status
                    if status_code >= 400:
                        url = response.url
                        clean_path = url.split('?')[0].split('#')[0].lower()

                        # Ignore static assets, media, fonts, and stylesheets
                        if clean_path.endswith(ASSET_EXTENSIONS):
                            return

                        # Check Playwright resource type: ignore subresources
                        req = response.request
                        res_type = req.resource_type if req else "other"
                        if res_type in ["image", "media", "font", "stylesheet", "other", "ping"]:
                            return

                        # Deduplicate: only record once per test run
                        if url not in seen_error_urls:
                            seen_error_urls.add(url)
                            http_errors.append((url, status_code, res_type))
                except Exception:
                    pass

            browser.page.on("response", handle_response)

            nav_start = time.time()
            await browser.navigate(target)
            nav_duration_ms = (time.time() - nav_start) * 1000

            finished = False
            while not finished and step_number < max_steps:
                # Check if run was requested to stop
                db.refresh(run)
                if run.status == "STOPPED":
                    print(f"[AutonomousAgent] Run {run_id} stopped by user.")
                    break

                step_number += 1
                step_start_time = time.time()

                # 1. Check HTTP Errors accumulated (document navigation errors only)
                while http_errors:
                    err_url, status_code, res_type = http_errors.pop(0)
                    severity = "CRITICAL" if status_code >= 500 else "HIGH" if res_type == "document" else "MEDIUM"
                    dyn_score = 9.0 if status_code >= 500 else 7.0 if res_type == "document" else 4.0
                    bl_issue = {
                        "type": "BROKEN_LINK",
                        "category": "BROKEN_LINK",
                        "severity": severity,
                        "dynamic_score": dyn_score,
                        "title": f"HTTP {status_code} Error on {res_type.capitalize()}",
                        "description": f"Navigation request to '{err_url}' failed with HTTP error status {status_code}.",
                        "impact_summary": f"Users encountering this {status_code} response are blocked from viewing the requested destination page.",
                        "fix_suggestion": f"Check routing and server configuration for '{err_url}'. Ensure URL rewrite rules, link targets, and endpoints exist.",
                        "step_number": step_number,
                        "url": browser.page.url,
                        "element_summary": f"HTTP Status: {status_code} ({res_type})"
                    }
                    all_issues.append(bl_issue)
                    db.add(Issue(run_id=run_id, **bl_issue))
                    db.commit()

                # 2. Performance timing check
                if nav_duration_ms > 3000:
                    perf_issue = {
                        "type": "PERFORMANCE",
                        "category": "PERFORMANCE",
                        "severity": "MEDIUM",
                        "title": "Slow page response time",
                        "description": f"Page navigation took {nav_duration_ms / 1000:.2f}s (exceeds 3.0s threshold).",
                        "step_number": step_number,
                        "url": browser.page.url,
                        "element_summary": f"Duration: {nav_duration_ms:.0f}ms"
                    }
                    score_res = await PlannerService.score_issue(
                        perf_issue["title"], perf_issue["description"], perf_issue["element_summary"], perf_issue["url"]
                    )
                    perf_issue.update(score_res)
                    all_issues.append(perf_issue)
                    db.add(Issue(run_id=run_id, **perf_issue))
                    db.commit()
                    nav_duration_ms = 0.0

                # 3. Security surface scan
                sec_findings = await browser.page.evaluate("""() => {
                    const findings = [];
                    document.querySelectorAll('form').forEach(f => {
                        const act = f.getAttribute('action') || '';
                        if (act.startsWith('http://') && window.location.protocol === 'https:') {
                            findings.push({
                                title: "Insecure Form Action over HTTP",
                                desc: "Form action attribute points to unencrypted http:// endpoint on an HTTPS site.",
                                elem: f.outerHTML.slice(0, 150)
                            });
                        }
                    });
                    document.querySelectorAll('input[type="password"]').forEach(p => {
                        if (!p.getAttribute('autocomplete')) {
                            findings.push({
                                title: "Missing Password Autocomplete Attribute",
                                desc: "Password field lacks autocomplete attribute ('current-password' or 'new-password').",
                                elem: p.outerHTML.slice(0, 150)
                            });
                        }
                    });
                    const bodyText = document.body.innerText || '';
                    if (bodyText.includes('Traceback (most recent call last)') || bodyText.includes('NullPointerException') || bodyText.includes('Fatal error:')) {
                        findings.push({
                            title: "Exposed Server Stack Trace",
                            desc: "Uncaught backend exception or debug stack trace is visibly rendered to end users.",
                            elem: bodyText.slice(0, 200)
                        });
                    }
                    return findings;
                }""")
                for sf in sec_findings:
                    s_issue = {
                        "type": "SECURITY",
                        "category": "SECURITY",
                        "severity": "HIGH",
                        "title": sf["title"],
                        "description": sf["desc"],
                        "step_number": step_number,
                        "url": browser.page.url,
                        "element_summary": sf["elem"]
                    }
                    if not any(i["title"] == s_issue["title"] for i in all_issues):
                        score_res = await PlannerService.score_issue(
                            s_issue["title"], s_issue["description"], s_issue["element_summary"], s_issue["url"]
                        )
                        s_issue.update(score_res)
                        all_issues.append(s_issue)
                        db.add(Issue(run_id=run_id, **s_issue))
                        db.commit()

                # 4. Observe current browser state
                observation = await ObserverService.observe_page(browser.page)
                current_url = observation["url"]
                state_sig = observation["state_signature"]
                visited_states.append(state_sig)
                visited_urls.add(current_url)

                # 5. Accessibility Analysis with batch dynamic scoring (deduplicated across session)
                a11y_issues = AccessibilityAnalyzer.analyze_observation(observation, step_number)
                new_a11y = [
                    i for i in a11y_issues
                    if not any(
                        x["title"] == i["title"] and x.get("element_summary") == i.get("element_summary")
                        for x in all_issues
                    )
                ]
                if new_a11y:
                    async def _score_a11y(issue):
                        score_res = await PlannerService.score_issue(
                            issue["title"], issue["description"], issue.get("element_summary"), current_url
                        )
                        issue.update(score_res)
                        issue["category"] = "ACCESSIBILITY"
                        return issue

                    scored_a11y = await asyncio.gather(*[_score_a11y(i) for i in new_a11y], return_exceptions=True)
                    for res in scored_a11y:
                        if isinstance(res, Exception):
                            continue
                        all_issues.append(res)
                        db.add(Issue(
                            run_id=run_id,
                            type=res["type"],
                            category="ACCESSIBILITY",
                            severity=res["severity"],
                            dynamic_score=res.get("dynamic_score", 5.0),
                            title=res["title"],
                            description=res["description"],
                            impact_summary=res.get("impact_summary"),
                            fix_suggestion=res.get("fix_suggestion"),
                            step_number=step_number,
                            url=current_url,
                            element_summary=res.get("element_summary")
                        ))
                    db.commit()

                # Mark failed targets on observation elements
                for el in observation.get("elements", []):
                    el_name = (el.get("accessible_name") or el.get("text") or "").strip().lower()
                    if el_name in failed_targets:
                        el["is_failed"] = True

                # 6. Plan next action using LLM / Fallback
                decision = await PlannerService.decide_next_action(
                    goal=run.goal,
                    observation=observation,
                    previous_steps=previous_steps_data,
                    visited_states=visited_states,
                    model=run_model,
                    failed_targets=failed_targets
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

                # 7. Friction Analysis with dynamic scoring (deduplicated across session)
                friction_issues = FrictionAnalyzer.analyze_step(
                    observation=observation,
                    step_number=step_number,
                    action_data=decision,
                    visited_signatures=visited_states,
                    previous_actions=previous_steps_data
                )
                new_friction = [
                    i for i in friction_issues
                    if not any(
                        x["title"] == i["title"] and x.get("element_summary") == i.get("element_summary")
                        for x in all_issues
                    )
                ]
                if new_friction:
                    async def _score_friction(issue):
                        score_res = await PlannerService.score_issue(
                            issue["title"], issue["description"], issue.get("element_summary"), current_url, model=run_model
                        )
                        issue.update(score_res)
                        issue["category"] = "FRICTION"
                        return issue

                    scored_friction = await asyncio.gather(*[_score_friction(i) for i in new_friction], return_exceptions=True)
                    for res in scored_friction:
                        if isinstance(res, Exception):
                            continue
                        all_issues.append(res)
                        db.add(Issue(
                            run_id=run_id,
                            type=res["type"],
                            category="FRICTION",
                            severity=res["severity"],
                            dynamic_score=res.get("dynamic_score", 5.0),
                            title=res["title"],
                            description=res["description"],
                            impact_summary=res.get("impact_summary"),
                            fix_suggestion=res.get("fix_suggestion"),
                            step_number=step_number,
                            url=current_url,
                            element_summary=res.get("element_summary")
                        ))
                    db.commit()

                # 8. Capture Screenshot with Target Highlighting (Action In Context)
                screenshot_filename = f"step_{step_number:03d}.png"
                screenshot_path = run_screenshot_dir / screenshot_filename

                if target_element and action_type in ["CLICK", "TYPE"]:
                    await browser.highlight_element(target_element, step_number, action_type)
                    await browser.take_screenshot(str(screenshot_path))
                    await browser.clear_highlight()
                else:
                    await browser.take_screenshot(str(screenshot_path))

                # 9. Execute Action
                act_start = time.time()
                executed = await browser.execute_action(decision, target_element)
                step_duration_ms = (time.time() - act_start) * 1000

                # 9b. Browser Error, Domain Boundary Guard & Recovery
                after_url = browser.page.url
                after_parsed = urlparse(after_url)

                # Check if landed on Chromium internal error page (e.g. net::ERR_CONNECTION_TIMED_OUT or DNS failure)
                if after_url.startswith("chrome-error://") or "chromewebdata" in after_url:
                    print(f"[AutonomousAgent] Unreachable route error on '{target_desc}' ({after_url}). Blacklisting target and recovering.")
                    if target_desc:
                        failed_targets.add(target_desc.strip().lower())

                    try:
                        await browser.page.go_back(wait_until="domcontentloaded", timeout=4000)
                    except Exception:
                        await browser.navigate(target)

                    if browser.page.url.startswith("chrome-error://") or "chromewebdata" in browser.page.url:
                        await browser.navigate(target)

                    if not any(i.get("element_summary") == target_desc and i.get("category") == "BROKEN_LINK" for i in all_issues):
                        db.add(Issue(
                            run_id=run_id,
                            type="BROKEN_LINK",
                            category="BROKEN_LINK",
                            severity="HIGH",
                            dynamic_score=7.0,
                            title="Unreachable Navigation Route",
                            description=f"Clicking '{target_desc}' failed to load and encountered a browser network error.",
                            impact_summary="Users attempting to follow this link encounter a connection failure or dead end.",
                            fix_suggestion="Verify target server availability, SSL certificates, and DNS routing for this link.",
                            step_number=step_number,
                            url=current_url,
                            element_summary=target_desc
                        ))
                        db.commit()

                elif after_parsed.netloc and target_host:
                    after_host = after_parsed.netloc.lower().split(':')[0]
                    is_in_bounds = (after_host == target_host or after_host.endswith('.' + target_host) or target_host.endswith('.' + after_host))

                    if not is_in_bounds:
                        print(f"[AutonomousAgent] Out of bounds detected: navigated to '{after_url}'. Returning to '{target_host}'.")
                        if target_desc:
                            failed_targets.add(target_desc.strip().lower())

                        try:
                            await browser.page.go_back(wait_until="domcontentloaded", timeout=4000)
                        except Exception:
                            await browser.navigate(target)

                        if not any(i.get("element_summary") == target_desc and i.get("title") == "External Navigation Out of Scope" for i in all_issues):
                            db.add(Issue(
                                run_id=run_id,
                                type="FRICTION",
                                category="FRICTION",
                                severity="LOW",
                                dynamic_score=2.5,
                                title="External Navigation Out of Scope",
                                description=f"Action on '{target_desc}' directed browser out-of-bounds to '{after_url}'. Automatically returned inside scope.",
                                impact_summary="Users may be unexpectedly redirected away from the primary application.",
                                fix_suggestion="Ensure external links include target='_blank' rel='noopener noreferrer' to preserve user session.",
                                step_number=step_number,
                                url=current_url,
                                element_summary=target_desc
                            ))
                            db.commit()

                # Check if landed on raw static asset (e.g. .webp, .jpg)
                if after_url.split('?')[0].lower().endswith(ASSET_EXTENSIONS):
                    print(f"[AutonomousAgent] Landed on raw asset URL '{after_url}'. Returning to previous page.")
                    if target_desc:
                        failed_targets.add(target_desc.strip().lower())
                    try:
                        await browser.page.go_back(wait_until="domcontentloaded", timeout=4000)
                    except Exception:
                        await browser.navigate(target)

                # 10. Record Step in Database
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
                    duration_ms=step_duration_ms,
                    timestamp=datetime.utcnow()
                )
                db.add(db_step)
                run.steps_count = step_number
                run.screens_count = len(visited_urls)
                db.commit()

                step_record = {
                    "step_number": step_number,
                    "action": action_type,
                    "target": target_desc,
                    "target_index": target_idx,
                    "state_signature": state_sig,
                    "reason": reason,
                    "thinking": thinking,
                    "confidence": confidence,
                    "url": current_url,
                    "duration_ms": step_duration_ms,
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

            # Calculate Dynamic Friction & Category Scores
            score_res = FrictionAnalyzer.calculate_friction_score(all_issues, step_number)
            run.friction_score = score_res["score"]
            run.category_scores = score_res["category_scores"]

            # Generate AI Executive Summary
            llm_summary = await PlannerService.generate_executive_summary(
                goal=run.goal,
                target_url=run.target_url,
                steps_count=run.steps_count,
                issues=all_issues,
                friction_score=run.friction_score
            )
            run.llm_summary = llm_summary
            db.commit()

            # Build Report
            report_data = {
                "id": run.id,
                "goal": run.goal,
                "target_url": run.target_url,
                "status": run.status,
                "mode": run.mode or "FOCUSED",
                "steps_count": run.steps_count,
                "screens_count": run.screens_count,
                "paths_count": run.paths_count,
                "friction_score": run.friction_score,
                "category_scores": run.category_scores,
                "llm_summary": run.llm_summary
            }
            report_file = ReporterService.generate_rich_report(
                report_data=report_data,
                steps_data=previous_steps_data,
                issues_data=all_issues,
                paths_data=[{"destination": current_url}],
                pages_tested=[{"url": u, "title": u, "depth": 0} for u in visited_urls]
            )

            # Encrypt report path at rest if enabled
            if ENCRYPT_AT_REST:
                run.report_path = cipher.encrypt(report_file)
            else:
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
