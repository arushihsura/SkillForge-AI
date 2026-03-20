# SkillForge AI: Technical Documentation
**Version 3.1.0 — Team ByteWorks — IISc Hackathon 2026**

---

## 📑 Table of Contents
1. [Executive Summary](#executive-summary)
2. [ML Engine Architecture](#ml-engine-architecture)
3. [SHAP & Explainability](#shap--explainability)
4. [Generative AI Integration](#generative-ai-integration)
5. [System Components](#system-components)
6. [Data Models & Schema](#data-models--schema)
7. [Deployment & Scaling](#deployment--scaling)

---

## 1. Executive Summary <a name="executive-summary"></a>
SkillForge AI is a high-performance career intelligence platform that leverages **Bayesian Graph Reasoning** and **SHAP Explainability** to bridge the gap between candidate resumes and job requirements. Unlike typical ATS systems that rely on keyword frequency, SkillForge treats text as evidence for latent skills, allowing for deep inference of implicit abilities.

---

## 2. ML Engine Architecture <a name="ml-engine-architecture"></a>
The core of SkillForge is a **13-stage inference pipeline** implemented in Python.

### The Pipeline Stages:
1. **Bayesian Extractor**: Uses 300+ rules to infer skills (e.g., "Transformer" → `P(Deep Learning|Transformer) = 0.98`).
2. **Probabilistic Matcher**: Calculates a distance metric between resume evidence and JD requirements.
3. **Graph Reasoner**: Identifies prerequisites and implicit skill relationships.
4. **Dijkstra Path Planner**: Optimizes the learning sequence to minimize "Time-to-Hired."
5. **Readiness Model**: Forecasts current and future readiness percentages.
6. **Transfer Accelerator**: Identifies cross-domain skill overlaps (e.g., Python → Ruby).
7. **Market Pulse Analytics**: Injects real-time demand data and salary trends.
8. **Pareto Optimizer**: Generates optimal schedules (Sprint vs. Balanced).
9. **Applicant Simulator**: Benchmarks the user against 2,000 synthetic candidates.
10. **Interview Ladder**: Predicts passing probability for different interview stages.
11. **Decay Forecaster**: Simulates skill retention over time.
12. **Counterfactual Analysis**: "What if I learned X instead of Y?"
13. **SHAP Stage**: Calculates feature importance for the final score.

---

## 3. SHAP & Explainability <a name="shap--explainability"></a>
To ensure AI transparency, we integrated **SHAP (SHapley Additive exPlanations)**.
- **Method**: We use `shap.KernelExplainer` to simulate a black-box model of the readiness score.
- **Output**: A dictionary of `shapValues` mapping skills to their percentage impact on the final score.
- **Visualization**: Frontend renders horizontal bars showing positive (Accent) and negative (Rose) contributions.

---

## 4. Generative AI Integration <a name="generative-ai-integration"></a>
Powered by **Google Gemini 1.5 Flash**, SkillForge provides two humanized AI layers:

### A. Skill Gap Questionnaire
- **Trigger**: Activated from the "Improve Your Profile" section.
- **Logic**: Backend passes the top 5 `missingSkills` and the `jobDescription` to Gemini.
- **Output**: 15 high-fidelity technical and behavioral questions designed to test and teach the user's gaps.

### B. ByteWorks Career Coach (AIChatbot)
- **Persona**: Friendly, empathetic, and observant.
- **Sentiment Awareness**: Detects tone (stress/overwhelmed) and provides motivational support.
- **Technical Support**: Can generate code snippets, explain ML stages, and provide roadmap advice.

---

## 5. System Components <a name="system-components"></a>
### Frontend (React 18 + Vite)
- **Design System**: Custom Vanilla CSS with Glassmorphism and CSS variables.
- **Animations**: `framer-motion` for fluid transitions and real-time streaming updates.

### Backend (Node.js ESM)
- **Transport**: Server-Sent Events (SSE) for real-time streaming of the 13 ML stages.
- **Security**: JWT-based authentication and helmet/rate-limit middleware.

---

## 6. Data Models & Schema <a name="data-models--schema"></a>
We utilize a unified **Result Schema** in MongoDB:
- `resumeSkills`: Array of {skill, confidence}
- `missingSkills`: Array of {skill, priority, reason}
- `readiness`: {currentPct, weeklyForecast, weeksTo80}
- `shapValues`: Mapped object of skill impact
- `learningPath`: Structured weekly steps with resources

---

## 7. Deployment & Scaling <a name="deployment--scaling"></a>
- **Local**: Hybrid warm-process via Unix/TCP sockets.
- **Production**: Optimized for **Vercel Serverless**. The ML engine can run in `--stdin` mode to minimize cold-start latency.

---
**Team ByteWorks — IISc Hackathon 2026**
*Arushi Tiwari, Aarya Patankar, Hridaya Vashishtha, Shivani Bhat*
