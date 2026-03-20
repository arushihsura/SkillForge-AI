"""
SkillForge ML Daemon
====================
Persistent async server that stays warm between requests.
Communicates with Node via a Unix socket (or TCP on Windows).

Modes:
  python3 ml/daemon.py                    → Unix socket at /tmp/skillforge.sock
  python3 ml/daemon.py --tcp 8001         → TCP on port 8001
  python3 ml/daemon.py --stdin            → single-shot stdin/stdout (fallback)

Protocol: newline-delimited JSON.
  Request:  {"id": "...", "resumeText": "...", "jobDescription": "...", "hoursPerWeek": 10}
  Response: stream of {"id": "...", "event": "stage"|"complete"|"error", "data": {...}}

The engine is instantiated ONCE at startup and reused — no cold start per request.
Concurrent requests are handled via asyncio — non-blocking.
Results are LRU-cached by SHA256(resume+jd) — identical inputs hit cache instantly.
"""

from __future__ import annotations
import asyncio, json, hashlib, time, sys, os, signal
from collections import OrderedDict
from typing import AsyncIterator

# Import from the v2 engine in the same directory
sys.path.insert(0, os.path.dirname(__file__))
from skill_gap_model import (
    SkillForgeEngine,
    BayesianSkillExtractor,
    SkillComparator,
    GraphReasoner,
    HireReadinessPlanner,
    ReadinessModel,
    LEARN_HOURS,
)
import math


# ── LRU Cache ─────────────────────────────────────────────────────────────

class LRUCache:
    def __init__(self, maxsize: int = 128):
        self._cache: OrderedDict[str, dict] = OrderedDict()
        self._maxsize = maxsize

    def key(self, resume: str, jd: str, hpw: int) -> str:
        raw = f"{resume.strip()}||{jd.strip()}||{hpw}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get(self, k: str) -> dict | None:
        if k in self._cache:
            self._cache.move_to_end(k)
            return self._cache[k]
        return None

    def set(self, k: str, v: dict) -> None:
        if k in self._cache:
            self._cache.move_to_end(k)
        else:
            if len(self._cache) >= self._maxsize:
                self._cache.popitem(last=False)
            self._cache[k] = v


# ── Streaming Engine Wrapper ───────────────────────────────────────────────

class StreamingEngine:
    """
    Wraps SkillForgeEngine to yield partial results stage-by-stage.
    Each yield is a dict the daemon can immediately push to the client.
    This is the core innovation: the frontend sees results as they compute,
    not after everything finishes.
    """

    def __init__(self) -> None:
        self.extractor  = BayesianSkillExtractor()
        self.comparator = SkillComparator()
        self.reasoner   = GraphReasoner()
        self.planner    = HireReadinessPlanner()
        self.readiness_model = ReadinessModel()

    async def stream(
        self,
        resume_text: str,
        jd_text: str,
        hours_per_week: int = 10,
    ) -> AsyncIterator[dict]:
        """
        Yields dicts, each one a partial result the frontend can render immediately.
        Total latency to first render: ~2ms (just the extractor).
        """
        t0 = time.monotonic()

        # ── Stage 1: Extract ──────────────────────────────────────────────
        # Run in executor so we don't block the event loop
        loop = asyncio.get_running_loop()

        resume_skills = await loop.run_in_executor(
            None, self.extractor.extract, resume_text
        )
        jd_skills_raw = await loop.run_in_executor(
            None, self.extractor.extract, jd_text
        )
        job_skills = sorted(s for s, c in jd_skills_raw.items() if c >= 0.60)

        yield {
            "event": "stage",
            "stage": 1,
            "label": "Skill extraction",
            "data": {
                "resumeSkills": sorted(
                    [{"skill": s, "confidence": round(c, 3)}
                     for s, c in resume_skills.items()],
                    key=lambda x: -x["confidence"]
                ),
                "jobSkills": job_skills,
            },
            "ms": round((time.monotonic() - t0) * 1000),
        }

        # ── Stage 2: Compare ──────────────────────────────────────────────
        matched, raw_gaps, soft_matched = await loop.run_in_executor(
            None, self.comparator.compare, resume_skills, job_skills
        )

        yield {
            "event": "stage",
            "stage": 2,
            "label": "Probabilistic matching",
            "data": {
                "matchedSkills": sorted(matched, key=lambda x: -x["confidence"]),
                "softMatches":   soft_matched,
                "rawGapCount":   len(raw_gaps),
            },
            "ms": round((time.monotonic() - t0) * 1000),
        }

        # ── Stage 3: Graph reasoning ──────────────────────────────────────
        have_set = set(resume_skills.keys())
        enriched_gaps = await loop.run_in_executor(
            None, self.reasoner.enrich, raw_gaps, have_set, job_skills
        )

        yield {
            "event": "stage",
            "stage": 3,
            "label": "Dependency graph reasoning",
            "data": {
                "missingSkills": [
                    {"skill": g["skill"], "priority": g["priority"],
                     "reason": g["reason"], "implicit": g["implicit"]}
                    for g in enriched_gaps
                ],
                "kpis": {
                    "criticalGaps":  sum(1 for g in enriched_gaps if g["priority"] == "critical"),
                    "highGaps":      sum(1 for g in enriched_gaps if g["priority"] == "high"),
                    "implicitGaps":  sum(1 for g in enriched_gaps if g["implicit"]),
                },
            },
            "ms": round((time.monotonic() - t0) * 1000),
        }

        # ── Stage 4: Dijkstra path ────────────────────────────────────────
        learning_path = await loop.run_in_executor(
            None, self.planner.plan, enriched_gaps, have_set, hours_per_week
        )
        total_hours = sum(s["estimatedHours"] for s in learning_path)
        est_weeks = math.ceil(total_hours / hours_per_week) if learning_path else 0

        yield {
            "event": "stage",
            "stage": 4,
            "label": "Learning path planning",
            "data": {
                "learningPath":        learning_path,
                "estimatedTotalHours": total_hours,
                "estimatedWeeks":      est_weeks,
            },
            "ms": round((time.monotonic() - t0) * 1000),
        }

        # ── Stage 5: Readiness model ──────────────────────────────────────
        readiness = await loop.run_in_executor(
            None,
            self.readiness_model.compute,
            matched, soft_matched, enriched_gaps,
            job_skills, learning_path, hours_per_week
        )

        # Final complete payload
        yield {
            "event": "complete",
            "data": {
                "resumeSkills":  sorted(
                    [{"skill": s, "confidence": round(c, 3)}
                     for s, c in resume_skills.items()],
                    key=lambda x: -x["confidence"]
                ),
                "jobSkills":     job_skills,
                "matchedSkills": sorted(matched, key=lambda x: -x["confidence"]),
                "softMatches":   soft_matched,
                "missingSkills": [
                    {"skill": g["skill"], "priority": g["priority"],
                     "reason": g["reason"], "implicit": g["implicit"]}
                    for g in enriched_gaps
                ],
                "skillGapScore": readiness["currentReadinessPct"],
                "readiness":     readiness,
                "learningPath":  learning_path,
                "kpis": {
                    "totalSkillsRequired":   len(job_skills),
                    "alreadyHave":           len(matched),
                    "softMatches":           len(soft_matched),
                    "criticalGaps":          sum(1 for g in enriched_gaps if g["priority"] == "critical"),
                    "implicitGaps":          sum(1 for g in enriched_gaps if g["implicit"]),
                    "estimatedWeeksToReady": est_weeks,
                    "estimatedTotalHours":   total_hours,
                },
                "reasoningTrace": [
                    f"Stage 1 — Extracted {len(resume_skills)} resume signals, {len(job_skills)} JD requirements.",
                    f"Stage 2 — {len(matched)} confident matches, {len(soft_matched)} soft matches, {len(raw_gaps)} gaps.",
                    f"Stage 3 — {sum(1 for g in enriched_gaps if g['priority']=='critical')} critical, "
                    f"{sum(1 for g in enriched_gaps if g['implicit'])} implicit gaps via DAG propagation.",
                    f"Stage 4 — Dijkstra path: {len(learning_path)} skills, {total_hours}h total, ~{est_weeks} weeks.",
                    f"Stage 5 — Readiness: {readiness['currentReadinessPct']}% now → {readiness['projectedReadinessPct']}% after path.",
                ],
            },
            "ms": round((time.monotonic() - t0) * 1000),
        }


# ── Daemon Server ──────────────────────────────────────────────────────────

class SkillForgeDaemon:
    """
    Async server. Handles N concurrent analysis requests without blocking.
    Single engine instance — warm after first request.
    """

    def __init__(self) -> None:
        self.engine = StreamingEngine()
        self.cache  = LRUCache(maxsize=256)
        self._requests = 0
        self._cache_hits = 0

    async def handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            raw = await reader.readline()
            if not raw:
                return

            req = json.loads(raw.decode().strip())
            req_id       = req.get("id", "req")
            resume_text  = req.get("resumeText", "")
            jd_text      = req.get("jobDescription", "")
            hours_per_week = int(req.get("hoursPerWeek", 10))
            self._requests += 1

            # ── Cache check ───────────────────────────────────────────────
            cache_key = self.cache.key(resume_text, jd_text, hours_per_week)
            cached = self.cache.get(cache_key)
            if cached:
                self._cache_hits += 1
                response = json.dumps({
                    "id": req_id, "event": "complete",
                    "cached": True, "data": cached, "ms": 0
                })
                writer.write((response + "\n").encode())
                await writer.drain()
                writer.close()
                return

            # ── Stream stages ─────────────────────────────────────────────
            complete_data = None
            async for chunk in self.engine.stream(resume_text, jd_text, hours_per_week):
                chunk["id"] = req_id
                writer.write((json.dumps(chunk) + "\n").encode())
                await writer.drain()
                if chunk["event"] == "complete":
                    complete_data = chunk["data"]

            # Cache the final result
            if complete_data:
                self.cache.set(cache_key, complete_data)

        except json.JSONDecodeError as e:
            err = json.dumps({"event": "error", "error": f"Bad JSON: {e}"})
            writer.write((err + "\n").encode())
            await writer.drain()
        except Exception as e:
            err = json.dumps({"event": "error", "error": str(e)})
            writer.write((err + "\n").encode())
            await writer.drain()
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def stats(self) -> dict:
        return {
            "requests": self._requests,
            "cacheHits": self._cache_hits,
            "hitRate": round(self._cache_hits / max(1, self._requests), 3),
            "cacheSize": len(self.cache._cache),
        }

    async def run_unix(self, path: str = "/tmp/skillforge.sock") -> None:
        if os.path.exists(path):
            os.unlink(path)
        server = await asyncio.start_unix_server(self.handle_client, path=path)
        os.chmod(path, 0o600)
        print(f"[SkillForge daemon] Unix socket: {path}", flush=True)
        async with server:
            await server.serve_forever()

    async def run_tcp(self, port: int = 8001) -> None:
        server = await asyncio.start_server(self.handle_client, "127.0.0.1", port)
        print(f"[SkillForge daemon] TCP: 127.0.0.1:{port}", flush=True)
        async with server:
            await server.serve_forever()

    async def run_stdin(self) -> None:
        """Single-shot stdin/stdout fallback — for environments without persistent processes."""
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(None, sys.stdin.readline)
        req = json.loads(raw.strip())
        async for chunk in self.engine.stream(
            req.get("resumeText", ""),
            req.get("jobDescription", ""),
            int(req.get("hoursPerWeek", 10)),
        ):
            if chunk["event"] == "complete":
                print(json.dumps(chunk["data"]), flush=True)
                return


if __name__ == "__main__":
    daemon = SkillForgeDaemon()

    def handle_sigterm(*_):
        print("[SkillForge daemon] SIGTERM received, shutting down.", flush=True)
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_sigterm)

    if "--stdin" in sys.argv:
        asyncio.run(daemon.run_stdin())
    elif "--tcp" in sys.argv:
        idx = sys.argv.index("--tcp")
        port = int(sys.argv[idx + 1]) if len(sys.argv) > idx + 1 else 8001
        asyncio.run(daemon.run_tcp(port))
    else:
        sock = os.environ.get("SF_SOCKET", "/tmp/skillforge.sock")
        asyncio.run(daemon.run_unix(sock))
