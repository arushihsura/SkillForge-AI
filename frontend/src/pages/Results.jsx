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
          <p className="mt-3 text-base text-slate-300">Insights from our 12-stage probabilistic engine.</p>
        </motion.header>

        <section className="grid gap-6 lg:grid-cols-2">
          <motion.article variants={itemVariants} className="sf-card p-7">
            <h2 className="font-space text-2xl font-semibold text-white">Skill Comparison</h2>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="mb-3 text-sm font-medium text-slate-300">Resume Skills</p>
                <div className="flex flex-wrap gap-2">
                  {resumeSkills.map((skill) => {
                    const isMatch = jobSet.has(normalize(skill));
                    const isPartial = !isMatch && partialSkills.some((item) => hasTokenOverlap(skill, item));
                    return (
                      <span key={`res-${skill}`} className={`rounded-full px-3 py-1 text-xs font-medium ${
                        isMatch ? "bg-emerald-400/20 text-emerald-200" : 
                        isPartial ? "bg-amber-400/20 text-amber-200" : "bg-white/10 text-slate-300"
                      }`}>{skill}</span>
                    );
                  })}
                </div>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="mb-3 text-sm font-medium text-slate-300">Job Skills</p>
                <div className="flex flex-wrap gap-2">
                  {jobSkills.map((skill) => {
                    const isMatch = resumeSet.has(normalize(skill));
                    const isPartial = !isMatch && partialSkills.includes(skill);
                    return (
                      <span key={`job-${skill}`} className={`rounded-full px-3 py-1 text-xs font-medium ${
                        isMatch ? "bg-emerald-400/20 text-emerald-200" :
                        isPartial ? "bg-amber-400/20 text-amber-200" : "bg-rose-400/20 text-rose-200"
                      }`}>{skill}</span>
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
                { label: "Coverage", val: `${coverage}%`, color: "text-cyan-300" },
                { label: "Missing", val: missingSkills.length, color: "text-rose-300" },
                { label: "Saved", val: redundancySaved, color: "text-amber-300" }
              ].map((kpi, i) => (
                <div key={i} className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <p className="text-[10px] uppercase tracking-[0.15em] text-slate-400">{kpi.label}</p>
                  <p className={`mt-1 text-3xl font-bold ${kpi.color}`}>{kpi.val}</p>
                </div>
              ))}
            </div>

            <div className="mt-6 space-y-4">
              {[
                { label: "Matched", count: matchedSkills.length, color: "bg-emerald-400", p: (matchedSkills.length/jobSkills.length)*100 },
                { label: "Partial", count: partialSkills.length, color: "bg-amber-400", p: (partialSkills.length/jobSkills.length)*100 },
                { label: "Missing", count: missingSkills.length, color: "bg-rose-400", p: (missingSkills.length/jobSkills.length)*100 }
              ].map((bar, i) => (
                <div key={i}>
                  <div className="mb-1 flex items-center justify-between text-xs text-slate-300">
                    <span>{bar.label}</span>
                    <span>{bar.count}</span>
                  </div>
                  <div className="h-2 rounded-full bg-white/10">
                    <motion.div initial={{ width: 0 }} animate={{ width: `${bar.p}%` }} transition={{ duration: 1, delay: 0.5 }} className={`h-2 rounded-full ${bar.color}`} />
                  </div>
                </div>
              ))}
            </div>
          </motion.article>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <motion.article variants={itemVariants} className="sf-card p-7">
            <h2 className="font-space text-2xl font-semibold text-white">Learning Path</h2>
            <div className="mt-5 space-y-6">
              {Object.entries(groupedPath).map(([phase, items]) => (
                <div key={phase} className="relative pl-6">
                  <div className="absolute left-[9px] top-0 h-full w-px bg-white/10" />
                  <p className="relative mb-3 inline-flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.15em] text-accent-primary" style={{ color: 'var(--accent-primary)' }}>
                    <span className="absolute -left-[29px] inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: 'var(--accent-primary)' }} />
                    {phase}
                  </p>
                  <div className="space-y-2">
                    {items.map((item) => (
                      <div key={item.skill} className="rounded-xl border border-white/5 bg-white/5 p-3 hover:bg-white/10 transition-colors">
                        <p className="font-medium text-slate-100">{item.skill}</p>
                        <div className="mt-2 flex gap-2 text-[10px]">
                          <span className={`px-2 py-0.5 rounded-full ${item.status === 'skip' ? 'bg-emerald-400/20 text-emerald-200' : 'bg-rose-400/20 text-rose-200'}`}>
                            {item.status.toUpperCase()}
                          </span>
                          <span className="px-2 py-0.5 rounded-full bg-white/10 text-slate-400">PRIORITY: {item.priority}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </motion.article>

          <motion.article variants={itemVariants} className="sf-card p-7">
            <h2 className="font-space text-2xl font-semibold text-white">Reasoning Trace</h2>
            <div className="mt-5 space-y-2">
              {learningPath.map((item, idx) => (
                <details key={idx} className="rounded-xl border border-white/5 bg-white/5 p-4 group open:border-accent-primary/50 transition-all">
                  <summary className="cursor-pointer list-none font-medium text-slate-100 flex items-center justify-between">
                    {item.skill}
                    <span className="text-xs text-slate-500 group-open:rotate-180 transition-transform md:block hidden">▼</span>
                  </summary>
                  <div className="mt-3 text-sm text-slate-400 space-y-2 border-t border-white/5 pt-3">
                    <p><span className="text-slate-200 font-medium">Inference:</span> {item.status === 'skip' ? "Sufficient evidentiary skill markers found." : "Critical skill gap detected."}</p>
                    <p><span className="text-slate-200 font-medium">Prerequisites:</span> {item.phase === 'Foundations' ? "Fundamental" : "Sequence required"}</p>
                  </div>
                </details>
              ))}
            </div>
          </motion.article>
        </section>

        <motion.section variants={itemVariants} className="sf-card p-7 flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="font-space text-2xl font-semibold text-white">Actions</h2>
            <p className="text-sm text-slate-400">Export or save your career intelligence report.</p>
          </div>
          <div className="flex gap-3">
            <button onClick={downloadReport} className="sf-btn-primary px-6 py-2">Download JSON</button>
            <button onClick={saveAnalysis} className="sf-btn-secondary px-6 py-2">Save to Profile</button>
          </div>
        </motion.section>
        {saveMessage && <p className="text-center text-sm text-emerald-400 font-medium">{saveMessage}</p>}
      </motion.div>
    </div>
  );
}

export default Results;
