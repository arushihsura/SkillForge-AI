"""
SkillForge AI — ML Skill Gap Analysis Engine
=============================================
Drop-in replacement for the /api/analyze route's AI logic.

Architecture
------------
1. SkillExtractor      — TF-IDF + regex + curated taxonomy → skill tokens
2. SemanticMatcher     — cosine similarity over TF-IDF vectors (no GPU needed)
3. SkillGraphReasoner  — prerequisite graph propagation (which gaps block others)
4. LearningPathPlanner — topological sort + difficulty-aware scheduling
5. AnalysisEngine      — orchestrates all stages, returns the JSON contract

JSON contract (matches SkillForge frontend expectations)
---------------------------------------------------------
{
  "resumeSkills":    ["Python", ...],
  "jobSkills":       ["Kubernetes", ...],
  "matchedSkills":   [{"skill": "Python", "confidence": 0.94}, ...],
  "missingSkills":   [{"skill": "Kubernetes", "priority": "critical", "reason": "..."}],
  "skillGapScore":   72,           // 0-100, higher = closer to ready
  "learningPath":    [
      {"week": 1, "skill": "Docker", "resources": [...], "estimatedHours": 8},
      ...
  ],
  "reasoningTrace":  ["Step 1: ...", ...],
  "kpis": {
      "totalSkillsRequired": 18,
      "alreadyHave": 12,
      "criticalGaps": 3,
      "niceToHaveGaps": 3,
      "estimatedWeeksToReady": 6
  }
}
"""

from __future__ import annotations

import re
import math
import json
import heapq
from collections import defaultdict, deque
from typing import Any

# ---------------------------------------------------------------------------
# 1.  SKILL TAXONOMY
# ---------------------------------------------------------------------------

SKILL_TAXONOMY: dict[str, list[str]] = {
    # Languages
    "python": ["py", "python3", "python2"],
    "javascript": ["js", "node", "nodejs", "node.js", "es6", "typescript", "ts"],
    "java": ["java8", "java11", "java17", "spring", "springboot"],
    "c++": ["cpp", "c plus plus"],
    "go": ["golang"],
    "rust": [],
    "r": ["r-lang", "r language"],
    "sql": ["mysql", "postgresql", "postgres", "sqlite", "t-sql", "plsql", "nosql"],

    # ML / AI
    "machine learning": ["ml", "supervised learning", "unsupervised learning"],
    "deep learning": ["dl", "neural network", "neural networks", "ann", "dnn"],
    "nlp": ["natural language processing", "text mining", "transformers"],
    "computer vision": ["cv", "image recognition", "object detection"],
    "llm": ["large language model", "gpt", "llama", "claude", "gemini", "chatgpt"],
    "pytorch": ["torch"],
    "tensorflow": ["tf", "keras"],
    "scikit-learn": ["sklearn", "scikit learn"],
    "hugging face": ["huggingface", "hf transformers"],
    "mlops": ["ml ops", "model deployment", "model serving"],
    "rag": ["retrieval augmented generation", "retrieval-augmented"],
    "vector database": ["vectordb", "pinecone", "weaviate", "chroma", "faiss", "qdrant"],

    # Data
    "pandas": ["dataframe", "data frames"],
    "numpy": [],
    "spark": ["apache spark", "pyspark"],
    "data engineering": ["etl", "data pipeline", "data pipelines"],
    "data visualization": ["matplotlib", "seaborn", "plotly", "tableau", "power bi", "powerbi"],
    "statistics": ["statistical analysis", "hypothesis testing", "regression"],
    "feature engineering": ["feature extraction", "feature selection"],

    # Cloud
    "aws": ["amazon web services", "s3", "ec2", "lambda", "sagemaker", "bedrock"],
    "gcp": ["google cloud", "google cloud platform", "bigquery", "vertex ai"],
    "azure": ["microsoft azure", "azure ml"],

    # Infra / DevOps
    "docker": ["containerization", "containers"],
    "kubernetes": ["k8s", "container orchestration"],
    "ci/cd": ["cicd", "jenkins", "github actions", "gitlab ci", "devops"],
    "terraform": ["infrastructure as code", "iac"],
    "linux": ["unix", "bash", "shell scripting"],

    # Web
    "react": ["reactjs", "react.js"],
    "fastapi": ["fast api"],
    "flask": [],
    "rest api": ["restful", "rest", "api design"],
    "graphql": [],

    # Soft / Process
    "agile": ["scrum", "kanban", "sprint"],
    "git": ["version control", "github", "gitlab"],
    "communication": ["presentation skills", "stakeholder management"],
    "problem solving": ["analytical thinking", "critical thinking"],
}

# Prerequisite edges: skill → [skills that should come first]
PREREQ_GRAPH: dict[str, list[str]] = {
    "deep learning":       ["machine learning", "python", "numpy"],
    "nlp":                 ["python", "machine learning"],
    "computer vision":     ["python", "deep learning"],
    "llm":                 ["nlp", "python"],
    "rag":                 ["llm", "vector database"],
    "mlops":               ["machine learning", "docker", "python"],
    "pytorch":             ["python", "numpy", "machine learning"],
    "tensorflow":          ["python", "numpy", "machine learning"],
    "hugging face":        ["python", "nlp", "deep learning"],
    "spark":               ["python", "sql", "data engineering"],
    "kubernetes":          ["docker"],
    "ci/cd":               ["docker", "git"],
    "terraform":           ["linux", "ci/cd"],
    "feature engineering": ["python", "pandas", "statistics"],
    "data engineering":    ["sql", "python"],
    "vector database":     ["python"],
    "react":               ["javascript"],
    "fastapi":             ["python", "rest api"],
    "flask":               ["python", "rest api"],
    "graphql":             ["rest api"],
}

DIFFICULTY_HOURS: dict[str, int] = {
    # key: canonical skill name, value: estimated hours to reach working proficiency
    "python": 40, "javascript": 40, "java": 50, "sql": 20, "r": 30,
    "machine learning": 60, "deep learning": 80, "nlp": 60, "computer vision": 70,
    "llm": 50, "pytorch": 40, "tensorflow": 40, "hugging face": 30,
    "rag": 25, "vector database": 15, "mlops": 45,
    "pandas": 15, "numpy": 10, "spark": 40, "statistics": 35,
    "data engineering": 50, "data visualization": 20, "feature engineering": 25,
    "aws": 40, "gcp": 40, "azure": 40,
    "docker": 20, "kubernetes": 35, "ci/cd": 25, "terraform": 30, "linux": 20,
    "react": 40, "fastapi": 15, "flask": 15, "rest api": 20, "graphql": 20,
    "git": 10, "agile": 8,
}
DEFAULT_HOURS = 20

RESOURCE_DB: dict[str, list[dict]] = {
    "python": [
        {"title": "Python for Everybody (Coursera)", "url": "https://coursera.org/specializations/python", "type": "course"},
        {"title": "Real Python Tutorials", "url": "https://realpython.com", "type": "tutorial"},
    ],
    "machine learning": [
        {"title": "Andrew Ng ML Specialization (Coursera)", "url": "https://coursera.org/specializations/machine-learning-introduction", "type": "course"},
        {"title": "Hands-On ML with Scikit-Learn & TensorFlow (O'Reilly)", "url": "https://oreilly.com/library/view/hands-on-machine-learning/9781098125967/", "type": "book"},
    ],
    "deep learning": [
        {"title": "fast.ai Practical Deep Learning", "url": "https://fast.ai", "type": "course"},
        {"title": "Deep Learning Specialization (Coursera)", "url": "https://coursera.org/specializations/deep-learning", "type": "course"},
    ],
    "llm": [
        {"title": "LLM Bootcamp (Full Stack Deep Learning)", "url": "https://fullstackdeeplearning.com/llm-bootcamp/", "type": "course"},
        {"title": "Building LLM-Powered Apps (DeepLearning.AI)", "url": "https://deeplearning.ai", "type": "course"},
    ],
    "rag": [
        {"title": "LangChain RAG Tutorial", "url": "https://python.langchain.com/docs/tutorials/rag/", "type": "tutorial"},
        {"title": "RAG from Scratch (DeepLearning.AI)", "url": "https://deeplearning.ai", "type": "course"},
    ],
    "docker": [
        {"title": "Docker Official Get Started", "url": "https://docs.docker.com/get-started/", "type": "docs"},
        {"title": "Docker & Kubernetes (Udemy)", "url": "https://udemy.com", "type": "course"},
    ],
    "kubernetes": [
        {"title": "Kubernetes Official Tutorial", "url": "https://kubernetes.io/docs/tutorials/", "type": "docs"},
        {"title": "CKA Prep (KodeKloud)", "url": "https://kodekloud.com", "type": "course"},
    ],
    "aws": [
        {"title": "AWS Cloud Practitioner (AWS Training)", "url": "https://aws.amazon.com/training/", "type": "course"},
        {"title": "AWS Solutions Architect Path", "url": "https://aws.amazon.com/certification/", "type": "course"},
    ],
    "sql": [
        {"title": "SQLZoo Interactive Tutorials", "url": "https://sqlzoo.net", "type": "tutorial"},
        {"title": "Mode SQL Tutorial", "url": "https://mode.com/sql-tutorial/", "type": "tutorial"},
    ],
    "pytorch": [
        {"title": "PyTorch Official Tutorials", "url": "https://pytorch.org/tutorials/", "type": "docs"},
        {"title": "Deep Learning with PyTorch (Manning)", "url": "https://www.manning.com/books/deep-learning-with-pytorch", "type": "book"},
    ],
    "mlops": [
        {"title": "MLOps Zoomcamp (DataTalks.Club)", "url": "https://github.com/DataTalksClub/mlops-zoomcamp", "type": "course"},
        {"title": "Made With ML MLOps Guide", "url": "https://madewithml.com", "type": "tutorial"},
    ],
    "vector database": [
        {"title": "Pinecone Learning Center", "url": "https://pinecone.io/learn/", "type": "tutorial"},
        {"title": "Weaviate Academy", "url": "https://weaviate.io/developers/academy", "type": "course"},
    ],
}


def _default_resources(skill: str) -> list[dict]:
    return [
        {"title": f"Search '{skill}' on Coursera", "url": f"https://coursera.org/search?query={skill.replace(' ', '+')}", "type": "search"},
        {"title": f"'{skill}' on YouTube", "url": f"https://youtube.com/results?search_query={skill.replace(' ', '+')}+tutorial", "type": "video"},
    ]


# ---------------------------------------------------------------------------
# 2.  SKILL EXTRACTOR
# ---------------------------------------------------------------------------

class SkillExtractor:
    """
    Converts raw text (resume / JD) → canonical skill names.
    Uses: alias expansion, regex boundary matching, deduplication.
    """

    def __init__(self) -> None:
        # Build reverse lookup: alias → canonical
        self._alias_to_canonical: dict[str, str] = {}
        for canonical, aliases in SKILL_TAXONOMY.items():
            self._alias_to_canonical[canonical] = canonical
            for alias in aliases:
                self._alias_to_canonical[alias] = canonical

        # Sort by length descending so longer phrases match first
        self._sorted_aliases = sorted(
            self._alias_to_canonical.keys(), key=len, reverse=True
        )

    def extract(self, text: str) -> list[str]:
        text_lower = text.lower()
        found: set[str] = set()
        # Replace matched spans with placeholder to avoid double-counting
        masked = text_lower
        for alias in self._sorted_aliases:
            pattern = r'(?<![a-z0-9])' + re.escape(alias) + r'(?![a-z0-9])'
            if re.search(pattern, masked):
                canonical = self._alias_to_canonical[alias]
                found.add(canonical)
                masked = re.sub(pattern, ' __MATCHED__ ', masked)
        return sorted(found)


# ---------------------------------------------------------------------------
# 3.  SEMANTIC MATCHER  (TF-IDF cosine similarity, no external libs)
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    return re.findall(r'[a-z0-9]+', text.lower())


def _build_tfidf(docs: list[str]) -> list[dict[str, float]]:
    """Returns TF-IDF vectors as dicts."""
    tokenized = [_tokenize(d) for d in docs]
    # IDF
    N = len(docs)
    df: dict[str, int] = defaultdict(int)
    for tokens in tokenized:
        for t in set(tokens):
            df[t] += 1
    idf = {t: math.log((N + 1) / (f + 1)) + 1 for t, f in df.items()}
    # TF-IDF
    vectors = []
    for tokens in tokenized:
        tf: dict[str, float] = defaultdict(float)
        for t in tokens:
            tf[t] += 1
        total = len(tokens) or 1
        vec = {t: (c / total) * idf[t] for t, c in tf.items()}
        vectors.append(vec)
    return vectors


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    dot = sum(a.get(t, 0.0) * v for t, v in b.items())
    norm_a = math.sqrt(sum(v * v for v in a.values())) or 1e-9
    norm_b = math.sqrt(sum(v * v for v in b.values())) or 1e-9
    return dot / (norm_a * norm_b)


class SemanticMatcher:
    """
    Matches resume skills to JD skills using TF-IDF cosine similarity.
    Exact taxonomy matches get confidence 1.0; fuzzy matches get 0.5–0.95.
    """

    def match(
        self,
        resume_skills: list[str],
        job_skills: list[str],
    ) -> tuple[list[dict], list[str]]:
        """
        Returns:
          matched: [{"skill": str, "confidence": float}]
          missing: [str]  (job skills not found in resume, even fuzzily)
        """
        resume_set = set(resume_skills)
        matched = []
        missing = []

        if not resume_skills:
            return [], job_skills[:]

        resume_vecs = _build_tfidf(resume_skills)
        for js in job_skills:
            if js in resume_set:
                matched.append({"skill": js, "confidence": 1.0})
                continue
            # fuzzy: compare js vector against all resume skill vectors
            js_vec = _build_tfidf([js])[0]
            best_score = max(_cosine(js_vec, rv) for rv in resume_vecs)
            if best_score >= 0.45:
                matched.append({"skill": js, "confidence": round(best_score, 3)})
            else:
                missing.append(js)

        return matched, missing


# ---------------------------------------------------------------------------
# 4.  SKILL GRAPH REASONER
# ---------------------------------------------------------------------------

class SkillGraphReasoner:
    """
    Given missing skills, propagates through the prerequisite graph to:
    - identify which gaps are 'critical' (block many other skills)
    - surface implicit gaps (e.g. missing Docker when Kubernetes is missing)
    - compute a priority score per gap
    """

    def _transitive_prereqs(self, skill: str, have: set[str]) -> list[str]:
        """BFS over PREREQ_GRAPH — returns prereqs the user doesn't have."""
        needed: list[str] = []
        visited = set()
        queue = deque([skill])
        while queue:
            s = queue.popleft()
            if s in visited:
                continue
            visited.add(s)
            for prereq in PREREQ_GRAPH.get(s, []):
                if prereq not in have:
                    needed.append(prereq)
                    queue.append(prereq)
        return list(dict.fromkeys(needed))  # deduplicated, preserves order

    def analyze(
        self,
        missing: list[str],
        have: set[str],
        job_skills: list[str],
    ) -> list[dict]:
        """
        Returns enriched missing-skill dicts:
        { "skill", "priority", "reason", "implicit", "blocks" }
        """
        # Count how many other missing skills each skill is a prereq of
        blocks_count: dict[str, int] = defaultdict(int)
        implicit_gaps: set[str] = set()

        for ms in missing:
            for prereq in self._transitive_prereqs(ms, have):
                if prereq not in missing:
                    implicit_gaps.add(prereq)
                blocks_count[prereq] += 1

        all_gaps = list(dict.fromkeys(missing + list(implicit_gaps)))

        result = []
        for skill in all_gaps:
            n_blocks = blocks_count.get(skill, 0)
            is_implicit = skill in implicit_gaps and skill not in missing
            in_jd = skill in job_skills

            if in_jd and n_blocks >= 2:
                priority = "critical"
                reason = f"Directly required by JD and a prerequisite for {n_blocks} other skills."
            elif in_jd:
                priority = "high"
                reason = "Explicitly listed in the job description."
            elif n_blocks >= 1:
                priority = "medium"
                reason = f"Not in JD but prerequisite for {n_blocks} required skill(s)."
            else:
                priority = "nice-to-have"
                reason = "Implicit gap — helpful background knowledge."

            result.append({
                "skill": skill,
                "priority": priority,
                "reason": reason,
                "implicit": is_implicit,
                "blocks": n_blocks,
            })

        # Sort: critical → high → medium → nice-to-have
        order = {"critical": 0, "high": 1, "medium": 2, "nice-to-have": 3}
        result.sort(key=lambda x: (order[x["priority"]], -x["blocks"]))
        return result


# ---------------------------------------------------------------------------
# 5.  LEARNING PATH PLANNER
# ---------------------------------------------------------------------------

class LearningPathPlanner:
    """
    Topological sort over prerequisite graph → weekly schedule.
    """

    def _topo_sort(self, skills: list[str]) -> list[str]:
        """Kahn's algorithm over the subgraph induced by `skills`."""
        skill_set = set(skills)
        in_degree: dict[str, int] = {s: 0 for s in skills}
        adj: dict[str, list[str]] = defaultdict(list)

        for skill in skills:
            for prereq in PREREQ_GRAPH.get(skill, []):
                if prereq in skill_set:
                    in_degree[skill] += 1
                    adj[prereq].append(skill)

        # Min-heap to pick alphabetically stable order among same-degree nodes
        queue: list[tuple[int, str]] = []
        for s, d in in_degree.items():
            if d == 0:
                heapq.heappush(queue, (0, s))

        sorted_skills: list[str] = []
        while queue:
            _, s = heapq.heappop(queue)
            sorted_skills.append(s)
            for neighbour in adj[s]:
                in_degree[neighbour] -= 1
                if in_degree[neighbour] == 0:
                    heapq.heappush(queue, (0, neighbour))

        # Append any cycles (shouldn't exist but safety net)
        remaining = [s for s in skills if s not in sorted_skills]
        return sorted_skills + remaining

    def build(
        self, enriched_gaps: list[dict], hours_per_week: int = 10
    ) -> list[dict]:
        """
        Returns a list of weekly learning plan entries.
        """
        # Only plan for critical / high / medium (skip nice-to-have for brevity)
        plannable = [
            g for g in enriched_gaps if g["priority"] in ("critical", "high", "medium")
        ]
        skills = [g["skill"] for g in plannable]
        if not skills:
            return []

        ordered = self._topo_sort(skills)
        priority_map = {g["skill"]: g["priority"] for g in enriched_gaps}

        plan: list[dict] = []
        week = 1
        accumulated = 0

        for skill in ordered:
            hours = DIFFICULTY_HOURS.get(skill, DEFAULT_HOURS)
            resources = RESOURCE_DB.get(skill, _default_resources(skill))[:2]

            plan.append({
                "week": week,
                "skill": skill,
                "priority": priority_map.get(skill, "medium"),
                "estimatedHours": hours,
                "resources": resources,
            })

            accumulated += hours
            week = math.ceil(accumulated / hours_per_week)

        return plan


# ---------------------------------------------------------------------------
# 6.  ORCHESTRATOR
# ---------------------------------------------------------------------------

class AnalysisEngine:
    """
    Main entry point. Call `analyze(resume_text, jd_text)` → dict.
    """

    def __init__(self) -> None:
        self.extractor = SkillExtractor()
        self.matcher   = SemanticMatcher()
        self.reasoner  = SkillGraphReasoner()
        self.planner   = LearningPathPlanner()

    def analyze(
        self,
        resume_text: str,
        jd_text: str,
        hours_per_week: int = 10,
    ) -> dict[str, Any]:
        trace: list[str] = []

        # Step 1 – Extract
        resume_skills = self.extractor.extract(resume_text)
        job_skills    = self.extractor.extract(jd_text)
        trace.append(
            f"Step 1 — Skill Extraction: found {len(resume_skills)} skill(s) in resume, "
            f"{len(job_skills)} skill(s) in job description."
        )

        # Step 2 – Match
        matched, raw_missing = self.matcher.match(resume_skills, job_skills)
        trace.append(
            f"Step 2 — Semantic Matching: {len(matched)} skill(s) matched "
            f"(exact + fuzzy), {len(raw_missing)} initially missing."
        )

        # Step 3 – Graph reasoning
        have_set = set(resume_skills) | {m["skill"] for m in matched}
        enriched_gaps = self.reasoner.analyze(raw_missing, have_set, job_skills)
        critical = [g for g in enriched_gaps if g["priority"] == "critical"]
        implicit = [g for g in enriched_gaps if g["implicit"]]
        trace.append(
            f"Step 3 — Graph Reasoning: identified {len(critical)} critical gap(s) "
            f"and {len(implicit)} implicit prerequisite gap(s) via dependency propagation."
        )

        # Step 4 – Learning path
        learning_path = self.planner.build(enriched_gaps, hours_per_week)
        total_hours   = sum(e["estimatedHours"] for e in learning_path)
        est_weeks     = math.ceil(total_hours / hours_per_week) if learning_path else 0
        trace.append(
            f"Step 4 — Learning Path: {len(learning_path)} skill(s) scheduled across "
            f"~{est_weeks} week(s) at {hours_per_week} hrs/week."
        )

        # KPIs
        n_required   = len(job_skills)
        n_have        = len(matched)
        gap_score     = round((n_have / n_required) * 100) if n_required else 100
        n_critical    = len([g for g in enriched_gaps if g["priority"] == "critical"])
        n_nice        = len([g for g in enriched_gaps if g["priority"] == "nice-to-have"])

        trace.append(
            f"Step 5 — Readiness Score: {gap_score}/100 — "
            f"you already have {n_have}/{n_required} required skill(s)."
        )

        return {
            "resumeSkills":  resume_skills,
            "jobSkills":     job_skills,
            "matchedSkills": [{"skill": m["skill"], "confidence": m["confidence"]} for m in matched],
            "missingSkills": [
                {"skill": g["skill"], "priority": g["priority"], "reason": g["reason"]}
                for g in enriched_gaps
            ],
            "skillGapScore": gap_score,
            "learningPath":  learning_path,
            "reasoningTrace": trace,
            "kpis": {
                "totalSkillsRequired":   n_required,
                "alreadyHave":           n_have,
                "criticalGaps":          n_critical,
                "niceToHaveGaps":        n_nice,
                "estimatedWeeksToReady": est_weeks,
            },
        }


# ---------------------------------------------------------------------------
# 7.  FLASK / EXPRESS BRIDGE  (drop-in for backend/routes/analyze.js)
# ---------------------------------------------------------------------------

def create_flask_app():
    """
    Optional: expose as a standalone Python microservice.
    Call from analyze.js via HTTP if you prefer Python isolation.
    """
    try:
        from flask import Flask, request, jsonify
        from flask_cors import CORS
    except ImportError:
        raise ImportError("pip install flask flask-cors")

    app   = Flask(__name__)
    CORS(app)
    engine = AnalysisEngine()

    @app.route("/ml/analyze", methods=["POST"])
    def analyze():
        body = request.get_json(force=True) or {}
        resume_text      = body.get("resumeText", "")
        jd_text          = body.get("jobDescription", "")
        hours_per_week   = int(body.get("hoursPerWeek", 10))

        if not resume_text or not jd_text:
            return jsonify({"error": "resumeText and jobDescription are required"}), 400

        result = engine.analyze(resume_text, jd_text, hours_per_week)
        return jsonify(result)

    @app.route("/ml/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "model": "SkillForge ML v1.0"})

    return app


# ---------------------------------------------------------------------------
# 8.  QUICK SELF-TEST
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    # ── subprocess mode: read JSON from stdin, write result to stdout ──────
    if "--stdin" in sys.argv:
        raw = sys.stdin.read()
        try:
            body = json.loads(raw)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"Invalid JSON input: {e}"}))
            sys.exit(1)

        engine = AnalysisEngine()
        result = engine.analyze(
            body.get("resumeText", ""),
            body.get("jobDescription", ""),
            int(body.get("hoursPerWeek", 10)),
        )
        print(json.dumps(result))
        sys.exit(0)

    # ── microservice mode ──────────────────────────────────────────────────
    if "--serve" in sys.argv:
        port = int(sys.argv[sys.argv.index("--serve") + 1]) if "--serve" in sys.argv and len(sys.argv) > sys.argv.index("--serve") + 1 else 8001
        app = create_flask_app()
        print(f"SkillForge ML service running on http://0.0.0.0:{port}")
        app.run(host="0.0.0.0", port=port)
        sys.exit(0)

    # ── self-test mode (default) ───────────────────────────────────────────
    SAMPLE_RESUME = """
    Software Engineer with 3 years of experience.
    Proficient in Python, JavaScript, React, SQL and REST APIs.
    Built ML pipelines using scikit-learn and pandas.
    Familiar with Docker, Git and Linux.
    """

    SAMPLE_JD = """
    We are looking for an ML Engineer.
    Requirements:
    - Strong Python skills
    - Experience with PyTorch or TensorFlow
    - Familiarity with LLMs and RAG pipelines
    - Knowledge of MLOps practices (CI/CD, model serving)
    - Kubernetes and AWS experience preferred
    - NLP or computer vision background a plus
    - SQL and data engineering skills
    - Excellent communication and problem solving
    """

    engine = AnalysisEngine()
    result = engine.analyze(SAMPLE_RESUME, SAMPLE_JD)
    print(json.dumps(result, indent=2))
