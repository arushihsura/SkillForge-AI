import { Link } from "react-router-dom";
import CardSwap, { Card } from "./CardSwap";
import BorderGlow from "../components/BorderGlow";

function Landing() {
  return (
    <div className="sf-page relative overflow-hidden">
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-40 left-1/2 h-96 w-96 -translate-x-1/2 rounded-full bg-cyan-500/20 blur-3xl" />
        <div className="absolute bottom-0 right-0 h-80 w-80 rounded-full bg-fuchsia-500/15 blur-3xl" />
        <div className="grid-overlay absolute inset-0 opacity-35" />
      </div>

      <header className="sf-shell mt-5 flex items-center justify-between rounded-2xl border border-slate-800/80 bg-slate-900/55 px-6 py-4 backdrop-blur-lg md:px-8">
        <p className="text-lg font-semibold tracking-wide text-cyan-300">SkillForge AI</p>
        <nav className="flex items-center gap-5 text-sm text-slate-300">
          <a href="#features" className="transition hover:text-cyan-300">
            Features
          </a>
          <a href="#how-it-works" className="transition hover:text-cyan-300">
            How it works
          </a>
          <Link
            to="/login"
            className="rounded-full border border-cyan-400/50 px-4 py-2 font-medium text-cyan-200 transition hover:border-cyan-300 hover:bg-cyan-300/10"
          >
            Login
          </Link>
        </nav>
      </header>

      <main className="sf-shell px-6 pb-28 pt-10 md:px-8">
        <section className="grid items-center gap-14 pb-28 pt-10 md:grid-cols-2 md:pt-16">
          <div>
            <p className="mb-4 inline-flex rounded-full border border-cyan-300/40 bg-cyan-300/10 px-4 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-200">
              AI-Powered Onboarding
            </p>
            <h1 className="sf-title text-5xl font-bold leading-[1.05] md:text-7xl">
              Adaptive Onboarding Engine
            </h1>
            <p className="mt-7 max-w-xl text-xl leading-relaxed text-slate-300">
              Personalized learning paths based on your skills.
            </p>
            <div className="mt-10 flex flex-wrap gap-4">
              <a
                href="#how-it-works"
                className="sf-btn-primary rounded-full px-7 py-3.5"
              >
                Get Started
              </a>
              <Link
                to="/login"
                className="sf-btn-secondary rounded-full px-7 py-3.5 font-semibold"
              >
                Login
              </Link>
            </div>
          </div>

          <div className="relative">
            <div className="absolute -left-8 -top-8 h-24 w-24 rounded-full border border-cyan-300/20 bg-cyan-300/10 blur-sm" />
            <div className="absolute -bottom-10 right-0 h-28 w-28 rounded-full border border-fuchsia-300/25 bg-fuchsia-300/10 blur-sm" />

            <div className="sf-card relative p-6">
              <div className="mb-4 flex items-center justify-between">
                <p className="text-sm text-slate-300">Onboarding Intelligence</p>
                <span className="rounded-full bg-emerald-400/20 px-3 py-1 text-xs font-medium text-emerald-300">
                  Live
                </span>
              </div>

              <div className="space-y-3">
                <div className="rounded-xl border border-slate-700 bg-slate-950/70 p-3">
                  <p className="text-xs text-slate-400">Skill Match</p>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-800">
                    <div className="h-full w-3/4 rounded-full bg-cyan-400" />
                  </div>
                </div>

                <div className="rounded-xl border border-slate-700 bg-slate-950/70 p-3">
                  <p className="text-xs text-slate-400">Learning Path Progress</p>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-800">
                    <div className="h-full w-1/2 rounded-full bg-fuchsia-400" />
                  </div>
                </div>

                <div className="rounded-xl border border-slate-700 bg-slate-950/70 p-3">
                  <p className="text-xs text-slate-400">AI Confidence</p>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-800">
                    <div className="h-full w-[88%] rounded-full bg-emerald-400" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="scroll-mt-24 pb-0">
          <h2 className="sf-title text-3xl font-semibold text-white md:text-4xl">Features</h2>
          <div style={{ height: "360px", position: "relative", marginTop: 0, marginBottom: 0 }}>
            <CardSwap
              cardDistance={60}
              verticalDistance={70}
              delay={5000}
              pauseOnHover={false}
            >
              <Card>
                <h3 className="font-space text-2xl font-semibold text-cyan-300">Skill Gap Analysis</h3>
                <p className="mt-4 text-slate-300">
                  Detect missing capabilities between current strengths and role requirements.
                </p>
              </Card>
              <Card>
                <h3 className="font-space text-2xl font-semibold text-fuchsia-300">Adaptive Learning Path</h3>
                <p className="mt-4 text-slate-300">
                  Dynamic roadmaps that evolve as each learner completes milestones.
                </p>
              </Card>
              <Card>
                <h3 className="font-space text-2xl font-semibold text-emerald-300">
                  Explainable AI Recommendations
                </h3>
                <p className="mt-4 text-slate-300">
                  Transparent guidance with rationale so every suggestion is easy to trust.
                </p>
              </Card>
            </CardSwap>
          </div>
        </section>

        <section id="how-it-works" className="scroll-mt-24 pb-24">
          <h2 className="sf-title text-3xl font-semibold text-white md:text-4xl">How it works</h2>
          <div className="mt-8 grid gap-5 md:grid-cols-3">
            <BorderGlow
              edgeSensitivity={30}
              glowColor="40 80 80"
              backgroundColor="#060010"
              borderRadius={28}
              glowRadius={40}
              glowIntensity={1}
              coneSpread={25}
              animated={false}
              colors={["#22d3ee", "#818cf8", "#f472b6"]}
            >
              <div style={{ padding: "2em" }}>
                <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Step 1</p>
                <p className="mt-2 font-space text-2xl font-semibold text-white">Upload</p>
              </div>
            </BorderGlow>

            <BorderGlow
              edgeSensitivity={30}
              glowColor="40 80 80"
              backgroundColor="#060010"
              borderRadius={28}
              glowRadius={40}
              glowIntensity={1}
              coneSpread={25}
              animated={false}
              colors={["#c084fc", "#f472b6", "#38bdf8"]}
            >
              <div style={{ padding: "2em" }}>
                <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Step 2</p>
                <p className="mt-2 font-space text-2xl font-semibold text-white">Analyze</p>
              </div>
            </BorderGlow>

            <BorderGlow
              edgeSensitivity={30}
              glowColor="40 80 80"
              backgroundColor="#060010"
              borderRadius={28}
              glowRadius={40}
              glowIntensity={1}
              coneSpread={25}
              animated={false}
              colors={["#38bdf8", "#22d3ee", "#a78bfa"]}
            >
              <div style={{ padding: "2em" }}>
                <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Step 3</p>
                <p className="mt-2 font-space text-2xl font-semibold text-white">Learn</p>
              </div>
            </BorderGlow>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-800/90">
        <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-6 text-sm text-slate-400">
          <p>SkillForge AI</p>
          <div className="flex items-center gap-5">
            <a href="#features" className="transition hover:text-slate-200">
              Features
            </a>
            <a href="#how-it-works" className="transition hover:text-slate-200">
              How it works
            </a>
            <Link to="/login" className="transition hover:text-slate-200">
              Login
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Landing;
