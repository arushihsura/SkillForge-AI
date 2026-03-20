function AnalysisLoading({ progress = 0 }) {
  const steps = [
    "Parsing Resume",
    "Extracting Skills",
    "Analyzing Skill Gaps",
    "Generating Learning Path",
  ];

  const activeStep = Math.min(Math.floor(progress / 25), steps.length - 1);

  return (
    <div className="sf-page relative flex min-h-screen items-center justify-center overflow-hidden px-4">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-1/4 top-1/4 h-72 w-72 rounded-full bg-cyan-500/15 blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 h-72 w-72 rounded-full bg-indigo-500/15 blur-3xl" />
      </div>

      <section className="sf-card w-full max-w-xl p-8 md:p-10">
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full border border-cyan-300/40 bg-cyan-300/10">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-cyan-200/20 border-t-cyan-300" />
        </div>

        <h1 className="sf-title text-center text-3xl font-bold text-white md:text-4xl">AI Analysis In Progress</h1>
        <p className="mt-3 text-center text-sm text-slate-300">We are building your personalized onboarding path.</p>

        <div className="mt-6 h-2 overflow-hidden rounded-full bg-slate-800">
          <div className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-indigo-400 transition-all duration-500" style={{ width: `${progress}%` }} />
        </div>
        <p className="mt-2 text-right text-xs text-slate-300">{progress}%</p>

        <ul className="mt-6 space-y-3">
          {steps.map((step, index) => {
            const isCompleted = index < activeStep;
            const isActive = index === activeStep;

            return (
              <li
                key={step}
                className={`flex items-center justify-between rounded-xl border px-4 py-3 transition-all duration-300 ${
                  isCompleted
                    ? "border-emerald-300/40 bg-emerald-300/10"
                    : isActive
                    ? "border-cyan-300/40 bg-cyan-300/10"
                    : "border-slate-700 bg-slate-900/70"
                }`}
              >
                <span className="text-sm text-slate-100">{step}</span>
                <span
                  className={`h-2.5 w-2.5 rounded-full ${
                    isCompleted ? "bg-emerald-300" : isActive ? "animate-pulse bg-cyan-300" : "bg-slate-500"
                  }`}
                />
              </li>
            );
          })}
        </ul>
      </section>
    </div>
  );
}

export default AnalysisLoading;
