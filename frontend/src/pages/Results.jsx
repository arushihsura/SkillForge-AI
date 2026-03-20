import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import axios from "axios";

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.2 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
};

function Results() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [saveMessage, setSaveMessage] = useState("");
  const [showQuiz, setShowQuiz] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [loadingQuestions, setLoadingQuestions] = useState(false);

  useEffect(() => {
    axios
      .get(`/api/results/${id}`)
      .then((res) => setData(res.data))
      .catch((err) => setError(err.response?.data || "Failed to load results"));
  }, [id]);

  const normalize = (skill) => skill.toLowerCase().trim();

  const hasTokenOverlap = (a, b) => {
    const tokensA = normalize(a).split(/\s+/);
    const tokensB = normalize(b).split(/\s+/);
    return tokensA.some((token) => tokensB.includes(token));
  };

  if (error) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center px-4">
        <p className="rounded-xl border border-rose-400/30 bg-rose-400/10 px-4 py-3 text-rose-200">{error}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center px-4 text-slate-200">
        <motion.div animate={{ opacity: [0.5, 1, 0.5] }} transition={{ repeat: Infinity, duration: 2 }}>
          Loading your v3 Intelligence Report...
        </motion.div>
      </div>
    );
  }

  const resumeSkills = data.skills?.resumeSkills || [];
  const jobSkills = data.skills?.jdSkills || [];
  const resumeSet = new Set(resumeSkills.map(normalize));
  const jobSet = new Set(jobSkills.map(normalize));

  const matchedSkills = jobSkills.filter((skill) => resumeSet.has(normalize(skill)));
  const missingSkills = jobSkills.filter((skill) => !resumeSet.has(normalize(skill)));
  const partialSkills = missingSkills.filter((jobSkill) =>
    resumeSkills.some((resumeSkill) => hasTokenOverlap(jobSkill, resumeSkill))
  );

  const coverage = jobSkills.length
    ? Math.round((matchedSkills.length / jobSkills.length) * 100)
    : 0;
  const redundancySaved = resumeSkills.filter((skill) => !jobSet.has(normalize(skill))).length;

  const learningBase =
    data.path?.length > 0
      ? data.path
      : jobSkills.map((skill) => ({
          skill,
          status: resumeSet.has(normalize(skill)) ? "skip" : "learn",
        }));

  const learningPath = learningBase.map((item, index) => {
    const phaseBreak = Math.ceil(learningBase.length / 3) || 1;
    const phaseIndex = Math.min(Math.floor(index / phaseBreak), 2);
    const phases = ["Foundations", "Core Skills", "Advanced"];
    const priority = index === 0 ? "High" : index < phaseBreak ? "Medium" : "Low";

    return {
      ...item,
      phase: phases[phaseIndex],
      priority,
      status: item.status?.toLowerCase() === "recommended" ? "learn" : item.status?.toLowerCase(),
    };
  });

  const groupedPath = {
    Foundations: learningPath.filter((item) => item.phase === "Foundations"),
    "Core Skills": learningPath.filter((item) => item.phase === "Core Skills"),
    Advanced: learningPath.filter((item) => item.phase === "Advanced"),
  };

  const saveAnalysis = () => {
    const inferredRole =
      data.role ||
      jobSkills.find((skill) => /engineer|developer|analyst|scientist|manager/i.test(skill)) ||
      "General Role";

    const existing = JSON.parse(localStorage.getItem("savedAnalyses") || "[]");
    const next = [
      {
        id: data._id,
        createdAt: data.createdAt,
        role: inferredRole,
        coverage,
        missingSkills: missingSkills.length,
      },
      ...existing,
    ];
    localStorage.setItem("savedAnalyses", JSON.stringify(next));
    setSaveMessage("Analysis saved to history.");
  };

  const downloadReport = () => {
    const report = {
      id: data._id,
      generatedAt: new Date().toISOString(),
      kpis: { coverage, missingSkills: missingSkills.length, redundancySaved },
      matchedSkills, missingSkills, partialSkills, learningPath,
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `skillforge-report-${data._id}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const generateQuestions = async () => {
    setLoadingQuestions(true);
    try {
      const res = await axios.post("/api/analyze/generate-questions", {
        missingSkills: missingSkills.slice(0, 5),
        jobDescription: data.jobDescription || jobSkills.join(", "),
      });
      setQuestions(res.data.questions || []);
      setShowQuiz(true);
    } catch (err) {
      console.error("Failed to generate questions", err);
    } finally {
      setLoadingQuestions(false);
    }
  };

  return (
    <div className="sf-page px-4 py-8 md:px-6">
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="sf-shell space-y-7"
      >
        <motion.header variants={itemVariants} className="sf-card p-7 md:p-8">
          <h1 className="sf-title text-3xl font-bold text-white md:text-5xl">AI Onboarding Results</h1>
          <p className="mt-3 text-base" style={{ color: 'var(--text-secondary)' }}>Insights from our 12-stage probabilistic engine.</p>
        </motion.header>

        <section className="grid gap-6 lg:grid-cols-2">
          <motion.article variants={itemVariants} className="sf-card p-7">
            <h2 className="font-space text-2xl font-semibold text-white">Skill Comparison</h2>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border p-4" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-soft)' }}>
                <p className="mb-3 text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Resume Skills</p>
                <div className="flex flex-wrap gap-2">
                  {resumeSkills.map((skill) => {
                    const isMatch = jobSet.has(normalize(skill));
                    const isPartial = !isMatch && partialSkills.some((item) => hasTokenOverlap(skill, item));
                    return (
                      <span key={`res-${skill}`} className="rounded-full px-3 py-1 text-xs font-medium" style={{
                        backgroundColor: isMatch ? 'color-mix(in srgb, var(--accent-primary) 30%, transparent)' : 
                                       isPartial ? 'rgba(251, 191, 36, 0.2)' : 'var(--bg-soft)',
                        color: isMatch ? 'var(--text-primary)' : isPartial ? '#fcd34d' : 'var(--text-secondary)'
                      }}>{skill}</span>
                    );
                  })}
                </div>
              </div>

              <div className="rounded-xl border p-4" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-soft)' }}>
                <p className="mb-3 text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Job Skills</p>
                <div className="flex flex-wrap gap-2">
                  {jobSkills.map((skill) => {
                    const isMatch = resumeSet.has(normalize(skill));
                    const isPartial = !isMatch && partialSkills.includes(skill);
                    return (
                      <span key={`job-${skill}`} className="rounded-full px-3 py-1 text-xs font-medium" style={{
                        backgroundColor: isMatch ? 'color-mix(in srgb, var(--accent-primary) 30%, transparent)' :
                                       isPartial ? 'rgba(251, 191, 36, 0.2)' : 'rgba(251, 113, 133, 0.2)',
                        color: isMatch ? 'var(--text-primary)' : isPartial ? '#fcd34d' : '#fb7185'
                      }}>{skill}</span>
                    );
                  })}
                </div>
              </div>
            </div>
          </motion.article>

          <motion.article variants={itemVariants} className="sf-card p-7">
            <h2 className="font-space text-2xl font-semibold text-white">Gap Visualization</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              {[
                { label: "Coverage", val: `${coverage}%`, color: 'var(--accent-primary)' },
                { label: "Missing", val: missingSkills.length, color: 'var(--accent-secondary)' },
                { label: "Saved", val: redundancySaved, color: 'var(--text-secondary)' }
              ].map((kpi, i) => (
                <div key={i} className="rounded-xl border p-4" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-soft)' }}>
                  <p className="text-[10px] uppercase tracking-[0.15em]" style={{ color: 'var(--text-secondary)' }}>{kpi.label}</p>
                  <p className="mt-1 text-3xl font-bold" style={{ color: kpi.color }}>{kpi.val}</p>
                </div>
              ))}
            </div>

            <div className="mt-6 space-y-4">
              {[
                { label: "Matched", count: matchedSkills.length, color: 'var(--accent-primary)', p: (matchedSkills.length/jobSkills.length)*100 },
                { label: "Partial", count: partialSkills.length, color: '#fcd34d', p: (partialSkills.length/jobSkills.length)*100 },
                { label: "Missing", count: missingSkills.length, color: 'var(--accent-secondary)', p: (missingSkills.length/jobSkills.length)*100 }
              ].map((bar, i) => (
                <div key={i}>
                  <div className="mb-1 flex items-center justify-between text-xs" style={{ color: 'var(--text-secondary)' }}>
                    <span>{bar.label}</span>
                    <span>{bar.count}</span>
                  </div>
                  <div className="h-2 rounded-full" style={{ backgroundColor: 'var(--bg-soft)' }}>
                    <motion.div initial={{ width: 0 }} animate={{ width: `${bar.p}%` }} transition={{ duration: 1, delay: 0.5 }} className="h-2 rounded-full" style={{ backgroundColor: bar.color }} />
                  </div>
                </div>
              ))}
            </div>
          </motion.article>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <motion.article variants={itemVariants} className="sf-card p-7">
            <h2 className="font-space text-2xl font-semibold text-white">SHAP: Explainability</h2>
            <p className="mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
              Impact of specific skills on your overall readiness score.
            </p>
            <div className="mt-5 space-y-4">
              {data.shapValues && Object.keys(data.shapValues).length > 0 ? (
                Object.entries(data.shapValues)
                  .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
                  .slice(0, 8)
                  .map(([skill, val]) => (
                    <div key={skill} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="font-medium text-white">{skill}</span>
                        <span style={{ color: val > 0 ? 'var(--accent-primary)' : '#fb7185' }}>
                          {val > 0 ? '+' : ''}{val.toFixed(1)}%
                        </span>
                      </div>
                      <div className="h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--bg-soft)' }}>
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${Math.min(100, Math.abs(val) * 5)}%` }}
                          className="h-full"
                          style={{
                            backgroundColor: val > 0 ? 'var(--accent-primary)' : '#fb7185',
                            marginLeft: val < 0 ? 'auto' : '0'
                          }}
                        />
                      </div>
                    </div>
                  ))
              ) : (
                <p className="text-sm italic" style={{ color: 'var(--text-secondary)' }}>No SHAP data available for this analysis.</p>
              )}
            </div>
          </motion.article>

          <motion.article variants={itemVariants} className="sf-card p-7 border-accent-glow">
            <h2 className="font-space text-2xl font-semibold text-white">Improve Your Profile</h2>
            <p className="mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
              Let SkillForge AI generate a customized 15-question questionnaire to help you close your skill gaps.
            </p>
            
            {!showQuiz ? (
              <div className="mt-6">
                <button 
                  onClick={generateQuestions}
                  disabled={loadingQuestions}
                  className="sf-btn-primary w-full py-4 flex items-center justify-center gap-3 text-lg"
                >
                  {loadingQuestions ? (
                    <>
                      <motion.div 
                        animate={{ rotate: 360 }} 
                        transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
                        className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full"
                      />
                      Generating Skill Quiz...
                    </>
                  ) : "Generate 15 Critical Questions"}
                </button>
              </div>
            ) : (
              <div className="mt-6 space-y-6">
                <div className="max-h-[400px] overflow-y-auto pr-2 space-y-4 sf-scrollbar">
                  {questions.map((q, idx) => (
                    <div key={idx} className="p-4 rounded-xl border" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-soft)' }}>
                      <p className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: 'var(--accent-primary)' }}>Question {idx + 1}</p>
                      <p className="text-white font-medium">{q.question}</p>
                    </div>
                  ))}
                </div>
                <button 
                  onClick={() => setShowQuiz(false)}
                  className="text-sm underline" style={{ color: 'var(--text-secondary)' }}
                >
                  Back to Overview
                </button>
              </div>
            )}
          </motion.article>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          {/* Market Intelligence Section */}
          <motion.article variants={itemVariants} className="sf-card p-7">
            <h2 className="font-space text-2xl font-semibold text-white">Market Intelligence</h2>
            <div className="mt-5 grid grid-cols-2 gap-4">
              <div className="rounded-xl border p-4 bg-white/5" style={{ borderColor: 'var(--border-color)' }}>
                <p className="text-[10px] uppercase tracking-wider text-slate-400">Competitive Percentile</p>
                <p className="mt-2 text-3xl font-bold text-emerald-400">{data.applicantBenchmark?.percentile || 0}th</p>
                <p className="text-[10px] mt-1 text-slate-500">vs 2,000 simulated applicants</p>
              </div>
              <div className="rounded-xl border p-4 bg-white/5" style={{ borderColor: 'var(--border-color)' }}>
                <p className="text-[10px] uppercase tracking-wider text-slate-400">JD Inflation Score</p>
                <p className="mt-2 text-3xl font-bold text-rose-400">{data.marketPulse?.jdInflationScore || 0}%</p>
                <p className="text-[10px] mt-1 text-slate-500">Unnecessary skill density</p>
              </div>
            </div>

            <div className="mt-6">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Trending Gap Skills</p>
              <div className="flex flex-wrap gap-2">
                {(data.marketPulse?.trendingSkills || []).map(s => (
                  <span key={s} className="px-3 py-1 bg-emerald-400/10 text-emerald-400 text-xs rounded-full border border-emerald-400/20">
                    🔥 {s}
                  </span>
                ))}
              </div>
            </div>

            <div className="mt-6 p-4 rounded-xl border border-accent-primary/20 bg-accent-primary/5">
              <p className="text-sm italic text-slate-300">"{data.marketPulse?.insight || 'Focus on high-velocity skills to stay ahead.'}"</p>
            </div>
          </motion.article>

          {/* ROI & Career Growth Section */}
          <motion.article variants={itemVariants} className="sf-card p-7">
            <h2 className="font-space text-2xl font-semibold text-white">Career ROI Analysis</h2>
            <div className="mt-5 space-y-6">
              <div>
                <div className="flex justify-between text-xs mb-2">
                  <span className="text-slate-400">Hire Probability Improvement</span>
                  <span className="text-emerald-400 font-bold">+{data.interviewReadiness?.improvementFactor || 1}x</span>
                </div>
                <div className="h-3 bg-white/5 rounded-full overflow-hidden flex">
                   <div 
                    className="h-full bg-slate-600" 
                    style={{ width: `${(data.interviewReadiness?.overallHireProbabilityNow || 0) * 100}%` }} 
                   />
                   <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${((data.interviewReadiness?.overallHireProbabilityAfterPath || 0) - (data.interviewReadiness?.overallHireProbabilityNow || 0)) * 100}%` }}
                    className="h-full bg-emerald-500"
                   />
                </div>
                <p className="text-[10px] mt-2 text-slate-500 text-right">Probability: Now (Gray) vs After Path (Green)</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-xl border border-white/5">
                  <p className="text-[10px] text-slate-400">Bottleneck Stage</p>
                  <p className="text-sm font-bold text-white uppercase mt-1">
                    {data.interviewReadiness?.bottleneck?.replace(/([A-Z])/g, ' $1') || 'N/A'}
                  </p>
                </div>
                <div className="p-3 rounded-xl border border-white/5">
                  <p className="text-[10px] text-slate-400">Total Learning Investment</p>
                  <p className="text-sm font-bold text-white mt-1">
                    {data.kpis?.estimatedTotalHours || 0} Hours
                  </p>
                </div>
              </div>
            </div>
          </motion.article>
        </section>

        <motion.section variants={itemVariants} className="sf-card p-7 flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="font-space text-2xl font-semibold text-white">Actions</h2>
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Export or save your career intelligence report.</p>
          </div>
          <div className="flex gap-3">
            <button onClick={downloadReport} className="sf-btn-primary px-6 py-2">Download JSON</button>
            <button onClick={saveAnalysis} className="sf-btn-secondary px-6 py-2">Save to Profile</button>
          </div>
        </motion.section>
        {saveMessage && <p className="text-center text-sm font-medium" style={{ color: 'var(--accent-primary)' }}>{saveMessage}</p>}
      </motion.div>
    </div>
  );
}

export default Results;
