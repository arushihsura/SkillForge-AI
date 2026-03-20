# SkillForge AI

SkillForge AI is a full-stack AI-powered onboarding platform that compares resume skills with job requirements, identifies skill gaps, and generates a personalized learning path.

## Tech Stack

- Frontend: React + Vite + Tailwind CSS
- Backend: Node.js + Express + MongoDB (Mongoose)
- Auth: JWT + bcrypt

## Project Structure

```text
SkillForge/
  backend/
  frontend/
```

## Prerequisites

- Node.js 18+
- npm 9+
- MongoDB Atlas connection string (or local MongoDB)

## 1) Install Dependencies

Run these commands from the project root:

```bash
cd backend
npm install

cd ../frontend
npm install
```

## 2) Configure Environment Variables

Create a file at `backend/.env`:

```env
MONGO_URI=your_mongodb_connection_string
```

Optional (recommended for production):

```env
JWT_SECRET=your_strong_secret
PORT=5000
```

Note: Current backend code uses `"secret"` for JWT in some places. Replace with `process.env.JWT_SECRET` before production use.

## 3) Run the App (Development)

Open two terminals.

Terminal A (backend):

```bash
cd backend
npm run dev
```

Terminal B (frontend):

```bash
cd frontend
npm run dev
```

- Frontend runs on Vite default port (usually 5173)
- Backend runs on port 5000
- Frontend proxy forwards `/api/*` requests to backend

## Available Scripts

### Backend

```bash
npm run start
npm run dev
```

### Frontend

```bash
npm run dev
npm run build
npm run preview
npm run lint
```

## Core Features

- Premium landing page UI with animated components
- Login/Signup authentication
- Dashboard, History, Profile pages
- Resume + Job Description upload flow
- AI analysis loading screen with progress steps
- Results dashboard:
  - Skill comparison
  - Skill gap KPIs and visualization
  - Learning path timeline
  - Reasoning trace
  - Download/Save actions

## API Endpoints (Current)

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/analyze`
- `GET /api/results/:id`

## Troubleshooting

### Frontend `npm run dev` exits with code 1

1. Ensure dependencies are installed in `frontend`:
   - `npm install`
2. Ensure backend is running on port 5000.
3. Check if port 5173 is already in use.
4. Run a build to verify syntax:
   - `npm run build`

### MongoDB connection errors

- Verify `MONGO_URI` in `backend/.env`
- Ensure your IP is allowed in Atlas Network Access
- Ensure DB user credentials are valid

## Security Notes

- Never commit real credentials to GitHub
- Keep `backend/.env` private (already ignored via `.gitignore`)
- Use a strong JWT secret and environment-based configuration for production

## Demo Flow

1. Open landing page
2. Login or sign up
3. Start new analysis
4. Upload resume + JD
5. View generated results and learning path
6. Save analysis and review in History
