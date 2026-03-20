/**
 * useSkillAnalysis.js
 * ===================
 * Drop into: frontend/src/hooks/useSkillAnalysis.js
 *
 * Consumes the SSE stream from POST /api/analyze.
 * Exposes progressive state so the UI can render each stage as it arrives —
 * not waiting for 100% completion.
 *
 * Usage:
 *   const { run, stages, result, error, isLoading, isDone } = useSkillAnalysis();
 *   run({ resumeText, jobDescription, hoursPerWeek: 10 });
 *
 * `stages` fills in as each stage arrives:
 *   stages[1] → { label, data } immediately after extraction (~5ms)
 *   stages[2] → matching results
 *   stages[3] → gap analysis
 *   stages[4] → learning path
 *   result    → full payload when stream completes
 */

import { useState, useCallback, useRef } from "react";

const STAGE_LABELS = {
  1: "Extracting skills from resume & JD",
  2: "Matching your skills to requirements",
  3: "Running dependency graph analysis",
  4: "Planning your optimal learning path",
  5: "Computing readiness forecast",
};

export function useSkillAnalysis() {
  const [stages,    setStages]    = useState({});   // { [stageNum]: { label, data, ms } }
  const [result,    setResult]    = useState(null);
  const [error,     setError]     = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDone,    setIsDone]    = useState(false);
  const abortRef = useRef(null);

  const reset = useCallback(() => {
    setStages({});
    setResult(null);
    setError(null);
    setIsLoading(false);
    setIsDone(false);
  }, []);

  const run = useCallback(async ({ resumeText, jobDescription, hoursPerWeek = 10 }) => {
    reset();
    setIsLoading(true);

    // Abort any in-flight request
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept":        "text/event-stream",
        },
        body: JSON.stringify({ resumeText, jobDescription, hoursPerWeek }),
        signal: abortRef.current.signal,
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ error: response.statusText }));
        throw new Error(err.error || `HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buf += decoder.decode(value, { stream: true });
        const blocks = buf.split("\n\n");
        buf = blocks.pop(); // incomplete block back to buffer

        for (const block of blocks) {
          if (!block.trim()) continue;

          // Parse SSE: "event: X\ndata: {...}"
          const eventMatch = block.match(/^event:\s*(\S+)/m);
          const dataMatch  = block.match(/^data:\s*(.+)/m);
          if (!eventMatch || !dataMatch) continue;

          const event = eventMatch[1];
          let data;
          try { data = JSON.parse(dataMatch[1]); } catch { continue; }

          if (event === "stage") {
            setStages((prev) => ({
              ...prev,
              [data.stage]: { label: data.label || STAGE_LABELS[data.stage], data: data.data, ms: data.ms },
            }));
          } else if (event === "complete") {
            setResult(data);
            setIsDone(true);
            setIsLoading(false);
          } else if (event === "error") {
            throw new Error(data.error || "Unknown analysis error");
          }
        }
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        setError(err.message);
        setIsLoading(false);
      }
    }
  }, [reset]);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setIsLoading(false);
  }, []);

  return {
    run,
    cancel,
    reset,
    stages,       // { 1: { label, data }, 2: {...}, ... }
    result,       // full result when done
    error,
    isLoading,
    isDone,
    stageLabels: STAGE_LABELS,
  };
}
