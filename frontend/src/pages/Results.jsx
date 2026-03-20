import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";

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
      <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
        <p className="rounded-xl border border-rose-400/30 bg-rose-400/10 px-4 py-3 text-rose-200">{error}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 text-slate-200">
        Loading results...
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
    setSaveMessage("Analysis saved locally.");
  };

  const downloadReport = () => {
    const report = {
      id: data._id,
      generatedAt: new Date().toISOString(),
      kpis: {
        coverage,
        missingSkills: missingSkills.length,
        redundancySaved,
      },
      matchedSkills,
      missingSkills,
      partialSkills,
      learningPath,
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
      <div className="sf-shell space-y-7">
        <header className="sf-card p-7 md:p-8">
          <h1 className="sf-title text-3xl font-bold text-white md:text-5xl">AI Onboarding Results</h1>
          <p className="mt-3 text-base text-slate-300">Role-fit insights, skill gap mapping, and a personalized learning path.</p>
        </header>

        <section className="grid gap-6 lg:grid-cols-2">
          <article className="sf-card p-7">
            <h2 className="font-space text-2xl font-semibold text-white">Skill Comparison</h2>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                <p className="mb-3 text-sm font-medium text-slate-300">Resume Skills</p>
                <div className="flex flex-wrap gap-2">
                  {resumeSkills.map((skill) => {
                    const isMatch = jobSet.has(normalize(skill));
                    const isPartial = !isMatch && partialSkills.some((item) => hasTokenOverlap(skill, item));

                    return (
                      <span
                        key={`resume-${skill}`}
                        className={`rounded-full px-3 py-1 text-xs font-medium ${
                          isMatch
                            ? "bg-emerald-400/20 text-emerald-200"
                            : isPartial
                            ? "bg-amber-400/20 text-amber-200"
                            : "bg-slate-700/60 text-slate-300"
                        }`}
                      >
                        {skill}
                      </span>
                    );
                  })}
                </div>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                <p className="mb-3 text-sm font-medium text-slate-300">Job Skills</p>
                <div className="flex flex-wrap gap-2">
                  {jobSkills.map((skill) => {
                    const isMatch = resumeSet.has(normalize(skill));
                    const isPartial = !isMatch && partialSkills.includes(skill);

                    return (
                      <span
                        key={`job-${skill}`}
                        className={`rounded-full px-3 py-1 text-xs font-medium ${
                          isMatch
                            ? "bg-emerald-400/20 text-emerald-200"
                            : isPartial
                            ? "bg-amber-400/20 text-amber-200"
                            : "bg-rose-400/20 text-rose-200"
                        }`}
                      >
                        {skill}
                      </span>
                    );
                  })}
                </div>
              </div>
            </div>
          </article>

          <article className="sf-card p-7">
            <h2 className="font-space text-2xl font-semibold text-white">Skill Gap Visualization</h2>

            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                <p className="text-xs uppercase tracking-[0.15em] text-slate-400">Skill Coverage %</p>
                <p className="mt-2 text-3xl font-semibold text-cyan-300">{coverage}%</p>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                <p className="text-xs uppercase tracking-[0.15em] text-slate-400">Missing Skills</p>
                <p className="mt-2 text-3xl font-semibold text-rose-300">{missingSkills.length}</p>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                <p className="text-xs uppercase tracking-[0.15em] text-slate-400">Redundancy Saved</p>
                <p className="mt-2 text-3xl font-semibold text-amber-300">{redundancySaved}</p>
              </div>
            </div>

            <div className="mt-6 space-y-4">
              <div>
                <div className="mb-1 flex items-center justify-between text-xs text-slate-300">
                  <span>Matched Skills</span>
                  <span>{matchedSkills.length}</span>
                </div>
                <div className="h-2 rounded-full bg-slate-800">
                  <div
                    className="h-2 rounded-full bg-emerald-400"
                    style={{ width: `${jobSkills.length ? (matchedSkills.length / jobSkills.length) * 100 : 0}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="mb-1 flex items-center justify-between text-xs text-slate-300">
                  <span>Partial Skills</span>
                  <span>{partialSkills.length}</span>
                </div>
                <div className="h-2 rounded-full bg-slate-800">
                  <div
                    className="h-2 rounded-full bg-amber-400"
                    style={{ width: `${jobSkills.length ? (partialSkills.length / jobSkills.length) * 100 : 0}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="mb-1 flex items-center justify-between text-xs text-slate-300">
                  <span>Missing Skills</span>
                  <span>{missingSkills.length}</span>
                </div>
                <div className="h-2 rounded-full bg-slate-800">
                  <div
                    className="h-2 rounded-full bg-rose-400"
                    style={{ width: `${jobSkills.length ? (missingSkills.length / jobSkills.length) * 100 : 0}%` }}
                  />
                </div>
              </div>
            </div>
          </article>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <article className="sf-card p-7">
            <h2 className="font-space text-2xl font-semibold text-white">Learning Path</h2>
            <div className="mt-5 space-y-6">
              {Object.entries(groupedPath).map(([phase, items]) => (
                <div key={phase} className="relative pl-6">
                  <div className="absolute left-[9px] top-0 h-full w-px bg-slate-700" />
                  <p className="relative mb-3 inline-flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.15em] text-cyan-300">
                    <span className="absolute -left-6 inline-block h-2.5 w-2.5 rounded-full bg-cyan-300" />
                    {phase}
                  </p>
                  <div className="space-y-3">
                    {items.length === 0 && (
                      <p className="text-sm text-slate-400">No skills mapped in this phase.</p>
                    )}
                    {items.map((item) => (
                      <div key={`${phase}-${item.skill}`} className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                        <p className="font-medium text-slate-100">{item.skill}</p>
                        <div className="mt-2 flex flex-wrap gap-2 text-xs">
                          <span
                            className={`rounded-full px-2.5 py-1 font-medium ${
                              item.status === "skip"
                                ? "bg-emerald-400/20 text-emerald-200"
                                : "bg-rose-400/20 text-rose-200"
                            }`}
                          >
                            {item.status === "skip" ? "Skip" : "Learn"}
                          </span>
                          <span className="rounded-full bg-slate-700/60 px-2.5 py-1 text-slate-200">
                            Priority: {item.priority}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </article>

          <article className="sf-card p-7">
            <h2 className="font-space text-2xl font-semibold text-white">Reasoning Trace</h2>
            <div className="mt-5 space-y-3">
              {learningPath.map((item, idx) => (
                <details key={`reason-${item.skill}-${idx}`} className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 open:border-cyan-400/40">
                  <summary className="cursor-pointer list-none font-medium text-slate-100">
                    {item.skill}
                  </summary>
                  <div className="mt-3 space-y-2 text-sm text-slate-300">
                    <p>
                      <span className="font-medium text-slate-200">Why recommended:</span>{" "}
                      {item.status === "skip"
                        ? "Existing proficiency detected from resume alignment."
                        : "Required by role but missing or weak in current profile."}
                    </p>
                    <p>
                      <span className="font-medium text-slate-200">Dependencies:</span>{" "}
                      {item.phase === "Foundations"
                        ? "None"
                        : item.phase === "Core Skills"
                        ? "Foundations"
                        : "Foundations, Core Skills"}
                    </p>
                  </div>
                </details>
              ))}
            </div>
          </article>
        </section>

        <section className="sf-card p-7">
          <h2 className="font-space text-2xl font-semibold text-white">Actions</h2>
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              onClick={downloadReport}
              className="sf-btn-primary px-5 py-2.5"
            >
              Download Report
            </button>
            <button
              onClick={saveAnalysis}
              className="sf-btn-secondary px-5 py-2.5 font-semibold"
            >
              Save Analysis
            </button>
          </div>
          {saveMessage && <p className="mt-3 text-sm text-emerald-300">{saveMessage}</p>}
        </section>
      </div>
    </div>
  );
}

export default Results;
