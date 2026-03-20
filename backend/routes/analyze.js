/**
 * SkillForge AI — ML Integration Adapter
 * =======================================
 * Drop this file into  backend/routes/analyze.js
 * (or import it alongside the existing file and swap the handler)
 *
 * TWO integration modes — choose one:
 *
 *   MODE A: Python subprocess  (zero extra infra, recommended for dev)
 *     → calls skill_gap_model.py directly via child_process.spawn
 *     → works out-of-the-box if Python 3.8+ is on the same machine
 *
 *   MODE B: Python microservice (recommended for production / Docker)
 *     → calls the Flask server started with `python skill_gap_model.py --serve`
 *     → set ML_SERVICE_URL env var, e.g. http://ml-service:8001
 *
 * Set MODE = "subprocess" | "service" in your .env (default: subprocess)
 */

const express  = require("express");
const router   = express.Router();
const { spawn } = require("child_process");
const path     = require("path");
const fetch    = require("node-fetch");          // already in most Node 18+ projects
const Result   = require("../models/Result");    // your existing Mongoose model

// ── Config ────────────────────────────────────────────────────────────────
const MODE           = process.env.ML_MODE         || "subprocess";
const ML_SERVICE_URL = process.env.ML_SERVICE_URL  || "http://localhost:8001";
const ML_SCRIPT      = process.env.ML_SCRIPT_PATH  ||
  path.join(__dirname, "../../ml/skill_gap_model.py");

// ── Helpers ───────────────────────────────────────────────────────────────

/**
 * MODE A — run the Python script as a subprocess.
 * Passes payload via stdin; reads JSON from stdout.
 */
function callPythonSubprocess(payload) {
  return new Promise((resolve, reject) => {
    const py = spawn("python3", [ML_SCRIPT, "--stdin"]);
    let stdout = "";
    let stderr = "";

    py.stdout.on("data", (d) => (stdout += d.toString()));
    py.stderr.on("data", (d) => (stderr += d.toString()));

    py.on("close", (code) => {
      if (code !== 0) {
        return reject(new Error(`ML subprocess exited ${code}: ${stderr}`));
      }
      try {
        resolve(JSON.parse(stdout));
      } catch (e) {
        reject(new Error(`ML output parse error: ${e.message}\nRaw: ${stdout}`));
      }
    });

    py.stdin.write(JSON.stringify(payload));
    py.stdin.end();
  });
}

/**
 * MODE B — HTTP call to the standalone Flask microservice.
 */
async function callMicroservice(payload) {
  const res = await fetch(`${ML_SERVICE_URL}/ml/analyze`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`ML service error ${res.status}: ${text}`);
  }
  return res.json();
}

/**
 * Unified dispatcher — picks the right mode automatically.
 */
async function runMLModel(resumeText, jobDescription, hoursPerWeek = 10) {
  const payload = { resumeText, jobDescription, hoursPerWeek };
  if (MODE === "service") {
    return callMicroservice(payload);
  }
  return callPythonSubprocess(payload);
}

// ── Route ─────────────────────────────────────────────────────────────────

router.post("/", async (req, res) => {
  try {
    const { resumeText, jobDescription, hoursPerWeek } = req.body;

    if (!resumeText || !jobDescription) {
      return res.status(400).json({
        error: "Both resumeText and jobDescription are required.",
      });
    }

    // ── Call ML model ──────────────────────────────────────────────────────
    const mlResult = await runMLModel(
      resumeText,
      jobDescription,
      hoursPerWeek || 10
    );

    // ── Persist to MongoDB (your existing schema) ──────────────────────────
    const saved = await Result.create({
      resumeText,
      jobDescription,
      ...mlResult,
      createdAt: new Date(),
    });

    return res.status(200).json({ id: saved._id, ...mlResult });

  } catch (err) {
    console.error("[analyze] error:", err.message);
    return res.status(500).json({ error: "ML analysis failed.", detail: err.message });
  }
});

module.exports = router;
