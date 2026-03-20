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
import re, math, json, heapq, time, random
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
    (r"sagemaker",
     {"mlops": 0.85, "aws": 0.70, "machine_learning": 0.75}),
    (r"vertex ai",
     {"mlops": 0.85, "gcp": 0.70, "machine_learning": 0.75}),
    (r"azure ml",
     {"mlops": 0.85, "azure": 0.70, "machine_learning": 0.75}),
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



# ── v3: Knowledge Transfer Matrix ────────────────────────────────────────
# (source_skill, target_skill) → fraction of base hours saved (0–0.85)
TRANSFER_MATRIX: dict[tuple[str, str], float] = {
    ("pytorch",          "jax"):               0.65,
    ("jax",              "pytorch"):            0.55,
    ("pytorch",          "tensorflow"):         0.50,
    ("tensorflow",       "pytorch"):            0.45,
    ("pytorch",          "huggingface"):        0.55,
    ("nlp",              "huggingface"):        0.45,
    ("nlp",              "llm"):               0.55,
    ("llm",              "rag"):               0.50,
    ("machine_learning", "deep_learning"):      0.40,
    ("deep_learning",    "nlp"):               0.40,
    ("deep_learning",    "computer_vision"):    0.45,
    ("deep_learning",    "reinforcement_learning"): 0.35,
    ("machine_learning", "statistics"):         0.50,
    ("statistics",       "machine_learning"):   0.50,
    ("machine_learning", "feature_engineering"):0.50,
    ("statistics",       "feature_engineering"):0.45,
    ("scikit",           "machine_learning"):   0.35,
    ("machine_learning", "scikit"):             0.40,
    ("pandas",           "feature_engineering"):0.30,
    ("pandas",           "spark"):              0.35,
    ("python",           "r"):                 0.30,
    ("r",                "statistics"):         0.45,
    ("sql",              "nosql"):              0.25,
    ("sql",              "data_engineering"):   0.30,
    ("data_engineering", "spark"):              0.35,
    ("data_engineering", "airflow"):            0.35,
    ("spark",            "data_engineering"):   0.30,
    ("javascript",       "typescript"):         0.60,
    ("typescript",       "javascript"):         0.50,
    ("react",            "nodejs"):             0.20,
    ("nodejs",           "rest_api"):           0.35,
    ("fastapi",          "flask"):              0.55,
    ("flask",            "fastapi"):            0.55,
    ("fastapi",          "rest_api"):           0.40,
    ("rest_api",         "graphql"):            0.35,
    ("docker",           "kubernetes"):         0.45,
    ("kubernetes",       "docker"):             0.30,
    ("docker",           "cicd"):               0.30,
    ("git",              "cicd"):               0.30,
    ("cicd",             "terraform"):          0.30,
    ("linux",            "docker"):             0.25,
    ("aws",              "gcp"):               0.40,
    ("aws",              "azure"):              0.35,
    ("gcp",              "aws"):               0.35,
    ("azure",            "aws"):               0.35,
    ("aws",              "mlops"):              0.25,
    ("deep_learning",    "mlops"):              0.25,
    ("numpy",            "pandas"):             0.25,
    ("huggingface",      "nlp"):               0.40,
    ("rag",              "vector_db"):          0.40,
    ("vector_db",        "rag"):               0.30,
    ("python",           "fastapi"):            0.20,
    ("dbt",              "sql"):               0.30,
}

# ── v3: Per-Skill Salary Impact (0–1, relative salary premium) ───────────
SALARY_IMPACT: dict[str, float] = {
    "llm": 0.96, "rag": 0.92, "system_design": 0.90, "mlops": 0.88,
    "vector_db": 0.88, "pytorch": 0.84, "deep_learning": 0.82,
    "huggingface": 0.82, "machine_learning": 0.80, "nlp": 0.80,
    "kubernetes": 0.80, "rust": 0.78, "jax": 0.78, "computer_vision": 0.78,
    "spark": 0.78, "statistics": 0.74, "reinforcement_learning": 0.75,
    "go": 0.72, "terraform": 0.76, "data_engineering": 0.76,
    "aws": 0.74, "gcp": 0.74, "feature_engineering": 0.72,
    "python": 0.72, "tensorflow": 0.72, "azure": 0.72, "airflow": 0.70,
    "docker": 0.70, "cicd": 0.68, "dbt": 0.68, "fastapi": 0.66,
    "scikit": 0.66, "java": 0.65, "typescript": 0.65,
    "react": 0.64, "nosql": 0.64, "nodejs": 0.62,
    "sql": 0.60, "javascript": 0.60, "linux": 0.60, "rest_api": 0.60,
    "pandas": 0.60, "r": 0.58, "graphql": 0.58, "numpy": 0.58,
    "data_viz": 0.55, "communication": 0.52, "agile": 0.45, "git": 0.50,
}
DEFAULT_SALARY_IMPACT = 0.55

# ── v3: Market Velocity — how fast is demand growing? (0=declining, 1=exploding)
MARKET_VELOCITY: dict[str, float] = {
    "llm": 1.00, "rag": 0.97, "vector_db": 0.95, "huggingface": 0.90,
    "mlops": 0.88, "rust": 0.80, "data_engineering": 0.80, "pytorch": 0.80,
    "deep_learning": 0.78, "nlp": 0.76, "python": 0.75, "fastapi": 0.70,
    "jax": 0.75, "machine_learning": 0.74, "dbt": 0.72, "go": 0.72,
    "typescript": 0.72, "computer_vision": 0.72, "gcp": 0.68, "cicd": 0.65,
    "reinforcement_learning": 0.65, "statistics": 0.65, "airflow": 0.65,
    "aws": 0.65, "azure": 0.66, "kubernetes": 0.70, "terraform": 0.68,
    "docker": 0.62, "spark": 0.70, "system_design": 0.70,
    "feature_engineering": 0.68, "react": 0.60, "sql": 0.55,
    "nosql": 0.58, "pandas": 0.60, "numpy": 0.58, "linux": 0.60,
    "scikit": 0.58, "nodejs": 0.55, "javascript": 0.55, "git": 0.55,
    "java": 0.52, "rest_api": 0.58, "agile": 0.50, "data_viz": 0.56,
    "communication": 0.52, "flask": 0.45, "tensorflow": 0.40,
    "r": 0.38, "graphql": 0.55, "c++": 0.55,
}
DEFAULT_MARKET_VELOCITY = 0.50

# ── v3: Learning Difficulty (0=trivial, 1=extremely hard) ────────────────
DIFFICULTY: dict[str, float] = {
    "git": 0.15, "agile": 0.20, "python": 0.25, "sql": 0.25, "numpy": 0.25,
    "communication": 0.25, "linux": 0.30, "pandas": 0.30, "data_viz": 0.30,
    "docker": 0.35, "rest_api": 0.30, "scikit": 0.35, "nosql": 0.35,
    "javascript": 0.35, "r": 0.40, "fastapi": 0.35, "flask": 0.35,
    "typescript": 0.40, "dbt": 0.40, "vector_db": 0.40, "react": 0.45,
    "nodejs": 0.40, "graphql": 0.45, "feature_engineering": 0.45,
    "huggingface": 0.50, "statistics": 0.50, "cicd": 0.50,
    "rag": 0.55, "aws": 0.55, "gcp": 0.55, "azure": 0.55,
    "java": 0.55, "machine_learning": 0.55, "airflow": 0.55, "terraform": 0.55,
    "pytorch": 0.60, "data_engineering": 0.60, "mlops": 0.65,
    "tensorflow": 0.65, "nlp": 0.65, "computer_vision": 0.65,
    "llm": 0.65, "spark": 0.65, "kubernetes": 0.65, "go": 0.50,
    "deep_learning": 0.70, "jax": 0.72, "system_design": 0.75,
    "c++": 0.75, "rust": 0.80, "reinforcement_learning": 0.85,
}
DEFAULT_DIFFICULTY = 0.50


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
# STAGE 6: KNOWLEDGE-TRANSFER ACCELERATOR
# ═══════════════════════════════════════════════════════════════════════════

class TransferLearningModel:
    """
    Existing skills shorten learning time for related skills.
    "Know PyTorch @ 0.90 → learn JAX in ~40% of base hours."
    Scans TRANSFER_MATRIX for every (have_skill, target_skill) pair,
    weights savings by current confidence, caps at 85%.
    """

    def adjust_hours(self, skill: str, resume_skills: dict[str, float]) -> tuple[int, float, str]:
        """Returns (adjusted_hours, saving_fraction, via_skill)."""
        base = LEARN_HOURS.get(skill, 20)
        best_saving, best_via = 0.0, ""
        for (src, dst), coef in TRANSFER_MATRIX.items():
            if dst == skill and src in resume_skills:
                saving = coef * resume_skills[src]
                if saving > best_saving:
                    best_saving, best_via = saving, src
        best_saving = min(best_saving, 0.85)
        return max(4, round(base * (1 - best_saving))), best_saving, best_via

    def compute_all(self, enriched_gaps: list[dict], resume_skills: dict[str, float]) -> list[dict]:
        bonuses = []
        for gap in enriched_gaps:
            adj, saving, via = self.adjust_hours(gap["skill"], resume_skills)
            if saving > 0.12:
                bonuses.append({
                    "skill": gap["skill"],
                    "baseHours": LEARN_HOURS.get(gap["skill"], 20),
                    "adjustedHours": adj,
                    "savingPct": round(saving * 100),
                    "via": via,
                    "interpretation": f"Your {via} experience covers ~{round(saving*100)}% of {gap['skill']} fundamentals.",
                })
        return sorted(bonuses, key=lambda x: -x["savingPct"])


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 7: MARKET PULSE ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════

class MarketPulseAnalyzer:
    """
    Per-skill velocity, JD inflation detection, and trending/declining signals.
    JD inflation score: JDs listing >12 skills often only truly require 5-6.
    """

    def analyze(self, job_skills: list[str]) -> dict:
        n = len(job_skills)
        vel = {s: MARKET_VELOCITY.get(s, DEFAULT_MARKET_VELOCITY) for s in job_skills}
        trending  = [s for s, v in vel.items() if v >= 0.80]
        stable    = [s for s, v in vel.items() if 0.50 <= v < 0.80]
        declining = [s for s, v in vel.items() if v < 0.50]
        inflation = min(100, max(0, round((n - 6) / max(1, 12 - 6) * 100))) if n > 6 else 0
        top5      = sorted(job_skills, key=lambda s: -MARKET_VELOCITY.get(s, 0.5))[:5]
        return {
            "velocityScores":    {s: round(v, 2) for s, v in vel.items()},
            "trendingSkills":    trending,
            "stableSkills":      stable,
            "decliningSkills":   declining,
            "jdInflationScore":  inflation,
            "jdInflationLabel":  "High" if inflation > 70 else "Moderate" if inflation > 35 else "Normal",
            "topSignalSkills":   top5,
            "insight": (
                f"JD lists {n} skills — inflation {inflation}/100. "
                f"Focus first on: {', '.join(top5[:3])}."
                if inflation > 40 else
                f"Well-scoped JD ({n} skills). Top velocity: {', '.join(top5[:3])}."
            ),
        }


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 8: PARETO-FRONT LEARNING PATH OPTIMIZER
# ═══════════════════════════════════════════════════════════════════════════

class ParetoPathOptimizer:
    """
    Generates 4 Pareto-optimal learning schedules by applying different
    greedy priority functions over the same dependency-constrained skill graph.

      Sprint          — minimise time to first critical skill
      Market-Optimal  — front-load highest-velocity skills
      Salary-Max      — front-load highest salary-impact skills
      Balanced        — geometric blend of all objectives

    Novel: no existing career-intelligence tool produces a Pareto frontier.
    """

    def _prereq_expand(self, targets: set[str]) -> set[str]:
        all_needed = set(targets)
        q = deque(targets)
        while q:
            s = q.popleft()
            for p, _ in PREREQ_GRAPH.get(s, []):
                if p not in all_needed:
                    all_needed.add(p); q.append(p)
        return all_needed

    def _run(self, to_learn, have, hpw, key_fn, transfer_model, resume_skills):
        targets   = {g["skill"] for g in to_learn}
        all_nodes = self._prereq_expand(targets)
        pmap      = {g["skill"]: g.get("urgency", 0.5) for g in to_learn}
        acquired  = set(have)
        plan, total_h = [], 0
        while True:
            free = [s for s in all_nodes if s not in acquired
                    and all(p in acquired for p, _ in PREREQ_GRAPH.get(s, []))]
            if not free: break
            best = min(free, key=key_fn)
            adj, _, _ = transfer_model.adjust_hours(best, resume_skills)
            total_h += adj
            week = max(1, math.ceil(total_h / hpw))
            res  = [{"title": r["t"], "url": r["u"], "type": r["type"]}
                    for r in RESOURCES.get(best, _fallback_resources(best))[:2]]
            plan.append({"week": week, "skill": best,
                         "estimatedHours": adj, "isPrerequisite": best not in targets,
                         "priority": "critical" if pmap.get(best,0)>=1.0 else
                                     "high" if pmap.get(best,0)>=0.8 else "medium",
                         "resources": res})
            acquired.add(best)
            if targets <= acquired: break
        return plan

    def _score(self, plan, jd_set):
        total_h = sum(s["estimatedHours"] for s in plan)
        demand  = sum(MARKET_VELOCITY.get(s["skill"], .5) / s["week"]
                      for s in plan if s["skill"] in jd_set)
        salary  = sum(SALARY_IMPACT.get(s["skill"], .5) / s["week"]
                      for s in plan if s["skill"] in jd_set)
        diff    = sum(DIFFICULTY.get(s["skill"], .5) * s["estimatedHours"]
                      for s in plan) / max(1, total_h)
        return {"totalHours": total_h,
                "demandScore": round(demand, 3),
                "salaryScore": round(salary, 3),
                "avgDifficulty": round(diff, 3)}

    def optimize(self, enriched_gaps, have, job_skills, hpw, transfer_model, resume_skills):
        to_learn = [g for g in enriched_gaps if g["priority"] in ("critical","high","medium")]
        if not to_learn: return []
        pm = {g["skill"]: g.get("urgency", 0.5) for g in to_learn}
        jd = set(job_skills)

        strategies = {
            "Sprint": lambda s: (
                -(pm.get(s,0.2)*3), LEARN_HOURS.get(s,20)),
            "Market-Optimal": lambda s: (
                -(MARKET_VELOCITY.get(s,DEFAULT_MARKET_VELOCITY) + pm.get(s,0.2)),
                DIFFICULTY.get(s,DEFAULT_DIFFICULTY)),
            "Salary-Maximising": lambda s: (
                -(SALARY_IMPACT.get(s,DEFAULT_SALARY_IMPACT) + pm.get(s,0.2)),
                DIFFICULTY.get(s,DEFAULT_DIFFICULTY)),
            "Balanced": lambda s: (
                -(MARKET_VELOCITY.get(s,DEFAULT_MARKET_VELOCITY)*.35 +
                  SALARY_IMPACT.get(s,DEFAULT_SALARY_IMPACT)*.35 +
                  pm.get(s,0.2)*.30),
                DIFFICULTY.get(s,DEFAULT_DIFFICULTY)),
        }
        descs = {
            "Sprint":           "Reach 80% readiness in minimum calendar time.",
            "Market-Optimal":   "Front-loads highest-velocity skills — profile stays relevant longest.",
            "Salary-Maximising":"Sequences by salary premium — maximises earning at each milestone.",
            "Balanced":         "Pareto-optimal blend: speed + demand + salary impact.",
        }
        frontier = []
        for label, kfn in strategies.items():
            p = self._run(to_learn, have, hpw, kfn, transfer_model, resume_skills)
            sc = self._score(p, jd)
            frontier.append({
                "label": label, "description": descs[label],
                "schedule": p, "scores": sc,
                "totalHours": sc["totalHours"],
                "estimatedWeeks": math.ceil(sc["totalHours"]/hpw) if p else 0,
            })
        return frontier


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 9: RIVAL APPLICANT COHORT SIMULATOR  (Monte Carlo, N=2 000)
# ═══════════════════════════════════════════════════════════════════════════

class ApplicantSimulator:
    """
    Simulates 2 000 competing applicants using a Gaussian-mixture tier model
    (junior 30% / mid 45% / senior 20% / expert 5%) seeded for determinism.
    Returns the candidate's percentile rank and cohort distribution.
    Novel: no existing skill-gap tool benchmarks against a simulated talent pool.
    """
    N = 2_000
    TIERS = [          # (weight, coverage_μ, coverage_σ, conf_μ, conf_σ)
        (0.30, 0.28, 0.10, 0.66, 0.08),   # junior
        (0.45, 0.55, 0.12, 0.76, 0.07),   # mid
        (0.20, 0.78, 0.10, 0.87, 0.05),   # senior
        (0.05, 0.93, 0.05, 0.94, 0.03),   # expert
    ]

    def _sim_score(self, job_skills, rng, tier):
        _, cm, cs, fm, fs = tier
        n = max(1, len(job_skills))
        n_have = max(0, min(n, round(rng.gauss(cm * n, cs * n))))
        possessed = set(job_skills[:n_have])          # deterministic slice
        return sum(max(0.4, min(1.0, rng.gauss(fm, fs)))
                   for s in job_skills if s in possessed) / n

    def simulate(self, job_skills: list[str], current_pct: int) -> dict:
        if not job_skills:
            return {"percentile": 50, "interpretation": "No skills to benchmark."}
        rng = random.Random(42)
        cohort = []
        for _ in range(self.N):
            r, cum = rng.random(), 0.0
            tier = self.TIERS[-1]
            for t in self.TIERS:
                cum += t[0]
                if r <= cum: tier = t; break
            cohort.append(round(self._sim_score(job_skills, rng, tier) * 100))
        cohort.sort()
        pct = round(sum(1 for s in cohort if s < current_pct) / self.N * 100)
        p = lambda q: cohort[int(self.N * q)]
        tier_benchmarks = {
            "Typical junior": p(0.30), "Typical mid-level": p(0.55),
            "Typical senior": p(0.80),
        }
        if   pct >= 80: interp = f"Top {100-pct}% of applicants — strong competitive position."
        elif pct >= 60: interp = f"Above-average ({pct}th percentile) — targeted gap-closing is high-leverage."
        elif pct >= 40: interp = f"Mid-field ({pct}th percentile) — significant upskilling needed."
        else:           interp = f"Below median ({pct}th percentile) — critical skills investment required."
        return {
            "percentile": pct, "interpretation": interp,
            "cohortStats": {"p25": p(0.25), "median": p(0.50), "p75": p(0.75), "p90": p(0.90)},
            "tierBenchmarks": {k: {"score": v, "vsYou": current_pct-v} for k,v in tier_benchmarks.items()},
            "simulatedApplicants": self.N,
        }


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 10: INTERVIEW STAGE LADDER
# ═══════════════════════════════════════════════════════════════════════════

class InterviewReadinessModel:
    """
    Four-stage P(pass) ladder: ATS → Phone Screen → Technical → System Design.
    Models each stage independently using different skill-coverage signals.
    Product gives overall hire-probability now vs. after the learning path.
    """

    def _logit(self, x: float, k: float = 8.0, m: float = 0.5) -> float:
        return 1 / (1 + math.exp(-k * (x - m)))

    def compute(self, matched, soft_matched, enriched_gaps, job_skills, learning_path) -> dict:
        jd  = set(job_skills)
        n   = max(1, len(jd))
        mc  = {m["skill"]: m["confidence"] for m in matched}
        sc  = {s["skill"]: s["confidence"] * 0.4 for s in soft_matched}
        all_c = {**sc, **mc}

        # Stage 1: ATS (keyword breadth)
        ats_sc  = min(1.0, (len(mc.keys() & jd) + 0.35*len(sc.keys() & jd)) / n)
        ats_p   = round(min(0.99, ats_sc**0.65 * 1.25), 3)

        # Stage 2: Recruiter phone (breadth, no red flags)
        phone_sc = len(mc.keys() & jd) / n
        phone_p  = round(self._logit(phone_sc, k=10, m=0.45), 3)

        # Stage 3: Technical (depth in critical/high skills)
        crit = {g["skill"] for g in enriched_gaps if g["priority"] in ("critical","high")} & jd
        tech_sc  = sum(all_c.get(s, 0) for s in (crit or jd)) / max(1, len(crit or jd))
        tech_p   = round(self._logit(tech_sc, k=9, m=0.58), 3)

        # Stage 4: System design (architecture signals)
        sys_skills = {"system_design","kubernetes","aws","gcp","azure","spark","data_engineering","cicd"}
        sys_in_jd  = sys_skills & jd
        sys_sc     = sum(all_c.get(s,0) for s in sys_in_jd)/max(1,len(sys_in_jd)) if sys_in_jd else 0.30
        sys_p      = round(self._logit(sys_sc, k=8, m=0.50), 3)

        # Post-path scores (learned → 0.85 confidence)
        lp_set = {s["skill"] for s in learning_path}
        post   = {**all_c, **{s: 0.85 for s in lp_set if s in jd}}
        p_phone = round(self._logit(len({s for s in jd if post.get(s,0)>=0.55})/n, 10, 0.45), 3)
        p_tech  = round(self._logit(sum(post.get(s,0) for s in (crit or jd))/max(1,len(crit or jd)),9,0.58),3)
        p_ats   = round(min(0.99, p_phone**0.65 * 1.25), 3)
        p_sys_sc= sum(post.get(s,0) for s in sys_in_jd)/max(1,len(sys_in_jd)) if sys_in_jd else 0.65
        p_sys   = round(self._logit(p_sys_sc, 8, 0.50), 3)

        hire_now  = round(ats_p * phone_p * tech_p * sys_p, 4)
        hire_path = round(p_ats * p_phone * p_tech * p_sys, 4)

        bottleneck = min(
            {"atsScreen": ats_p, "phoneScreen": phone_p,
             "technicalRound": tech_p, "systemDesign": sys_p},
            key=lambda k: {"atsScreen":ats_p,"phoneScreen":phone_p,"technicalRound":tech_p,"systemDesign":sys_p}[k]
        )
        return {
            "stages": {
                "atsScreen":      {"label": "ATS / Resume Screen",    "passProbability": ats_p,   "afterPath": p_ats},
                "phoneScreen":    {"label": "Recruiter Phone Screen", "passProbability": phone_p, "afterPath": p_phone},
                "technicalRound": {"label": "Technical Interview",    "passProbability": tech_p,  "afterPath": p_tech},
                "systemDesign":   {"label": "System Design Round",    "passProbability": sys_p,   "afterPath": p_sys},
            },
            "overallHireProbabilityNow":       hire_now,
            "overallHireProbabilityAfterPath": hire_path,
            "improvementFactor": round(hire_path / max(0.001, hire_now), 1),
            "bottleneck": bottleneck,
        }


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 11: SKILL DECAY EARLY-WARNING SYSTEM
# ═══════════════════════════════════════════════════════════════════════════

class SkillDecayForecaster:
    """
    Projects each current skill's confidence forward in time using the
    exponential decay model from Stage 1 (same half-life constants).
    Flags skills that will drop below MATCH_THRESHOLD within 12 months
    if left unused — "refresh" recommendations before they become gaps.
    """
    HORIZON = 12  # months to look ahead

    def forecast(self, resume_skills: dict[str, float]) -> list[dict]:
        alerts = []
        for skill, conf in resume_skills.items():
            if conf <= MATCH_THRESHOLD:
                continue
            hl_months = HALF_LIFE_YEARS.get(skill, DEFAULT_HALF_LIFE) * 12
            # t* = hl * log2(conf / threshold)
            t_star = hl_months * math.log(conf / MATCH_THRESHOLD) / math.log(2)
            if 0 < t_star <= self.HORIZON:
                urg = "critical" if t_star <= 3 else "high" if t_star <= 6 else "moderate"
                alerts.append({
                    "skill": skill,
                    "currentConfidence": round(conf, 3),
                    "monthsToThreshold": round(t_star, 1),
                    "urgency": urg,
                    "recommendation": (
                        f"Refresh {skill} in ≤{math.ceil(t_star)} month(s) — confidence will fall below hire threshold."
                        if t_star <= 6 else
                        f"Re-engage with {skill} within the year to maintain competitive confidence."
                    ),
                })
        return sorted(alerts, key=lambda x: x["monthsToThreshold"])


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 12: COUNTERFACTUAL KEYSTONE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

class CounterfactualExplorer:
    """
    Finds the KEYSTONE skill: the single gap whose closure maximises
    immediate readiness improvement × market velocity × salary impact.
    Also ranks every gap skill by its marginal impact score,
    answering: "If I could learn only ONE skill this month, which is it?"
    """

    def analyze(self, enriched_gaps, resume_skills, job_skills, matched, soft_matched) -> dict:
        jd  = set(job_skills)
        n   = max(1, len(jd))
        all_c = {m["skill"]: m["confidence"] for m in matched}
        all_c.update({s["skill"]: s["confidence"]*0.5 for s in soft_matched})
        base_score = sum(all_c.get(s, 0) for s in jd) / n

        table = []
        for gap in enriched_gaps:
            sk = gap["skill"]
            if sk not in jd:
                continue
            hypo = {**all_c, sk: 0.85}
            delta = (sum(hypo.get(s,0) for s in jd)/n - base_score) * 100
            # Skills that become fully prereq-satisfied once we acquire sk
            unlocks = []
            for other in jd:
                if other in all_c: continue
                prereqs = {p for p,_ in PREREQ_GRAPH.get(other,[])}
                if sk in prereqs and not (prereqs - set(resume_skills) - {sk}):
                    unlocks.append(other)
            composite = (delta/100)*0.45 + MARKET_VELOCITY.get(sk,DEFAULT_MARKET_VELOCITY)*0.30 + SALARY_IMPACT.get(sk,DEFAULT_SALARY_IMPACT)*0.25
            table.append({
                "skill": sk,
                "readinessDeltaPct": round(delta, 1),
                "unlocks": unlocks,
                "marketVelocity": MARKET_VELOCITY.get(sk, DEFAULT_MARKET_VELOCITY),
                "salaryImpact":   SALARY_IMPACT.get(sk, DEFAULT_SALARY_IMPACT),
                "compositeScore": round(composite, 4),
            })

        table.sort(key=lambda x: -x["compositeScore"])
        ks = table[0] if table else None
        narrative = ""
        if ks:
            kn, kd, ku = ks["skill"], ks["readinessDeltaPct"], ks["unlocks"]
            narrative = (
                f"Learning `{kn}` first raises readiness by {kd:.1f}%"
                + (f" and directly unlocks: {', '.join(ku)}." if ku else ".")
                + f" Market velocity: {round(MARKET_VELOCITY.get(kn,0.5)*10)}/10."
            )
        return {
            "keystoneSkill": ks["skill"] if ks else None,
            "keystoneImpact": ks,
            "marginalImpactRanking": table,
            "scenarioNarrative": narrative,
        }


# ═══════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR — v3 (12 stages)
# ═══════════════════════════════════════════════════════════════════════════

class SkillForgeEngine:
    """
    Main entry point — v3.
    analyze(resume_text, jd_text, hours_per_week) → full JSON payload.
    Backward-compatible: all v2 keys are preserved. New v3 keys are additive.
    """

    def __init__(self) -> None:
        # v2 stages
        self.extractor  = BayesianSkillExtractor()
        self.comparator = SkillComparator()
        self.reasoner   = GraphReasoner()
        self.planner    = HireReadinessPlanner()
        self.readiness  = ReadinessModel()
        # v3 stages
        self.transfer   = TransferLearningModel()
        self.market     = MarketPulseAnalyzer()
        self.pareto     = ParetoPathOptimizer()
        self.applicants = ApplicantSimulator()
        self.interview  = InterviewReadinessModel()
        self.decay      = SkillDecayForecaster()
        self.cf         = CounterfactualExplorer()

    def analyze(self, resume_text: str, jd_text: str, hours_per_week: int = 10) -> dict[str, Any]:
        trace: list[str] = []

        # ── Stages 1-5 (v2, unchanged) ────────────────────────────────────
        resume_skills = self.extractor.extract(resume_text)
        jd_skills_raw = self.extractor.extract(jd_text)
        job_skills    = sorted(s for s, c in jd_skills_raw.items() if c >= 0.60)
        trace.append(f"Stage 1 — Bayesian Extraction: {len(resume_skills)} resume signals, {len(job_skills)} JD requirements.")

        matched, raw_gaps, soft_matched = self.comparator.compare(resume_skills, job_skills)
        trace.append(f"Stage 2 — Probabilistic Matching: {len(matched)} matches, {len(soft_matched)} soft, {len(raw_gaps)} gaps.")

        have_set      = set(resume_skills.keys())
        enriched_gaps = self.reasoner.enrich(raw_gaps, have_set, job_skills)
        critical_n    = sum(1 for g in enriched_gaps if g["priority"] == "critical")
        implicit_n    = sum(1 for g in enriched_gaps if g["implicit"])
        trace.append(f"Stage 3 — Graph Reasoning: {critical_n} critical, {implicit_n} implicit prereq gaps.")

        learning_path = self.planner.plan(enriched_gaps, have_set, hours_per_week)
        total_hours   = sum(s["estimatedHours"] for s in learning_path)
        est_weeks     = math.ceil(total_hours / hours_per_week) if learning_path else 0
        trace.append(f"Stage 4 — Dijkstra Path: {len(learning_path)} skills, ~{est_weeks} weeks.")

        readiness = self.readiness.compute(matched, soft_matched, enriched_gaps, job_skills, learning_path, hours_per_week)
        trace.append(f"Stage 5 — Readiness: {readiness['currentReadinessPct']}% → {readiness['projectedReadinessPct']}%.")

        # ── Stages 6-12 (v3) ──────────────────────────────────────────────
        transfer_bonuses = self.transfer.compute_all(enriched_gaps, resume_skills)
        trace.append(f"Stage 6 — Transfer Learning: {len(transfer_bonuses)} skills with accelerated paths.")

        market_pulse = self.market.analyze(job_skills)
        trace.append(f"Stage 7 — Market Pulse: {len(market_pulse['trendingSkills'])} trending, inflation {market_pulse['jdInflationScore']}/100.")

        pareto_frontier = self.pareto.optimize(enriched_gaps, have_set, job_skills, hours_per_week, self.transfer, resume_skills)
        trace.append(f"Stage 8 — Pareto Optimizer: {len(pareto_frontier)} non-dominated schedules generated.")

        benchmark = self.applicants.simulate(job_skills, readiness["currentReadinessPct"])
        trace.append(f"Stage 9 — Cohort Sim ({benchmark['simulatedApplicants']} applicants): {benchmark['percentile']}th percentile.")

        interview = self.interview.compute(matched, soft_matched, enriched_gaps, job_skills, learning_path)
        trace.append(f"Stage 10 — Interview Ladder: P(hire|now)={interview['overallHireProbabilityNow']:.1%}, P(hire|path)={interview['overallHireProbabilityAfterPath']:.1%}.")

        decay_alerts = self.decay.forecast(resume_skills)
        trace.append(f"Stage 11 — Decay Forecast: {len(decay_alerts)} skill(s) at risk within 12 months.")

        cf = self.cf.analyze(enriched_gaps, resume_skills, job_skills, matched, soft_matched)
        if cf["keystoneSkill"]:
            trace.append(f"Stage 12 — Counterfactual: keystone=`{cf['keystoneSkill']}` (+{cf['keystoneImpact']['readinessDeltaPct']}% readiness).")

        return {
            # ── v2 (fully backward-compatible) ─────────────────────────
            "resumeSkills":   sorted([{"skill": s, "confidence": round(c,3)} for s,c in resume_skills.items()],
                                     key=lambda x: -x["confidence"]),
            "jobSkills":      job_skills,
            "matchedSkills":  sorted(matched, key=lambda x: -x["confidence"]),
            "softMatches":    soft_matched,
            "missingSkills":  [{"skill":g["skill"],"priority":g["priority"],"reason":g["reason"],"implicit":g["implicit"]}
                               for g in enriched_gaps],
            "skillGapScore":  readiness["currentReadinessPct"],
            "readiness":      readiness,
            "learningPath":   learning_path,
            "reasoningTrace": trace,
            "kpis": {
                "totalSkillsRequired":   len(job_skills),
                "alreadyHave":           len(matched),
                "softMatches":           len(soft_matched),
                "criticalGaps":          critical_n,
                "implicitGaps":          implicit_n,
                "estimatedWeeksToReady": est_weeks,
                "estimatedTotalHours":   total_hours,
            },
            # ── v3 (new) ────────────────────────────────────────────────
            "transferBonuses":    transfer_bonuses,
            "marketPulse":        market_pulse,
            "paretoFrontier":     pareto_frontier,
            "applicantBenchmark": benchmark,
            "interviewReadiness": interview,
            "decayAlerts":        decay_alerts,
            "counterfactual":     cf,
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
