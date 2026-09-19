import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

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
from app.services.crawler import SiteCrawler

class MultiAgentOrchestrator:
    """
    Coordinates multi-agent full website exploration and security/accessibility auditing.
    Divides discovered site pages across 2-3 parallel specialized agent contexts.
    """
    @staticmethod
    async def execute_full_site_run(run_id: str):
        db = SessionLocal()
        try:
            run = db.query(Run).filter(Run.id == run_id).first()
            if not run:
                print(f"[MultiAgentOrchestrator] Run {run_id} not found.")
                return

            run.status = "RUNNING"
            run.mode = "FULL_SITE"
            run.started_at = datetime.utcnow()
            db.commit()

            base_url = run.target_url or TARGET_URL
            run_screenshot_dir = SCREENSHOTS_DIR / f"run_{run_id}"
            run_screenshot_dir.mkdir(parents=True, exist_ok=True)

            # Step 1: Discover pages via BFS crawler
            print(f"[MultiAgentOrchestrator] Crawling {base_url} to discover internal routes...")
            discovered_pages = await SiteCrawler.discover_pages(base_url, max_pages=15)
            print(f"[MultiAgentOrchestrator] Discovered {len(discovered_pages)} pages.")

            # Partition pages for parallel workers
            form_pages = [p for p in discovered_pages if p.get("has_form")]
            nav_pages = [p for p in discovered_pages if not p.get("has_form")]

            # Worker 1: Form & Security Inspector
            # Worker 2: Navigation & Broken Link Inspector
            # Worker 3 (if > 6 pages): Deep Accessibility Inspector
            tracks = []
            if form_pages:
                tracks.append({"role": "Form & Security Inspector", "pages": form_pages[:5]})
            else:
                tracks.append({"role": "Primary Journey Inspector", "pages": nav_pages[:3]})

            remaining_nav = [p for p in nav_pages if p not in tracks[0]["pages"]]
            half = len(remaining_nav) // 2
            if remaining_nav[:half]:
                tracks.append({"role": "Navigation & Performance Auditor", "pages": remaining_nav[:half]})
            if remaining_nav[half:]:
                tracks.append({"role": "Accessibility & Content Auditor", "pages": remaining_nav[half:]})
            elif not tracks or len(tracks) < 2:
                tracks.append({"role": "Exploratory Auditor", "pages": discovered_pages[:3]})

            # Run parallel agent workers
            tasks = [
                MultiAgentOrchestrator._run_worker(
                    run_id=run_id,
                    worker_index=idx + 1,
                    track_info=track,
                    run_screenshot_dir=run_screenshot_dir
                )
                for idx, track in enumerate(tracks[:3]) # max 3 parallel agents
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Refresh run
            db.refresh(run)
            all_steps = []
            all_issues_list = []
            sub_run_summaries = []
            total_screens = set()

            for idx, res in enumerate(results):
                if isinstance(res, Exception):
                    print(f"[MultiAgentOrchestrator] Worker {idx + 1} raised error: {res}")
                    continue
                sub_run_summaries.append(res.get("summary", {}))
                total_screens.update(res.get("visited_urls", []))
                all_steps.extend(res.get("steps", []))
                all_issues_list.extend(res.get("issues", []))

            # Query all issues recorded in DB for this run
            db_issues = db.query(Issue).filter(Issue.run_id == run_id).all()
            issues_for_score = [
                {
                    "type": i.type,
                    "category": i.category,
                    "severity": i.severity,
                    "dynamic_score": i.dynamic_score,
                    "title": i.title,
                    "description": i.description,
                    "impact_summary": i.impact_summary,
                    "fix_suggestion": i.fix_suggestion,
                    "url": i.url
                }
                for i in db_issues
            ]

            # Calculate composite scores
            score_data = FrictionAnalyzer.calculate_friction_score(issues_for_score, len(all_steps))
            run.friction_score = score_data["score"]
            run.category_scores = score_data["category_scores"]
            run.steps_count = len(all_steps)
            run.screens_count = max(len(total_screens), len(discovered_pages))
            run.paths_count = len(tracks)
            run.sub_runs = sub_run_summaries

            # Generate AI Executive Summary
            llm_summary = await PlannerService.generate_executive_summary(
                goal=f"Full Website Audit ({run.mode}) across {run.screens_count} discovered pages",
                target_url=base_url,
                steps_count=run.steps_count,
                issues=issues_for_score,
                friction_score=run.friction_score
            )
            run.llm_summary = llm_summary
            run.completed_at = datetime.utcnow()
            run.status = "COMPLETED"

            # Record paths
            for idx, track in enumerate(tracks):
                db.add(PathModel(
                    run_id=run_id,
                    path_number=idx + 1,
                    steps_json=[p["url"] for p in track["pages"]],
                    destination=track["pages"][-1]["url"] if track["pages"] else base_url
                ))

            db.commit()

            # Generate Rich HTML and JSON reports
            report_data = {
                "id": run.id,
                "goal": run.goal or "Full Site Comprehensive Audit",
                "target_url": run.target_url,
                "status": run.status,
                "mode": run.mode,
                "steps_count": run.steps_count,
                "screens_count": run.screens_count,
                "paths_count": run.paths_count,
                "friction_score": run.friction_score,
                "category_scores": run.category_scores,
                "llm_summary": run.llm_summary,
                "sub_runs": run.sub_runs
            }

            report_file = ReporterService.generate_rich_report(
                report_data=report_data,
                steps_data=all_steps,
                issues_data=issues_for_score,
                paths_data=[{"destination": t["pages"][-1]["url"]} for t in tracks if t["pages"]],
                pages_tested=discovered_pages
            )

            # Encrypt report path at rest if configured
            if ENCRYPT_AT_REST:
                run.report_path = cipher.encrypt(report_file)
            else:
                run.report_path = report_file

            db.commit()
            print(f"[MultiAgentOrchestrator] Full site run {run_id} completed successfully.")

        except Exception as e:
            print(f"[MultiAgentOrchestrator] Error during full site run: {e}")
            import traceback
            traceback.print_exc()
            run.status = "FAILED"
            run.error_message = str(e)
            db.commit()
        finally:
            db.close()

    @staticmethod
    async def _run_worker(
        run_id: str,
        worker_index: int,
        track_info: Dict[str, Any],
        run_screenshot_dir: Path
    ) -> Dict[str, Any]:
        """Worker agent executing targeted audits across assigned page routes."""
        db = SessionLocal()
        browser = BrowserManager()
        worker_steps = []
        worker_issues = []
        visited = []

        try:
            await browser.start(headless=True)
            pages = track_info.get("pages", [])
            role = track_info.get("role", "Worker Agent")

            for page_idx, page_info in enumerate(pages):
                target_url = page_info["url"]
                visited.append(target_url)

                # Listen for HTTP errors (4xx / 5xx) with subresource filtering and deduplication
                http_errors = []
                seen_worker_errors = set()
                ASSET_EXTENSIONS = (
                    '.webp', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.bmp',
                    '.css', '.js', '.map', '.woff', '.woff2', '.ttf', '.eot', '.mp4', '.mp3'
                )

                async def handle_response(response):
                    try:
                        status = response.status
                        if status >= 400:
                            url = response.url
                            clean_path = url.split('?')[0].split('#')[0].lower()
                            if clean_path.endswith(ASSET_EXTENSIONS):
                                return

                            req = response.request
                            res_type = req.resource_type if req else "other"
                            if res_type in ["image", "media", "font", "stylesheet", "other", "ping"]:
                                return

                            if url not in seen_worker_errors:
                                seen_worker_errors.add(url)
                                http_errors.append((url, status, res_type))
                    except Exception:
                        pass

                browser.page.on("response", handle_response)

                start_time = time.time()
                await browser.navigate(target_url)
                duration_ms = (time.time() - start_time) * 1000

                # 1. Performance check: if page load > 3000ms
                if duration_ms > 3000:
                    perf_issue = {
                        "type": "PERFORMANCE",
                        "category": "PERFORMANCE",
                        "severity": "MEDIUM",
                        "dynamic_score": 4.5,
                        "title": "Slow page response time",
                        "description": f"Page {target_url} took {duration_ms / 1000:.2f}s to load (exceeds 3.0s threshold).",
                        "impact_summary": "High latency degrades user experience and conversion rates.",
                        "fix_suggestion": "Optimize server response times, compress assets, and defer non-critical scripts.",
                        "url": target_url,
                        "element_summary": f"Load Duration: {duration_ms:.0f}ms"
                    }
                    worker_issues.append(perf_issue)
                    db.add(Issue(
                        run_id=run_id,
                        step_number=len(worker_steps) + 1,
                        **perf_issue
                    ))
                    db.commit()

                # 2. Broken Link / HTTP 4xx / 5xx checks
                for err_url, status_code, res_type in http_errors:
                    severity = "CRITICAL" if status_code >= 500 else "HIGH" if res_type == "document" else "MEDIUM"
                    dyn_score = 9.0 if status_code >= 500 else 7.0 if res_type == "document" else 4.0
                    bl_issue = {
                        "type": "BROKEN_LINK",
                        "category": "BROKEN_LINK",
                        "severity": severity,
                        "dynamic_score": dyn_score,
                        "title": f"HTTP {status_code} Error on {res_type.capitalize()}",
                        "description": f"Navigation request to '{err_url}' returned HTTP error status code {status_code}.",
                        "impact_summary": f"Users encountering this {status_code} response cannot access destination content.",
                        "fix_suggestion": f"Check routing and server configuration for '{err_url}'. Ensure URL rewrite rules and endpoints exist.",
                        "url": target_url,
                        "element_summary": f"HTTP Status: {status_code} ({res_type})"
                    }
                    worker_issues.append(bl_issue)
                    db.add(Issue(
                        run_id=run_id,
                        step_number=len(worker_steps) + 1,
                        **bl_issue
                    ))
                    db.commit()

                # 3. Security surface scan: forms over HTTP, missing password autocomplete, error stack traces
                sec_findings = await browser.page.evaluate("""() => {
                    const findings = [];
                    // Check for forms posting to insecure HTTP
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
                    // Check password fields
                    document.querySelectorAll('input[type="password"]').forEach(p => {
                        if (!p.getAttribute('autocomplete')) {
                            findings.push({
                                title: "Missing Password Autocomplete Attribute",
                                desc: "Password field lacks autocomplete attribute ('current-password' or 'new-password'), creating friction for password managers.",
                                elem: p.outerHTML.slice(0, 150)
                            });
                        }
                    });
                    // Check for exposed stack traces in body text
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
                        "url": target_url,
                        "element_summary": sf["elem"]
                    }
                    score_res = await PlannerService.score_issue(
                        s_issue["title"], s_issue["description"], s_issue["element_summary"], target_url
                    )
                    s_issue.update(score_res)
                    worker_issues.append(s_issue)
                    db.add(Issue(
                        run_id=run_id,
                        step_number=len(worker_steps) + 1,
                        **s_issue
                    ))
                    db.commit()

                # 4. Observe page DOM & Accessibility audit
                obs = await ObserverService.observe_page(browser.page)
                a11y_issues = AccessibilityAnalyzer.analyze_observation(obs, len(worker_steps) + 1)
                for issue in a11y_issues:
                    score_res = await PlannerService.score_issue(
                        issue["title"], issue["description"], issue.get("element_summary"), target_url
                    )
                    issue.update(score_res)
                    issue["category"] = "ACCESSIBILITY"
                    worker_issues.append(issue)
                    db.add(Issue(
                        run_id=run_id,
                        step_number=len(worker_steps) + 1,
                        **issue
                    ))
                    db.commit()

                # Screenshot
                screenshot_filename = f"w{worker_index}_step_{page_idx + 1:03d}.png"
                screenshot_path = run_screenshot_dir / screenshot_filename
                await browser.take_screenshot(str(screenshot_path))

                step_rec = {
                    "step_number": len(worker_steps) + 1,
                    "action": f"AUDIT_PAGE ({role})",
                    "target": target_url,
                    "reason": f"Worker {worker_index} inspected page {page_info.get('title', target_url)}",
                    "confidence": 0.95,
                    "url": target_url,
                    "duration_ms": duration_ms,
                    "screenshot_path": str(screenshot_path)
                }
                worker_steps.append(step_rec)

                db.add(Step(
                    run_id=run_id,
                    step_number=len(worker_steps),
                    action=step_rec["action"],
                    target=step_rec["target"],
                    reason=step_rec["reason"],
                    confidence=step_rec["confidence"],
                    url=target_url,
                    screenshot_path=str(screenshot_path),
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow()
                ))
                db.commit()

            return {
                "worker_index": worker_index,
                "role": role,
                "steps": worker_steps,
                "issues": worker_issues,
                "visited_urls": visited,
                "summary": {
                    "worker": worker_index,
                    "role": role,
                    "pages_checked": len(visited),
                    "issues_found": len(worker_issues)
                }
            }
        except Exception as e:
            print(f"[MultiAgentOrchestrator] Worker {worker_index} exception: {e}")
            return {"worker_index": worker_index, "error": str(e), "steps": worker_steps, "issues": worker_issues, "visited_urls": visited}
        finally:
            await browser.close()
            db.close()
