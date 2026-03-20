import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import AnalysisLoading from "../components/AnalysisLoading";

function Analyze() {
  const [resumeFile, setResumeFile] = useState(null);
  const [jdFile, setJdFile] = useState(null);
  const [isDraggingResume, setIsDraggingResume] = useState(false);
  const [isDraggingJd, setIsDraggingJd] = useState(false);
  const [progress, setProgress] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const hasBothFiles = Boolean(resumeFile && jdFile);

  const extractFileText = async (file) => {
    if (!file) return "";
    return file.text();
  };

  const handleDrop = (event, type) => {
    event.preventDefault();
    const droppedFile = event.dataTransfer.files?.[0];
    if (!droppedFile) return;

    if (type === "resume") {
      setResumeFile(droppedFile);
      setIsDraggingResume(false);
      return;
    }

    setJdFile(droppedFile);
    setIsDraggingJd(false);
  };

  const handleAnalyze = async () => {
    if (!hasBothFiles || isAnalyzing) return;

    setError("");
    setIsAnalyzing(true);
    setProgress(10);

    const intervalId = setInterval(() => {
      setProgress((current) => (current >= 90 ? current : current + 10));
    }, 250);

    try {
      const [resumeText, jdText] = await Promise.all([
        extractFileText(resumeFile),
        extractFileText(jdFile),
      ]);

      const res = await axios.post(
        "/api/analyze",
        {
          resumeText,
          jdText,
        },
        {
          headers: { Authorization: localStorage.getItem("token") },
        }
      );

      setProgress(100);
      navigate(`/results/${res.data._id}`);
    } catch (err) {
      setError(err.response?.data || "Analysis failed");
    } finally {
      clearInterval(intervalId);
      setTimeout(() => {
        setIsAnalyzing(false);
        setProgress(0);
      }, 250);
    }
  };

  if (isAnalyzing) {
    return <AnalysisLoading progress={progress} />;
  }

  return (
    <div className="sf-page relative overflow-hidden px-4 py-10 md:px-6">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-0 top-0 h-72 w-72 rounded-full bg-cyan-500/15 blur-3xl" />
        <div className="absolute bottom-0 right-0 h-80 w-80 rounded-full bg-indigo-500/15 blur-3xl" />
      </div>

      <div className="sf-shell max-w-3xl">
        <div className="sf-card p-7 md:p-9">
          <h1 className="sf-title text-3xl font-bold text-white md:text-5xl">Start New Analysis</h1>
          <p className="mt-2 text-sm text-slate-300">
            Upload both files to generate a skill gap analysis and learning path.
          </p>

          <div className="mt-7 space-y-5">
            <div>
              <p className="mb-2 text-sm font-medium text-slate-200">Upload Resume</p>
              <label
                onDragOver={(event) => {
                  event.preventDefault();
                  setIsDraggingResume(true);
                }}
                onDragLeave={() => setIsDraggingResume(false)}
                onDrop={(event) => handleDrop(event, "resume")}
                className={`block cursor-pointer rounded-2xl border-2 border-dashed p-5 transition ${
                  isDraggingResume
                    ? "border-cyan-300 bg-cyan-300/10"
                    : "border-slate-600 bg-slate-900/50 hover:border-cyan-400/60 hover:bg-slate-900"
                }`}
              >
                <input
                  type="file"
                  className="hidden"
                  onChange={(event) => setResumeFile(event.target.files?.[0] || null)}
                />
                <div className="flex items-center gap-3">
                  <span className="rounded-lg bg-cyan-300/15 p-2 text-cyan-200">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zm0 2.5L18.5 9H14z" />
                    </svg>
                  </span>
                  <div>
                    <p className="text-sm text-slate-100">Drag and drop your resume</p>
                    <p className="text-xs text-slate-400">or click to browse files</p>
                  </div>
                </div>
              </label>
              {resumeFile && <p className="mt-2 text-sm text-cyan-200">Selected: {resumeFile.name}</p>}
            </div>

            <div>
              <p className="mb-2 text-sm font-medium text-slate-200">Upload Job Description</p>
              <label
                onDragOver={(event) => {
                  event.preventDefault();
                  setIsDraggingJd(true);
                }}
                onDragLeave={() => setIsDraggingJd(false)}
                onDrop={(event) => handleDrop(event, "jd")}
                className={`block cursor-pointer rounded-2xl border-2 border-dashed p-5 transition ${
                  isDraggingJd
                    ? "border-indigo-300 bg-indigo-300/10"
                    : "border-slate-600 bg-slate-900/50 hover:border-indigo-400/60 hover:bg-slate-900"
                }`}
              >
                <input
                  type="file"
                  className="hidden"
                  onChange={(event) => setJdFile(event.target.files?.[0] || null)}
                />
                <div className="flex items-center gap-3">
                  <span className="rounded-lg bg-indigo-300/15 p-2 text-indigo-200">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zm0 2.5L18.5 9H14z" />
                    </svg>
                  </span>
                  <div>
                    <p className="text-sm text-slate-100">Drag and drop the job description</p>
                    <p className="text-xs text-slate-400">or click to browse files</p>
                  </div>
                </div>
              </label>
              {jdFile && <p className="mt-2 text-sm text-indigo-200">Selected: {jdFile.name}</p>}
            </div>
          </div>

          {error && <p className="mt-4 text-sm text-rose-300">{error}</p>}

          <button
            onClick={handleAnalyze}
            disabled={!hasBothFiles || isAnalyzing}
            className="sf-btn-primary mt-7 w-full px-4 py-3 disabled:cursor-not-allowed disabled:brightness-75 disabled:grayscale"
          >
            {isAnalyzing ? "Analyzing..." : "Analyze"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default Analyze;
