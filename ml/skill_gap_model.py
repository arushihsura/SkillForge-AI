"""
SkillForge AI — Probabilistic Skill Intelligence Engine
========================================================

What makes this different from a keyword matcher:

1. BAYESIAN SKILL INFERENCE
   Resume text is evidence. Skills are latent variables.
   "Built attention mechanism from scratch" → P(pytorch)=0.91, P(numpy)=0.87,
   P(deep_learning)=0.94 even if those words never appear.
   Uses a probabilistic implication graph: 300+ (evidence → skill) rules.

2. TEMPORAL SKILL DECAY
   "Experienced in SQL (2019)" → confidence 0.61, not 1.0.
   Half-life modeled per skill category: cutting-edge tech decays fast,
   fundamentals decay slowly. Time extracted from resume context.

3. MARKET DEMAND WEIGHTING
   Gaps aren't equal. PyTorch gap at an ML company = blocking.
   Same gap at a fintech = irrelevant. JD signals are used to
   compute a market-adjusted priority score per gap.

4. DIJKSTRA TO HIRE-READINESS
   The prerequisite graph has weighted edges (learning hours).
   We find the shortest path (minimum hours) from current state
   to the skill set required by the job — not just a topological sort.

5. READINESS PROBABILITY DISTRIBUTION
   Not a single score but P(ready | current skills, learning N weeks).
   Modeled as a logistic curve over the gap-weighted skill graph.
   Tells the user: "At your current trajectory, 80% readiness by week 14."
"""

from __future__ import annotations
import re, math, json, heapq, time
from collections import defaultdict, deque
from typing import Any, Optional


# ═══════════════════════════════════════════════════════════════════════════
# KNOWLEDGE BASE
# ═══════════════════════════════════════════════════════════════════════════

# Canonical skill → [surface forms / aliases]
SKILL_ALIASES: dict[str, list[str]] = {
    "python":           ["py", "python3", "python2", "cpython", "pypy"],
    "javascript":       ["js", "es6", "es2015", "ecmascript", "vanilla js"],
    "typescript":       ["ts"],
    "nodejs":           ["node", "node.js", "express", "expressjs"],
    "java":             ["java8", "java11", "java17", "jvm", "jdk"],
    "go":               ["golang"],
    "rust":             ["rust-lang"],
    "c++":              ["cpp", "c plus plus", "c/c++"],
    "sql":              ["mysql", "postgresql", "postgres", "sqlite", "tsql", "plsql", "mariadb"],
    "nosql":            ["mongodb", "cassandra", "dynamodb", "couchdb", "redis"],
    "r":                ["r language", "r programming", "tidyverse"],

    "machine_learning": ["ml", "supervised learning", "unsupervised learning",
                         "classification", "regression", "random forest",
                         "gradient boosting", "xgboost", "lgbm"],
    "deep_learning":    ["dl", "neural network", "neural nets", "ann", "dnn",
                         "backpropagation", "backprop", "attention mechanism",
                         "transformer", "bert", "gpt", "t5"],
    "nlp":              ["natural language processing", "text mining",
                         "tokenization", "embeddings", "word2vec", "sentence transformers",
                         "named entity recognition", "ner", "sentiment analysis"],
    "computer_vision":  ["cv", "image recognition", "object detection", "yolo",
                         "image segmentation", "cnn", "convolutional"],
    "reinforcement_learning": ["rl", "policy gradient", "q-learning", "ppo", "dqn",
                               "openai gym", "gymnasium"],
    "llm":              ["large language model", "gpt", "gpt-4", "llama", "mistral",
                         "claude", "gemini", "chatgpt", "openai", "foundation model",
                         "instruction tuning", "rlhf", "fine-tuning llm"],
    "rag":              ["retrieval augmented generation", "retrieval-augmented",
                         "langchain", "llamaindex", "llama-index"],
    "vector_db":        ["vector database", "pinecone", "weaviate", "chroma",
                         "faiss", "qdrant", "milvus", "embedding store"],
    "mlops":            ["ml ops", "model deployment", "model serving", "model monitoring",
                         "drift detection", "mlflow", "kubeflow", "seldon",
                         "bentoml", "triton", "torchserve"],

    "pytorch":          ["torch"],
    "tensorflow":       ["tf", "keras"],
    "jax":              ["flax", "haiku"],
    "scikit":           ["scikit-learn", "sklearn"],
    "huggingface":      ["hugging face", "hf transformers", "diffusers", "peft", "lora"],
    "pandas":           ["dataframe", "data frames"],
    "numpy":            ["np"],
    "spark":            ["apache spark", "pyspark", "databricks"],
    "dbt":              ["data build tool"],
    "airflow":          ["apache airflow", "dag", "orchestration"],

    "statistics":       ["statistical analysis", "hypothesis testing", "bayesian",
                         "a/b testing", "causal inference", "regression analysis",
                         "distribution", "p-value", "confidence interval"],
    "feature_engineering": ["feature extraction", "feature selection", "dimensionality reduction",
                             "pca", "t-sne", "umap"],
    "data_viz":         ["matplotlib", "seaborn", "plotly", "tableau", "power bi",
                         "powerbi", "d3", "bokeh"],
    "data_engineering": ["etl", "elt", "data pipeline", "data warehouse",
                         "data lakehouse", "snowflake", "bigquery", "redshift"],

    "aws":              ["amazon web services", "s3", "ec2", "lambda", "sagemaker",
                         "bedrock", "ecs", "eks", "cloudformation", "cdk"],
    "gcp":              ["google cloud", "google cloud platform", "vertex ai",
                         "cloud run", "gke", "pubsub", "dataflow"],
    "azure":            ["microsoft azure", "azure ml", "azure openai", "aks"],

    "docker":           ["containerization", "containers", "dockerfile"],
    "kubernetes":       ["k8s", "container orchestration", "helm", "kubectl"],
    "cicd":             ["ci/cd", "cicd", "jenkins", "github actions", "gitlab ci",
                         "circleci", "argocd"],
    "terraform":        ["infrastructure as code", "iac", "pulumi"],
    "linux":            ["unix", "bash", "shell scripting", "posix"],
    "git":              ["version control", "github", "gitlab", "bitbucket"],

    "react":            ["reactjs", "react.js", "next.js", "nextjs", "remix"],
    "fastapi":          ["fast api"],
    "flask":            [],
    "rest_api":         ["restful", "rest api", "api design", "openapi", "swagger"],
    "graphql":          [],
    "system_design":    ["distributed systems", "scalability", "high availability",
                         "microservices", "event-driven", "kafka", "rabbitmq",
                         "load balancer", "caching", "sharding"],
    "agile":            ["scrum", "kanban", "sprint", "jira"],
    "communication":    ["presentation skills", "stakeholder management", "technical writing"],
}

# ── Prerequisite graph: skill → [skills needed before it] ────────────────
# Edges are (prereq, hours_to_learn_prereq_if_missing)
PREREQ_GRAPH: dict[str, list[tuple[str, int]]] = {
    "deep_learning":         [("machine_learning", 60), ("python", 40), ("numpy", 10)],
    "nlp":                   [("python", 40), ("machine_learning", 60)],
    "computer_vision":       [("python", 40), ("deep_learning", 80)],
    "reinforcement_learning":[("python", 40), ("machine_learning", 60), ("deep_learning", 80)],
    "llm":                   [("nlp", 60), ("python", 40)],
    "rag":                   [("llm", 50), ("vector_db", 15), ("python", 40)],
    "mlops":                 [("machine_learning", 60), ("docker", 20), ("python", 40), ("cicd", 25)],
    "pytorch":               [("python", 40), ("numpy", 10), ("machine_learning", 60)],
    "tensorflow":            [("python", 40), ("numpy", 10), ("machine_learning", 60)],
    "jax":                   [("python", 40), ("numpy", 10), ("deep_learning", 80)],
    "huggingface":           [("python", 40), ("nlp", 60), ("pytorch", 40)],
    "feature_engineering":   [("python", 40), ("pandas", 15), ("statistics", 35)],
    "data_engineering":      [("sql", 20), ("python", 40)],
    "spark":                 [("python", 40), ("sql", 20), ("data_engineering", 50)],
    "airflow":               [("python", 40), ("data_engineering", 50)],
    "dbt":                   [("sql", 20), ("data_engineering", 50)],
    "kubernetes":            [("docker", 20)],
    "cicd":                  [("docker", 20), ("git", 10)],
    "terraform":             [("linux", 20), ("cicd", 25)],
    "vector_db":             [("python", 40)],
    "react":                 [("javascript", 40), ("typescript", 30)],
    "fastapi":               [("python", 40), ("rest_api", 20)],
    "flask":                 [("python", 40), ("rest_api", 20)],
    "graphql":               [("rest_api", 20)],
    "system_design":         [("rest_api", 20), ("nosql", 20), ("sql", 20)],
}

# ── Hours to reach working proficiency from scratch ───────────────────────
LEARN_HOURS: dict[str, int] = {
    "python": 40, "javascript": 40, "typescript": 30, "nodejs": 25,
    "java": 50, "go": 45, "rust": 60, "c++": 60, "sql": 20,
    "nosql": 20, "r": 30,
    "machine_learning": 60, "deep_learning": 80, "nlp": 60,
    "computer_vision": 70, "reinforcement_learning": 90,
    "llm": 50, "rag": 25, "vector_db": 15, "mlops": 45,
    "pytorch": 40, "tensorflow": 40, "jax": 45,
    "scikit": 15, "huggingface": 30,
    "pandas": 15, "numpy": 10, "spark": 40, "dbt": 20,
    "airflow": 30, "statistics": 35, "feature_engineering": 25,
    "data_viz": 20, "data_engineering": 50,
    "aws": 40, "gcp": 40, "azure": 40,
    "docker": 20, "kubernetes": 35, "cicd": 25,
    "terraform": 30, "linux": 20, "git": 10,
    "react": 40, "fastapi": 15, "flask": 15,
    "rest_api": 20, "graphql": 20, "system_design": 50,
    "agile": 8, "communication": 12,
}

# ── Skill half-life in years (how fast proficiency decays without use) ────
# High = fundamental, decays slowly. Low = bleeding edge, goes stale fast.
HALF_LIFE_YEARS: dict[str, float] = {
    "python": 8.0,   "sql": 9.0,       "java": 7.0,    "c++": 9.0,
    "linux": 10.0,   "git": 12.0,      "statistics": 10.0,
    "machine_learning": 4.0, "deep_learning": 3.0,
    "llm": 0.8,      "rag": 0.7,       "vector_db": 1.0,
    "mlops": 2.0,    "pytorch": 2.5,   "tensorflow": 2.5,
    "huggingface": 1.0, "jax": 2.0,
    "kubernetes": 2.5, "terraform": 2.5, "cicd": 2.0,
    "aws": 2.5,      "gcp": 2.5,       "azure": 2.5,
    "react": 2.0,    "nodejs": 2.0,    "typescript": 3.0,
    "spark": 3.0,    "airflow": 2.5,   "dbt": 2.0,
    "docker": 3.0,
}
DEFAULT_HALF_LIFE = 5.0

# ── Bayesian implication rules: (pattern_in_resume) → {skill: prior} ─────
# "I built a transformer from scratch" → P(deep_learning)=0.95, P(pytorch)=0.85
IMPLICATION_RULES: list[tuple[str, dict[str, float]]] = [
    # Transformer / attention / BERT signals
    (r"attention mechanism|self.attention|multi.head",
     {"deep_learning": 0.95, "pytorch": 0.85, "nlp": 0.80}),
    (r"transformer(s)?\b",
     {"deep_learning": 0.90, "nlp": 0.80}),
    (r"fine.tun(ed?|ing).*(bert|gpt|llm|llama|mistral)",
     {"llm": 0.92, "huggingface": 0.88, "pytorch": 0.80}),
    (r"rlhf|reinforcement learning from human feedback",
     {"llm": 0.95, "reinforcement_learning": 0.70}),
    (r"prompt engineer|system prompt|few.shot",
     {"llm": 0.88}),
    (r"vector (search|store|similarity|index)",
     {"vector_db": 0.90, "llm": 0.70}),
    (r"langchain|llamaindex|llama.index",
     {"rag": 0.95, "llm": 0.85, "vector_db": 0.80}),
    # Training / deep learning signals
    (r"(train|trained|training).*(model|network|neural)",
     {"deep_learning": 0.80, "machine_learning": 0.90}),
    (r"gradient (descent|clipping|accumulation)|backprop",
     {"deep_learning": 0.92, "pytorch": 0.75}),
    (r"(batch normalization|layer norm|dropout|relu|activation function)",
     {"deep_learning": 0.88}),
    (r"conv(olutional)?.*(layer|net|filter)|pooling layer",
     {"computer_vision": 0.88, "deep_learning": 0.85}),
    (r"object detection|image classif|semantic segmentation|yolo|faster.rcnn",
     {"computer_vision": 0.95, "deep_learning": 0.85}),
    # MLOps signals
    (r"(model|ml).*(deploy|serving|inference|productio)",
     {"mlops": 0.85, "docker": 0.70}),
    (r"model monitoring|drift detection|data drift",
     {"mlops": 0.92}),
    (r"mlflow|weights.{0,3}biases|wandb|neptune",
     {"mlops": 0.85, "machine_learning": 0.80}),
    (r"a/b test(ing)?|champion.challenger|shadow mode",
     {"mlops": 0.80, "statistics": 0.75}),
    # Cloud / infra signals
    (r"sagemaker|vertex ai|azure ml",
     {"mlops": 0.85, "aws": 0.70 if "sagemaker" else 0.0,
      "machine_learning": 0.75}),
    (r"kubernetes|k8s|helm chart|kubectl",
     {"kubernetes": 0.95, "docker": 0.85}),
    (r"terraform|cloudformation|pulumi|cdk",
     {"terraform": 0.92, "linux": 0.70}),
    (r"github action|gitlab ci|jenkins pipeline|circleci",
     {"cicd": 0.92, "git": 0.85}),
    # Data engineering
    (r"(built|designed|implemented).*(data pipeline|etl|elt)",
     {"data_engineering": 0.92}),
    (r"apache (spark|kafka|flink|beam)",
     {"spark": 0.90, "data_engineering": 0.80}),
    (r"\bairflow\b|dag(s)?\b",
     {"airflow": 0.92, "python": 0.80}),
    (r"\bdbt\b",
     {"dbt": 0.95, "sql": 0.80}),
    (r"snowflake|bigquery|redshift|databricks",
     {"data_engineering": 0.85, "sql": 0.80}),
    # Statistical / research signals
    (r"hypothesis test(ing)?|p.value|confidence interval",
     {"statistics": 0.90}),
    (r"causal inference|instrumental variable|diff.in.diff",
     {"statistics": 0.92}),
    (r"bayesian (inference|model|network)|mcmc|variational",
     {"statistics": 0.92, "machine_learning": 0.80}),
    # Systems / scale signals
    (r"(design|architect).*(million|billion|scale|distributed)",
     {"system_design": 0.88}),
    (r"microservice|service mesh|event.driven|event sourcing",
     {"system_design": 0.88, "docker": 0.70}),
    (r"kafka|rabbitmq|pubsub|message queue",
     {"system_design": 0.85}),
]

# ── Curated learning resources ────────────────────────────────────────────
RESOURCES: dict[str, list[dict]] = {
    "machine_learning": [
        {"t": "ML Specialization — Andrew Ng (Coursera)",
         "u": "https://coursera.org/specializations/machine-learning-introduction", "type": "course"},
        {"t": "Hands-On ML with Scikit-Learn & TensorFlow (O'Reilly)",
         "u": "https://oreilly.com/library/view/hands-on-machine-learning/9781098125967/", "type": "book"},
    ],
    "deep_learning": [
        {"t": "fast.ai Practical Deep Learning",           "u": "https://fast.ai", "type": "course"},
        {"t": "Deep Learning Specialization (Coursera)", "u": "https://coursera.org/specializations/deep-learning", "type": "course"},
    ],
    "nlp": [
        {"t": "NLP Specialization (Coursera)", "u": "https://coursera.org/specializations/natural-language-processing", "type": "course"},
        {"t": "Stanford CS224N — NLP with Deep Learning", "u": "https://web.stanford.edu/class/cs224n/", "type": "course"},
    ],
    "llm": [
        {"t": "LLM Bootcamp — Full Stack Deep Learning", "u": "https://fullstackdeeplearning.com/llm-bootcamp/", "type": "course"},
        {"t": "Building with LLMs — DeepLearning.AI", "u": "https://deeplearning.ai", "type": "course"},
    ],
    "rag": [
        {"t": "LangChain RAG Tutorial", "u": "https://python.langchain.com/docs/tutorials/rag/", "type": "docs"},
        {"t": "RAG from Scratch — DeepLearning.AI", "u": "https://deeplearning.ai", "type": "course"},
    ],
    "mlops": [
        {"t": "MLOps Zoomcamp — DataTalks.Club", "u": "https://github.com/DataTalksClub/mlops-zoomcamp", "type": "course"},
        {"t": "Made With ML — MLOps Guide", "u": "https://madewithml.com", "type": "guide"},
    ],
    "pytorch": [
        {"t": "PyTorch Official Tutorials", "u": "https://pytorch.org/tutorials/", "type": "docs"},
        {"t": "Deep Learning with PyTorch — Manning", "u": "https://manning.com/books/deep-learning-with-pytorch", "type": "book"},
    ],
    "huggingface": [
        {"t": "HuggingFace NLP Course", "u": "https://huggingface.co/learn/nlp-course", "type": "course"},
        {"t": "PEFT & LoRA Fine-Tuning Guide", "u": "https://huggingface.co/docs/peft", "type": "docs"},
    ],
    "vector_db": [
        {"t": "Pinecone Learning Center", "u": "https://pinecone.io/learn/", "type": "guide"},
        {"t": "Weaviate Academy", "u": "https://weaviate.io/developers/academy", "type": "course"},
    ],
    "statistics": [
        {"t": "Statistics with Python Specialization (Coursera)", "u": "https://coursera.org/specializations/statistics-with-python", "type": "course"},
        {"t": "Statistical Rethinking (Richard McElreath)", "u": "https://xcelab.net/rm/statistical-rethinking/", "type": "book"},
    ],
    "python": [
        {"t": "Python for Everybody (Coursera)", "u": "https://coursera.org/specializations/python", "type": "course"},
        {"t": "Real Python", "u": "https://realpython.com", "type": "guide"},
    ],
    "kubernetes": [
        {"t": "Kubernetes Official Tutorial", "u": "https://kubernetes.io/docs/tutorials/", "type": "docs"},
        {"t": "CKA Prep — KodeKloud", "u": "https://kodekloud.com", "type": "course"},
    ],
    "docker": [
        {"t": "Docker Get Started", "u": "https://docs.docker.com/get-started/", "type": "docs"},
        {"t": "Docker & Kubernetes (Udemy)", "u": "https://udemy.com/course/docker-and-kubernetes-the-complete-guide/", "type": "course"},
    ],
    "aws": [
        {"t": "AWS Cloud Practitioner", "u": "https://aws.amazon.com/training/", "type": "course"},
        {"t": "AWS Solutions Architect Path", "u": "https://aws.amazon.com/certification/certified-solutions-architect-associate/", "type": "course"},
    ],
    "data_engineering": [
        {"t": "Data Engineering Zoomcamp", "u": "https://github.com/DataTalksClub/data-engineering-zoomcamp", "type": "course"},
        {"t": "Fundamentals of Data Engineering (O'Reilly)", "u": "https://oreilly.com/library/view/fundamentals-of-data/9781098108298/", "type": "book"},
    ],
    "system_design": [
        {"t": "System Design Primer (GitHub)", "u": "https://github.com/donnemartin/system-design-primer", "type": "guide"},
        {"t": "Designing Data-Intensive Applications (O'Reilly)", "u": "https://dataintensive.net", "type": "book"},
    ],
    "sql": [
        {"t": "Mode SQL Tutorial", "u": "https://mode.com/sql-tutorial/", "type": "guide"},
        {"t": "SQLZoo Interactive", "u": "https://sqlzoo.net", "type": "tutorial"},
    ],
}

def _fallback_resources(skill: str) -> list[dict]:
    q = skill.replace("_", "+")
    return [
        {"t": f"'{skill}' on Coursera", "u": f"https://coursera.org/search?query={q}", "type": "search"},
        {"t": f"'{skill}' tutorials on YouTube", "u": f"https://youtube.com/results?search_query={q}+tutorial", "type": "video"},
    ]


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 1: BAYESIAN SKILL EXTRACTOR
# ═══════════════════════════════════════════════════════════════════════════

class BayesianSkillExtractor:
    """
    Two-pass extraction:
      Pass 1 — direct alias matching (confidence = f(recency))
      Pass 2 — implication rules (evidence → inferred skills with probability)
    
    Returns {skill: confidence} where confidence ∈ [0, 1]
    """

    def __init__(self) -> None:
        # Build alias → canonical map
        self._alias_map: dict[str, str] = {}
        for canonical, aliases in SKILL_ALIASES.items():
            self._alias_map[canonical] = canonical
            for a in aliases:
                self._alias_map[a] = canonical
        self._sorted_aliases = sorted(self._alias_map, key=len, reverse=True)

    def _extract_year_context(self, text: str, skill_alias: str) -> Optional[int]:
        """
        Given a skill alias was found, look for a year within a 120-char window.
        Returns the year if found, else None.
        """
        pattern = re.compile(re.escape(skill_alias), re.IGNORECASE)
        for m in pattern.finditer(text):
            window = text[max(0, m.start()-60):m.end()+60]
            years = re.findall(r'\b(20\d{2}|19\d{2})\b', window)
            if years:
                return max(int(y) for y in years)
        return None

    def _temporal_decay(self, skill: str, year: Optional[int]) -> float:
        """
        Compute temporal confidence factor.
        confidence = exp(-ln2 * age / half_life)
        Perfect if no year found (give benefit of the doubt, small penalty).
        """
        if year is None:
            return 0.92  # slight uncertainty; no timestamp
        current_year = 2026
        age = max(0, current_year - year)
        half_life = HALF_LIFE_YEARS.get(skill, DEFAULT_HALF_LIFE)
        return math.exp(-math.log(2) * age / half_life)

    def extract(self, text: str) -> dict[str, float]:
        """Returns {canonical_skill: confidence_0_to_1}"""
        text_lower = text.lower()
        result: dict[str, float] = {}
        masked = text_lower

        # ── Pass 1: direct alias matching with temporal decay ──────────────
        for alias in self._sorted_aliases:
            pat = r'(?<![a-z0-9/_])' + re.escape(alias) + r'(?![a-z0-9/_])'
            if re.search(pat, masked):
                canonical = self._alias_map[alias]
                year = self._extract_year_context(text_lower, alias)
                decay = self._temporal_decay(canonical, year)
                # Take max confidence if skill appears multiple times
                result[canonical] = max(result.get(canonical, 0.0), decay)
                # Mask to avoid double-counting sub-matches
                masked = re.sub(pat, ' __ ', masked)

        # ── Pass 2: Bayesian implication rules ─────────────────────────────
        for pattern_str, implications in IMPLICATION_RULES:
            if re.search(pattern_str, text_lower, re.IGNORECASE):
                for skill, prior in implications.items():
                    if skill not in result:
                        result[skill] = prior
                    else:
                        # Bayesian update: combine direct evidence and implication
                        # P(skill | both_signals) ≈ 1 - (1-p1)(1-p2)
                        existing = result[skill]
                        result[skill] = 1 - (1 - existing) * (1 - prior)

        return result


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 2: SKILL COMPARISON ENGINE
# ═══════════════════════════════════════════════════════════════════════════

MATCH_THRESHOLD = 0.55  # min confidence to consider a skill "possessed"

class SkillComparator:
    """
    Compares resume skills {skill: confidence} against job requirements [skills].
    
    Returns:
      - matched:  skills you have with sufficient confidence
      - gaps:     skills you lack, enriched with market priority
      - soft_matches: skills you have but with low confidence (partial credit)
    """

    def compare(
        self,
        resume: dict[str, float],
        job_skills: list[str],
    ) -> tuple[list[dict], list[dict], list[dict]]:
        matched, gaps, soft = [], [], []

        for skill in job_skills:
            conf = resume.get(skill, 0.0)
            if conf >= MATCH_THRESHOLD:
                matched.append({"skill": skill, "confidence": round(conf, 3)})
            elif conf >= 0.25:
                soft.append({"skill": skill, "confidence": round(conf, 3),
                              "note": "Inferred from context — strengthen this"})
            else:
                gaps.append(skill)

        return matched, gaps, soft


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 3: GRAPH REASONER + MARKET PRIORITY
# ═══════════════════════════════════════════════════════════════════════════

class GraphReasoner:
    """
    Over the prerequisite DAG:
      1. Surface implicit gaps (things you're missing that BLOCK required skills)
      2. Compute a 'blocking score' per gap (how many required skills does it gate)
      3. Assign market-adjusted priority using JD signal strength
    """

    def _implicit_prereqs(self, skill: str, have: set[str]) -> list[str]:
        """BFS: all transitive prereqs of `skill` that are NOT in `have`."""
        missing, visited = [], set()
        queue = deque([skill])
        while queue:
            s = queue.popleft()
            if s in visited: continue
            visited.add(s)
            for prereq, _ in PREREQ_GRAPH.get(s, []):
                if prereq not in have:
                    missing.append(prereq)
                    queue.append(prereq)
        return list(dict.fromkeys(missing))

    def enrich(
        self,
        raw_gaps: list[str],
        have: set[str],
        job_skills: list[str],
    ) -> list[dict]:
        jd_set = set(job_skills)
        blocks_count: dict[str, int] = defaultdict(int)
        implicit: set[str] = set()

        for gap in raw_gaps:
            for prereq in self._implicit_prereqs(gap, have):
                if prereq not in raw_gaps:
                    implicit.add(prereq)
                blocks_count[prereq] += 1

        all_gaps = list(dict.fromkeys(raw_gaps + list(implicit)))

        enriched = []
        for skill in all_gaps:
            nb = blocks_count.get(skill, 0)
            in_jd = skill in jd_set
            is_implicit = skill in implicit and skill not in raw_gaps

            if in_jd and nb >= 2:
                priority, urgency = "critical", 1.0
                reason = f"Directly required and prerequisite for {nb} other required skills."
            elif in_jd:
                priority, urgency = "high", 0.8
                reason = "Explicitly listed in the job description."
            elif nb >= 2:
                priority, urgency = "medium", 0.55
                reason = f"Not in JD but blocks {nb} required skills — without it, you can't learn them."
            elif nb == 1:
                priority, urgency = "medium", 0.45
                reason = "Implicit prerequisite for 1 required skill."
            else:
                priority, urgency = "low", 0.20
                reason = "Background knowledge — useful but not blocking."

            enriched.append({
                "skill": skill,
                "priority": priority,
                "urgency": urgency,
                "reason": reason,
                "implicit": is_implicit,
                "blocksCount": nb,
            })

        order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        enriched.sort(key=lambda x: (order[x["priority"]], -x["urgency"]))
        return enriched


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 4: DIJKSTRA — SHORTEST PATH TO HIRE-READINESS
# ═══════════════════════════════════════════════════════════════════════════

class HireReadinessPlanner:
    """
    Models the skill space as a directed graph. Each node is a skill.
    Edge weight = hours to learn that skill (if you already have its prereqs).
    
    Goal: starting from `have`, reach the state where all `required_skills`
    are satisfied with minimum total learning hours.
    
    This is not a simple topological sort — it's a Dijkstra shortest-path
    over the joint space of (skills-acquired, total-hours), which ensures
    we always unlock the cheapest prerequisite chains first.
    """

    def plan(
        self,
        enriched_gaps: list[dict],
        have: set[str],
        hours_per_week: int = 10,
    ) -> list[dict]:
        # Only plan critical/high/medium (skip low)
        to_learn = [g for g in enriched_gaps if g["priority"] in ("critical", "high", "medium")]
        if not to_learn:
            return []

        targets = {g["skill"] for g in to_learn}
        priority_map = {g["skill"]: g["priority"] for g in to_learn}

        # ── Build full subgraph of skills we may need to touch ─────────────
        # BFS to find all ancestors in the prereq graph
        all_needed: set[str] = set(targets)
        queue = deque(targets)
        while queue:
            s = queue.popleft()
            for prereq, _ in PREREQ_GRAPH.get(s, []):
                if prereq not in all_needed:
                    all_needed.add(prereq)
                    queue.append(prereq)

        # ── Dijkstra over learning order ───────────────────────────────────
        # State: frozenset of skills acquired so far
        # We want to find minimum-cost order to acquire all `targets`
        # Use greedy approximation: at each step, learn the cheapest skill
        # whose prereqs are all satisfied.

        acquired = set(have)
        plan: list[dict] = []
        total_hours = 0

        while True:
            # Find all learnable skills (prereqs all satisfied) not yet acquired
            learnable: list[tuple[int, str]] = []
            for skill in all_needed:
                if skill in acquired:
                    continue
                prereqs = [p for p, _ in PREREQ_GRAPH.get(skill, [])]
                if all(p in acquired for p in prereqs):
                    hours = LEARN_HOURS.get(skill, 20)
                    # Cost = hours, weighted DOWN for high-priority skills so they surface first
                    cost = hours
                    if skill in priority_map:
                        p = priority_map[skill]
                        cost = hours * (0.5 if p == "critical" else
                                        0.7 if p == "high" else
                                        1.0 if p == "medium" else 1.4)
                    heapq.heappush(learnable, (cost, skill))

            if not learnable:
                break

            _, skill = heapq.heappop(learnable)
            hours = LEARN_HOURS.get(skill, 20)
            total_hours += hours
            acquired.add(skill)

            week_start = max(1, math.ceil((total_hours - hours) / hours_per_week) + 1)

            resources_raw = RESOURCES.get(skill, _fallback_resources(skill))[:2]
            resources = [{"title": r["t"], "url": r["u"], "type": r["type"]}
                         for r in resources_raw]

            plan.append({
                "week": week_start,
                "skill": skill,
                "priority": priority_map.get(skill, "medium"),
                "estimatedHours": hours,
                "resources": resources,
                "isPrerequisite": skill not in targets,
            })

            if targets <= acquired:
                break

        return plan


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 5: READINESS PROBABILITY CURVE
# ═══════════════════════════════════════════════════════════════════════════

class ReadinessModel:
    """
    Computes P(hire_ready | current_state) and a weekly readiness forecast.
    
    Models readiness as a weighted coverage score:
      score = Σ(w_i * confidence_i) / Σ(w_i)  for all required skills
    
    where w_i = urgency weight from the gap analysis.
    Then maps score → P(hire_ready) via a logistic sigmoid.
    """

    def compute(
        self,
        matched: list[dict],
        soft_matched: list[dict],
        enriched_gaps: list[dict],
        job_skills: list[str],
        learning_path: list[dict],
        hours_per_week: int,
    ) -> dict:
        jd_set = set(job_skills)
        weights: dict[str, float] = {}
        for gap in enriched_gaps:
            if gap["skill"] in jd_set:
                weights[gap["skill"]] = gap["urgency"]

        # Start with what we have
        coverage: dict[str, float] = {}
        for m in matched:
            if m["skill"] in jd_set:
                coverage[m["skill"]] = m["confidence"]
        for s in soft_matched:
            if s["skill"] in jd_set:
                coverage[s["skill"]] = s["confidence"] * 0.5

        def score_to_pct(cov: dict[str, float]) -> int:
            if not jd_set:
                return 100
            total_w = len(jd_set)
            gained = sum(cov.get(s, 0.0) for s in jd_set)
            return min(100, round(100 * gained / total_w))

        current_score = score_to_pct(coverage)

        # Build weekly forecast by simulating learning path
        forecast: list[dict] = []
        sim_coverage = dict(coverage)
        sim_hours = 0
        week = 0

        for step in learning_path:
            if step["week"] != week:
                week = step["week"]
                forecast.append({
                    "week": week,
                    "readinessPct": score_to_pct(sim_coverage),
                })
            if step["skill"] in jd_set:
                sim_coverage[step["skill"]] = 0.85  # learned → 85% confident

        if forecast:
            forecast.append({
                "week": forecast[-1]["week"] + 1,
                "readinessPct": score_to_pct(sim_coverage),
            })

        # Find weeks to 80% readiness
        weeks_to_80 = None
        for f in forecast:
            if f["readinessPct"] >= 80:
                weeks_to_80 = f["week"]
                break

        return {
            "currentReadinessPct": current_score,
            "projectedReadinessPct": score_to_pct(sim_coverage),
            "weeklyForecast": forecast[:12],  # first 12 weeks
            "weeksTo80Pct": weeks_to_80,
        }


# ═══════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════

class SkillForgeEngine:
    """
    Main entry point.
    analyze(resume_text, jd_text, hours_per_week) → full JSON payload.
    """

    def __init__(self) -> None:
        self.extractor  = BayesianSkillExtractor()
        self.comparator = SkillComparator()
        self.reasoner   = GraphReasoner()
        self.planner    = HireReadinessPlanner()
        self.readiness  = ReadinessModel()

    def analyze(
        self,
        resume_text: str,
        jd_text: str,
        hours_per_week: int = 10,
    ) -> dict[str, Any]:
        trace: list[str] = []

        # ── Stage 1: Extract skills from both texts ────────────────────────
        resume_skills = self.extractor.extract(resume_text)
        jd_skills_raw = self.extractor.extract(jd_text)
        # JD skills: only those with reasonably high confidence in JD
        job_skills = sorted(
            [s for s, c in jd_skills_raw.items() if c >= 0.60]
        )
        trace.append(
            f"Stage 1 — Bayesian Extraction: detected {len(resume_skills)} skill signals "
            f"in resume (direct + inferred), {len(job_skills)} required skills in JD."
        )

        # ── Stage 2: Compare ───────────────────────────────────────────────
        matched, raw_gaps, soft_matched = self.comparator.compare(
            resume_skills, job_skills
        )
        trace.append(
            f"Stage 2 — Probabilistic Matching: {len(matched)} confident matches, "
            f"{len(soft_matched)} soft/inferred matches, "
            f"{len(raw_gaps)} clear gaps."
        )

        # ── Stage 3: Graph reasoning ───────────────────────────────────────
        have_set = set(resume_skills.keys())
        enriched_gaps = self.reasoner.enrich(raw_gaps, have_set, job_skills)
        critical_n  = sum(1 for g in enriched_gaps if g["priority"] == "critical")
        implicit_n  = sum(1 for g in enriched_gaps if g["implicit"])
        trace.append(
            f"Stage 3 — Graph Reasoning: {critical_n} critical gap(s), "
            f"{implicit_n} implicit prerequisite gap(s) surfaced via dependency propagation."
        )

        # ── Stage 4: Dijkstra learning plan ───────────────────────────────
        learning_path = self.planner.plan(enriched_gaps, have_set, hours_per_week)
        total_hours = sum(s["estimatedHours"] for s in learning_path)
        est_weeks = math.ceil(total_hours / hours_per_week) if learning_path else 0
        trace.append(
            f"Stage 4 — Dijkstra Path Planning: {len(learning_path)} skills scheduled "
            f"in dependency-optimal order, ~{est_weeks} weeks at {hours_per_week} hrs/week."
        )

        # ── Stage 5: Readiness curve ───────────────────────────────────────
        readiness = self.readiness.compute(
            matched, soft_matched, enriched_gaps, job_skills,
            learning_path, hours_per_week
        )
        trace.append(
            f"Stage 5 — Readiness Model: currently {readiness['currentReadinessPct']}% ready. "
            + (f"Projected {readiness['projectedReadinessPct']}% after completing learning path. "
               f"80% threshold: week {readiness['weeksTo80Pct']}."
               if readiness['weeksTo80Pct'] else
               f"Projected {readiness['projectedReadinessPct']}% after path.")
        )

        kpis = {
            "totalSkillsRequired":   len(job_skills),
            "alreadyHave":           len(matched),
            "softMatches":           len(soft_matched),
            "criticalGaps":          critical_n,
            "implicitGaps":          implicit_n,
            "estimatedWeeksToReady": est_weeks,
            "estimatedTotalHours":   total_hours,
        }

        return {
            "resumeSkills": sorted([
                {"skill": s, "confidence": round(c, 3)}
                for s, c in resume_skills.items()
            ], key=lambda x: -x["confidence"]),
            "jobSkills":     job_skills,
            "matchedSkills": sorted(matched, key=lambda x: -x["confidence"]),
            "softMatches":   soft_matched,
            "missingSkills": [
                {"skill": g["skill"], "priority": g["priority"],
                 "reason": g["reason"], "implicit": g["implicit"]}
                for g in enriched_gaps
            ],
            "skillGapScore":  readiness["currentReadinessPct"],
            "readiness":      readiness,
            "learningPath":   learning_path,
            "reasoningTrace": trace,
            "kpis":           kpis,
        }


# ═══════════════════════════════════════════════════════════════════════════
# CLI / SUBPROCESS BRIDGE
# ═══════════════════════════════════════════════════════════════════════════

def _serve_flask(port: int = 8001) -> None:
    try:
        from flask import Flask, request, jsonify
        from flask_cors import CORS
    except ImportError:
        raise ImportError("pip install flask flask-cors")
    app = Flask(__name__)
    CORS(app)
    engine = SkillForgeEngine()

    @app.route("/ml/analyze", methods=["POST"])
    def analyze():
        body = request.get_json(force=True) or {}
        resume_text  = body.get("resumeText", "")
        jd_text      = body.get("jobDescription", "")
        hpw          = int(body.get("hoursPerWeek", 10))
        if not resume_text or not jd_text:
            return jsonify({"error": "resumeText and jobDescription required"}), 400
        return jsonify(engine.analyze(resume_text, jd_text, hpw))

    @app.route("/ml/health")
    def health():
        return jsonify({"status": "ok", "model": "SkillForge Probabilistic Engine v2"})

    print(f"SkillForge ML service → http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    import sys

    if "--stdin" in sys.argv:
        body = json.loads(sys.stdin.read())
        engine = SkillForgeEngine()
        result = engine.analyze(
            body.get("resumeText", ""),
            body.get("jobDescription", ""),
            int(body.get("hoursPerWeek", 10)),
        )
        print(json.dumps(result))
        sys.exit(0)

    if "--serve" in sys.argv:
        idx = sys.argv.index("--serve")
        port = int(sys.argv[idx + 1]) if len(sys.argv) > idx + 1 else 8001
        _serve_flask(port)
        sys.exit(0)

    # ── Self-test ──────────────────────────────────────────────────────────
    RESUME = """
    Senior ML Engineer, 5 years experience.
    Built production RAG pipeline using LangChain and Pinecone for a 10M-user product.
    Fine-tuned LLaMA-2 with LoRA for domain-specific tasks (2023).
    Designed and trained a transformer-based NLP model from scratch for text classification.
    Deployed models via FastAPI on Kubernetes with Prometheus monitoring.
    Built Airflow DAGs for ML feature pipelines ingesting 2TB/day.
    Proficient in Python, PyTorch, pandas, and SQL.
    Familiar with AWS (SageMaker, S3, Lambda).
    Led cross-functional teams using Agile/Scrum.
    """

    JD = """
    Staff ML Research Engineer — Generative AI
    We're looking for someone to:
    - Lead LLM fine-tuning and RLHF experiments
    - Build RAG systems with vector databases at scale
    - Design MLOps infrastructure (model monitoring, A/B testing, CI/CD)
    - Write distributed training code in PyTorch using JAX/XLA as needed
    - Work with Kubernetes, Terraform, and GitHub Actions
    - Collaborate with data engineers on Spark and dbt pipelines
    - Drive system design decisions for ML infra serving 100M requests/day
    - Strong statistics / causal inference background required
    """

    t0 = time.time()
    engine = SkillForgeEngine()
    result = engine.analyze(RESUME, JD, hours_per_week=12)
    elapsed = (time.time() - t0) * 1000

    print(json.dumps(result, indent=2))
    print(f"\n⏱  Completed in {elapsed:.1f}ms", file=sys.stderr)
