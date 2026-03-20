# SkillForge AI

SkillForge AI is a full-stack AI-powered onboarding platform that compares resume skills with job requirements, identifies skill gaps, and generates a personalized learning path using a probabilistic ML engine.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React + Vite + Tailwind CSS |
| **Backend** | Node.js + Express + MongoDB (Mongoose) |
| **Auth** | JWT + bcrypt |
| **ML Engine** | Python 3.10+ · asyncio · probabilistic inference |
| **ML (HTTP mode)** | Flask + flask-cors *(optional)* |

## ML Engine Architecture

The `ml/` directory contains a custom **Probabilistic Skill Intelligence Engine** — not a keyword matcher, but a 5-stage inference pipeline:

```
Resume Text + JD Text
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ Stage 1 — Bayesian Skill Extractor                      │
│  Direct alias matching + 30+ implication rules          │
│  "built attention mechanism" → P(deep_learning)=0.95    │
│  Temporal decay: mentions from 2019 get lower confidence│
└───────────────────────┬─────────────────────────────────┘
                        │ {skill: confidence} dicts
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Stage 2 — Probabilistic Skill Comparator                │
│  Matched ≥ 0.55, Soft match 0.25–0.55, Gap < 0.25      │
└───────────────────────┬─────────────────────────────────┘
                        │ raw + soft gaps
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Stage 3 — Graph Reasoner (BFS over prereq DAG)          │
│  Surfaces implicit gaps: "you can't learn PyTorch       │
│   without Python" — flags it as blocking                │
│  Assigns priority: critical / high / medium / low       │
└───────────────────────┬─────────────────────────────────┘
                        │ enriched gap list
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Stage 4 — Dijkstra Learning Path Planner                │
│  Minimum-hours path from current skills → job-ready     │
│  Dependency-ordered schedule with curated resources     │
└───────────────────────┬─────────────────────────────────┘
                        │ weekly learning plan
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Stage 5 — Readiness Probability Model                   │
│  P(hire_ready | current state) as a % score             │
│  Weekly forecast: "80% ready by week 14"                │
└─────────────────────────────────────────────────────────┘
```

Results are streamed stage-by-stage via **Server-Sent Events (SSE)** — the frontend renders progressively as each stage completes.

### Daemon Architecture

```
React UI  ←─── SSE stream ───  Express /api/analyze
                                       │
                               Unix socket (Linux/Mac)
                               TCP 127.0.0.1:8001 (Windows)
                                       │
                               ml/daemon.py  ← stays warm
                               (asyncio, LRU-256 cache)
```

The Python daemon starts once and is reused across requests — zero cold-start per analysis.

## Project Structure

```text
SkillForge-AI/
  backend/
    controllers/        # analyzeController.js, authController.js
    models/             # Mongoose schemas (Result, Analysis)
    routes/             # analyze.js (SSE + daemon bridge), auth.js, results.js
    utils/              # auth.js (JWT middleware), parser.js, skills.js
    server.js
  frontend/             # React + Vite app
  ml/
    skill_gap_model.py  # Full ML engine (SkillForgeEngine + all stages)
    daemon.py           # Async streaming daemon server
```

## Prerequisites

- Node.js 18+
- npm 9+
- Python 3.10+
- MongoDB Atlas connection string (or local MongoDB)

## 1) Install Dependencies

```bash
# Node dependencies
cd backend && npm install
cd ../frontend && npm install

# Python ML dependencies (minimal — no heavy ML frameworks required)
pip install flask flask-cors   # only needed for --serve (HTTP) mode
```

> The daemon's core engine (`skill_gap_model.py`) uses only Python standard library modules (`re`, `math`, `json`, `heapq`, `asyncio`, `collections`). No PyTorch/TensorFlow required.

## 2) Configure Environment Variables

Create `backend/.env`:

```env
MONGO_URI=your_mongodb_connection_string
JWT_SECRET=your_strong_random_secret
PORT=5000
```

### ML Environment Variables (optional overrides)

```env
# Transport mode: "unix" (default, Linux/Mac) or "tcp" (Windows-friendly)
SF_MODE=tcp

# Socket path (unix mode only)
SF_SOCKET=/tmp/skillforge.sock

# TCP settings (tcp mode only)
SF_TCP_HOST=127.0.0.1
SF_TCP_PORT=8001

# Absolute path to daemon.py (auto-detected by default)
ML_DAEMON_PATH=/absolute/path/to/ml/daemon.py

# Analysis timeout in ms (default 120000)
SF_TIMEOUT_MS=120000
```

> **Windows users:** Set `SF_MODE=tcp` in `backend/.env`. Unix sockets are not supported on Windows.

## 3) Run the App (Development)

Open **three** terminals.

**Terminal A — Backend (Node.js):**
```bash
cd backend
npm run dev
```

**Terminal B — Frontend (React):**
```bash
cd frontend
npm run dev
```

**Terminal C — ML Daemon (Python):**
```bash
# TCP mode (Windows / cross-platform)
python ml/daemon.py --tcp 8001

# Unix socket mode (Linux / Mac — default)
python ml/daemon.py

# Single-shot stdin mode (debug / fallback — no persistent daemon)
echo '{"resumeText":"...","jobDescription":"...","hoursPerWeek":10}' | python ml/daemon.py --stdin
```

> The Node.js backend **auto-starts** the daemon on the first `/api/analyze` request if it's not already running. You only need Terminal C during development for faster startup or independent testing.

**Access the app:**
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:5000`
- ML daemon health: `http://localhost:5000/api/analyze/health`

## Available Scripts

### Backend
```bash
npm run start   # production
npm run dev     # nodemon dev server
```

### Frontend
```bash
npm run dev
npm run build
npm run preview
npm run lint
```

### ML Engine (standalone)
```bash
# Self-test with built-in sample resume + JD
python ml/skill_gap_model.py

# HTTP server mode (exposes /ml/analyze and /ml/health)
python ml/skill_gap_model.py --serve 8001

# Persistent async daemon (TCP)
python ml/daemon.py --tcp 8001
```

## Core Features

- Premium landing page UI with animated components
- Login/Signup authentication (JWT)
- Dashboard, History, Profile pages
- Resume + Job Description upload flow
- AI analysis loading screen with live stage progress (SSE)
- Results dashboard:
  - Skill comparison (matched / soft-matched / gap)
  - Skill gap KPIs with priority breakdown (critical / high / medium)
  - Dependency-optimal learning path timeline with curated resources
  - Hire-readiness probability curve (weekly forecast)
  - Reasoning trace (5-stage audit log)
  - Download / Save actions

## API Endpoints

| Method | Endpoint | Description |
|--------|---------|-------------|
| `POST` | `/api/auth/signup` | Register a new user |
| `POST` | `/api/auth/login` | Login and receive JWT |
| `POST` | `/api/analyze` | Run skill gap analysis (SSE or JSON) |
| `GET`  | `/api/analyze/health` | Daemon status + PID |
| `GET`  | `/api/results/:id` | Fetch saved analysis by ID |

### POST /api/analyze

**Request headers:**
- `Accept: text/event-stream` → streamed SSE response (recommended)
- `Accept: application/json` → blocking JSON response (fallback)

**Request body:**
```json
{
  "resumeText": "...",
  "jobDescription": "...",
  "hoursPerWeek": 10
}
```

**SSE event stream:**
```
event: connected   → { requestId }
event: stage       → { stage: 1..4, label, data, ms }
event: complete    → { id, matchedSkills, missingSkills, learningPath, readiness, kpis, ... }
event: done        → {}
```

## Troubleshooting

### ML Daemon won't start

1. Verify Python 3.10+ is installed: `python --version`
2. Ensure `ml/skill_gap_model.py` exists (the daemon imports from it)
3. On Windows, make sure `SF_MODE=tcp` is set in `backend/.env`
4. Check the daemon manually: `python ml/daemon.py --tcp 8001`
5. Look for Python import errors in the backend console (stderr is now logged for tracebacks and errors)

### "ML service unavailable" error on /api/analyze

- The daemon failed to start within 6 seconds
- Check backend console for `[daemon]` error lines
- Try starting the daemon manually (Terminal C above) and retry

### Frontend `npm run dev` exits with code 1

1. Run `npm install` in `frontend/`
2. Ensure backend is running on port 5000
3. Check if port 5173 is already in use
4. Verify build syntax: `npm run build`

### MongoDB connection errors

- Verify `MONGO_URI` in `backend/.env`
- Ensure your IP is allowed in MongoDB Atlas Network Access
- Ensure DB user credentials are valid

## Security Notes

- **Never** commit real credentials to GitHub
- Keep `backend/.env` private (already in `.gitignore`)
- Set a strong `JWT_SECRET` environment variable — the `"secret"` fallback is for local development only; **it must be overridden in production**
- The ML daemon binds to `127.0.0.1` only (not publicly accessible)

## Demo Flow

1. Open landing page → Login or Sign Up
2. Start new analysis
3. Upload resume text + job description
4. Watch real-time stage progress (SSE)
5. View generated results: skill comparison, gap KPIs, learning path, readiness curve
6. Save analysis and review in History
