/**
 * SkillForge AI — analyze.js  (v3)
 * ================================
 * Drop into: backend/routes/analyze.js
 *
 * Architecture upgrade from v1:
 *  ┌──────────────┐   SSE stream    ┌─────────────────────┐
 *  │  React UI    │ ←────────────── │  Express /analyze   │
 *  └──────────────┘                 └──────────┬──────────┘
 *                                              │  Unix socket
 *                                   ┌──────────▼──────────┐
 *                                   │  Python daemon.py   │  ← stays warm
 *                                   │  (async, LRU cache) │
 *                                   └─────────────────────┘
 *
 * Key differences:
 *   v1: spawn("python3") per request — 200ms cold start every time
 *   v3: persistent daemon, zero cold start, concurrent requests, LRU cache
 *
 *   v1: res.json(result) after 100% complete
 *   v3: SSE streams stage-by-stage — frontend renders progressively
 *
 *   v1: no health check, no daemon restart
 *   v3: GET /health, auto-restart on crash, 5s startup timeout
 */

const express   = require("express");
const router    = express.Router();
const net       = require("net");
const { spawn } = require("child_process");
const path      = require("path");
const crypto    = require("crypto");
const Result    = require("../models/Result");

// ── Config ──────────────────────────────────────────────────────────────────
const SF_MODE        = process.env.SF_MODE        || "unix";
const SF_SOCKET      = process.env.SF_SOCKET      || "/tmp/skillforge.sock";
const SF_TCP_HOST    = process.env.SF_TCP_HOST    || "127.0.0.1";
const SF_TCP_PORT    = parseInt(process.env.SF_TCP_PORT || "8001");
const DAEMON_SCRIPT  = process.env.ML_DAEMON_PATH ||
  path.resolve(__dirname, "../../ml/daemon.py");
const STREAM_TIMEOUT = parseInt(process.env.SF_TIMEOUT_MS || "120000");

// ── Daemon lifecycle ─────────────────────────────────────────────────────────
let _proc    = null;
let _ready   = false;
let _starting = false;

async function ensureDaemon() {
  if (_ready) return;
  if (_starting) {
    return new Promise((res) => {
      const iv = setInterval(() => { if (_ready || !_starting) { clearInterval(iv); res(); }}, 80);
    });
  }

  _starting = true;
  console.log("[SkillForge] Starting ML daemon…");

  const args = SF_MODE === "tcp"
    ? [DAEMON_SCRIPT, "--tcp", String(SF_TCP_PORT)]
    : [DAEMON_SCRIPT];

  _proc = spawn("python3", args, {
    env: { ...process.env, SF_SOCKET, PYTHONUNBUFFERED: "1" },
    stdio: ["ignore", "pipe", "pipe"],
  });

  _proc.stdout.on("data", (d) => {
    const line = d.toString().trim();
    if (line.includes("[SkillForge daemon]")) {
      console.log(line);
      _ready = true;
      _starting = false;
    }
  });

  _proc.stderr.on("data", (d) => {
    const t = d.toString().trim();
    // Surface import errors or tracebacks — hide normal asyncio noise
    if (t && (t.startsWith("Traceback") || t.includes("Error") || t.includes("error"))) {
      console.error("[daemon]", t);
    }
  });

  _proc.on("exit", (code) => {
    console.warn(`[SkillForge] Daemon exited (${code ?? "?"}). Will restart on next request.`);
    _ready = false; _starting = false; _proc = null;
  });

  await new Promise((resolve, reject) => {
    const deadline = Date.now() + 6000;
    const iv = setInterval(() => {
      if (_ready) { clearInterval(iv); resolve(); return; }
      if (Date.now() > deadline) {
        clearInterval(iv); _starting = false;
        reject(new Error("ML daemon did not start within 6s"));
      }
    }, 100);
  });
}

process.on("SIGTERM", () => _proc?.kill("SIGTERM"));
process.on("SIGINT",  () => _proc?.kill("SIGTERM"));

// ── Socket transport ─────────────────────────────────────────────────────────

function makeDaemonSocket() {
  return SF_MODE === "tcp"
    ? net.createConnection({ host: SF_TCP_HOST, port: SF_TCP_PORT })
    : net.createConnection({ path: SF_SOCKET });
}

/**
 * Send payload to daemon, receive newline-delimited JSON chunks.
 * Calls onStage(msg) for each "stage" event (SSE intermediate).
 * Resolves with the final "complete" data.
 */
function queryDaemon(payload, onStage) {
  return new Promise((resolve, reject) => {
    const sock = makeDaemonSocket();
    let buf = "", done = false;

    const timeout = setTimeout(() => {
      if (!done) { done = true; sock.destroy(); reject(new Error("Daemon timeout")); }
    }, STREAM_TIMEOUT);

    sock.once("connect", () => sock.write(JSON.stringify(payload) + "\n"));

    sock.on("data", (chunk) => {
      buf += chunk.toString();
      const lines = buf.split("\n");
      buf = lines.pop();
      for (const line of lines) {
        if (!line.trim()) continue;
        let msg;
        try { msg = JSON.parse(line); } catch { continue; }

        if      (msg.event === "stage"    ) { onStage?.(msg); }
        else if (msg.event === "complete" ) { clearTimeout(timeout); if (!done) { done = true; resolve(msg.data); } }
        else if (msg.event === "error"    ) { clearTimeout(timeout); if (!done) { done = true; reject(new Error(msg.error)); } }
      }
    });

    sock.on("error", (e) => { clearTimeout(timeout); if (!done) { done = true; reject(e); } });
  });
}

// ── POST /api/analyze ────────────────────────────────────────────────────────

router.post("/", async (req, res) => {
  const { resumeText, jobDescription, hoursPerWeek } = req.body;

  if (!resumeText?.trim() || !jobDescription?.trim())
    return res.status(400).json({ error: "resumeText and jobDescription are required." });

  // Ensure daemon is alive
  try {
    await ensureDaemon();
  } catch (err) {
    return res.status(503).json({ error: "ML service unavailable.", detail: err.message });
  }

  const requestId = crypto.randomUUID();
  const payload   = { id: requestId, resumeText, jobDescription, hoursPerWeek: hoursPerWeek || 10 };
  const wantsSSE  = req.headers.accept?.includes("text/event-stream");

  // ── SSE streaming path ─────────────────────────────────────────────────
  if (wantsSSE) {
    res.setHeader("Content-Type",      "text/event-stream");
    res.setHeader("Cache-Control",     "no-cache");
    res.setHeader("Connection",        "keep-alive");
    res.setHeader("X-Accel-Buffering", "no");
    res.flushHeaders();

    const sse = (event, data) =>
      res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);

    sse("connected", { requestId });

    try {
      const result = await queryDaemon(payload, (msg) => {
        sse("stage", { stage: msg.stage, label: msg.label, data: msg.data, ms: msg.ms });
      });

      let savedId = null;
      try {
        const doc = await Result.create({ resumeText, jobDescription, ...result, requestId });
        savedId = doc._id;
      } catch (dbErr) {
        console.error("[analyze] DB save failed:", dbErr.message);
      }

      sse("complete", { id: savedId, requestId, ...result });
      res.write("event: done\ndata: {}\n\n");
      res.end();

    } catch (err) {
      console.error("[analyze] SSE error:", err.message);
      sse("error", { error: err.message });
      res.end();
    }
    return;
  }

  // ── JSON fallback (for clients that don't support SSE) ─────────────────
  try {
    const result = await queryDaemon(payload, null);
    const doc    = await Result.create({ resumeText, jobDescription, ...result, requestId });
    return res.status(200).json({ id: doc._id, requestId, ...result });
  } catch (err) {
    console.error("[analyze] JSON mode error:", err.message);
    return res.status(500).json({ error: "Analysis failed.", detail: err.message });
  }
});

// ── GET /api/analyze/health ──────────────────────────────────────────────────

router.get("/health", (_req, res) => {
  res.json({ daemon: _ready ? "ready" : "offline", mode: SF_MODE, pid: _proc?.pid ?? null });
});

module.exports = router;
