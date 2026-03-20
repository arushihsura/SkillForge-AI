import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import axios from "axios";
import AnalysisLoading from "../components/AnalysisLoading";

function Analyze() {
  const [resumeFile, setResumeFile] = useState(null);
  const [jdFile, setJdFile] = useState(null);
  const [jdMode, setJdMode] = useState("file"); // "file" or "text"
  const [jdText, setJdText] = useState("");
  const [isDraggingResume, setIsDraggingResume] = useState(false);
  const [isDraggingJd, setIsDraggingJd] = useState(false);
  const [progress, setProgress] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const hasBothFiles = Boolean(resumeFile && (jdMode === "text" ? jdText.trim().length > 0 : jdFile));

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
    setJdMode("file");
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
      const resumeText = await extractFileText(resumeFile);
      const finalJdText = jdMode === "text" ? jdText : await extractFileText(jdFile);

      const res = await axios.post(
        "/api/analyze",
        {
          resumeText,
          jobDescription: finalJdText,
        },
        {
          headers: { Authorization: localStorage.getItem("token") },
        }
      );

      setProgress(100);
      navigate(`/results/${res.data._id || res.data.id}`);
    } catch (err) {
      setError(err.response?.data?.error || err.message || "Analysis failed");
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
    <div className="sf-page relative px-4 py-10 md:px-6">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="sf-shell max-w-3xl"
      >
        <div className="sf-card p-7 md:p-9">
          <h1 className="sf-title text-3xl font-bold text-white md:text-5xl">Start New Analysis</h1>
          <p className="mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
            Upload both files to generate a skill gap analysis using the v3 Probabilistic Engine.
          </p>

          <div className="mt-7 space-y-5">
            <div>
              <p className="mb-2 text-sm font-medium text-white/80">Upload Resume</p>
              <label
                onDragOver={(event) => {
                  event.preventDefault();
                  setIsDraggingResume(true);
                }}
                onDragLeave={() => setIsDraggingResume(false)}
                onDrop={(event) => handleDrop(event, "resume")}
                className="block cursor-pointer rounded-2xl border-2 border-dashed p-5 transition-all"
                style={{ 
                  borderColor: isDraggingResume ? 'var(--accent-primary)' : 'var(--border-color)',
                  backgroundColor: isDraggingResume ? 'var(--glow-1)' : 'var(--bg-soft)',
                  transform: isDraggingResume ? 'scale(1.01)' : 'none'
                }}
              >
                <input
                  type="file"
                  className="hidden"
                  onChange={(event) => setResumeFile(event.target.files?.[0] || null)}
                />
                <div className="flex items-center gap-3">
                  <span className="rounded-lg bg-white/5 p-2" style={{ color: 'var(--accent-primary)' }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zm0 2.5L18.5 9H14z" />
                    </svg>
                  </span>
                  <div>
                    <p className="text-sm text-white">{resumeFile ? resumeFile.name : "Drag and drop your resume"}</p>
                    <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{resumeFile ? "File selected" : "or click to browse files"}</p>
                  </div>
                </div>
              </label>
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm font-medium text-white/100">Job Description</p>
                <div className="flex gap-1 rounded-lg bg-white/5 p-1">
                  <button 
                    onClick={() => setJdMode('file')}
                    className={`rounded-md px-3 py-1 text-[10px] font-bold uppercase tracking-wider transition-all ${jdMode === 'file' ? 'bg-white/10 text-white shadow-sm' : 'text-white/40 hover:text-white/60'}`}
                  >File</button>
                  <button 
                    onClick={() => setJdMode('text')}
                    className={`rounded-md px-3 py-1 text-[10px] font-bold uppercase tracking-wider transition-all ${jdMode === 'text' ? 'bg-white/10 text-white shadow-sm' : 'text-white/40 hover:text-white/60'}`}
                  >Text</button>
                </div>
              </div>
              
              {jdMode === 'file' ? (
                <label
                  onDragOver={(event) => {
                    event.preventDefault();
                    setIsDraggingJd(true);
                  }}
                  onDragLeave={() => setIsDraggingJd(false)}
                  onDrop={(event) => handleDrop(event, "jd")}
                  className="block cursor-pointer rounded-2xl border-2 border-dashed p-5 transition-all"
                  style={{ 
                    borderColor: isDraggingJd ? 'var(--accent-secondary)' : 'var(--border-color)',
                    backgroundColor: isDraggingJd ? 'var(--glow-2)' : 'var(--bg-soft)',
                    transform: isDraggingJd ? 'scale(1.01)' : 'none'
                  }}
                >
                  <input
                    type="file"
                    className="hidden"
                    onChange={(event) => setJdFile(event.target.files?.[0] || null)}
                  />
                  <div className="flex items-center gap-3">
                    <span className="rounded-lg bg-white/5 p-2" style={{ color: 'var(--accent-secondary)' }}>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zm0 2.5L18.5 9H14z" />
                      </svg>
                    </span>
                    <div>
                      <p className="text-sm text-white">{jdFile ? jdFile.name : "Drag and drop the job description"}</p>
                      <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{jdFile ? "File selected" : "or click to browse files"}</p>
                    </div>
                  </div>
                </label>
              ) : (
                <textarea
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  placeholder="Paste the job description or requirements here..."
                  className="w-full h-32 rounded-2xl border-2 p-4 text-sm bg-transparent transition-all focus:outline-none"
                  style={{ 
                    borderColor: 'var(--border-color)',
                    backgroundColor: 'var(--bg-soft)',
                    color: 'var(--text-primary)'
                  }}
                />
              )}
            </div>
          </div>

          {error && <p className="mt-4 text-sm text-rose-300 font-medium">{error}</p>}

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleAnalyze}
            disabled={!hasBothFiles || isAnalyzing}
            className="sf-btn-primary mt-7 w-full px-4 py-4 disabled:cursor-not-allowed disabled:opacity-50 disabled:grayscale"
          >
            {isAnalyzing ? "Processing Stage..." : "Generate Analysis"}
          </motion.button>
        </div>
      </motion.div>
    </div>
  );
}

export default Analyze;
