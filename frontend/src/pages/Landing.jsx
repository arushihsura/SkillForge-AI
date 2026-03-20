import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import CardSwap, { Card } from "./CardSwap";
import BorderGlow from "../components/BorderGlow";

const containerVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.6, staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

function Landing() {
  return (
    <div className="sf-page relative overflow-hidden">
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div 
          className="absolute -top-40 left-1/2 h-96 w-96 -translate-x-1/2 rounded-full blur-3xl opacity-40" 
          style={{ backgroundColor: 'var(--glow-1)' }}
        />
        <div 
          className="absolute bottom-0 right-0 h-80 w-80 rounded-full blur-3xl opacity-30" 
          style={{ backgroundColor: 'var(--glow-2)' }}
        />
        <div className="grid-overlay absolute inset-0 opacity-35" />
      </div>

      <main className="sf-shell px-6 pb-28 pt-10 md:px-8">
        <motion.section 
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid items-center gap-14 pb-28 pt-10 md:grid-cols-2 md:pt-16"
        >
          <motion.div variants={itemVariants}>
            <p 
              className="mb-4 inline-flex rounded-full border px-4 py-1 text-xs font-semibold uppercase tracking-[0.18em]"
              style={{ 
                borderColor: 'color-mix(in srgb, var(--accent-primary) 40%, transparent)',
                backgroundColor: 'color-mix(in srgb, var(--accent-primary) 10%, transparent)',
                color: 'var(--text-secondary)'
              }}
            >
              AI-Powered Onboarding
            </p>
            <h1 className="sf-title text-5xl font-bold leading-[1.05] md:text-7xl">
              Adaptive Onboarding Engine
            </h1>
            <p className="mt-7 max-w-xl text-xl leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              Personalized learning paths based on your skills. Our v3 engine uses probabilistic inference to map your career trajectory.
            </p>
            <div className="mt-10 flex flex-wrap gap-4">
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <a
                  href="#how-it-works"
                  className="sf-btn-primary inline-block rounded-full px-7 py-3.5"
                >
                  Get Started
                </a>
              </motion.div>
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Link
                  to="/login"
                  className="sf-btn-secondary inline-block rounded-full px-7 py-3.5 font-semibold"
                >
                  Login
                </Link>
              </motion.div>
            </div>
          </motion.div>

          <motion.div 
            variants={itemVariants}
            className="relative"
          >
            <div className="absolute -left-8 -top-8 h-24 w-24 rounded-full border blur-sm opacity-30" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--glow-1)' }} />
            <div className="absolute -bottom-10 right-0 h-28 w-28 rounded-full border blur-sm opacity-30" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--glow-2)' }} />

            <div className="sf-card relative p-6 mt-10 md:mt-0">
              <div className="mb-4 flex items-center justify-between">
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Onboarding Intelligence</p>
                <span className="rounded-full px-3 py-1 text-xs font-medium" style={{ backgroundColor: 'color-mix(in srgb, var(--accent-secondary) 20%, transparent)', color: 'var(--accent-secondary)' }}>
                  Live
                </span>
              </div>

              <div className="space-y-3">
                {[
                  { label: "Skill Match", color: 'var(--accent-primary)', width: "75%" },
                  { label: "Learning Path Progress", color: 'var(--accent-secondary)', width: "50%" },
                  { label: "AI Confidence", color: 'var(--accent-primary)', width: "88%" }
                ].map((bar, i) => (
                  <div key={i} className="rounded-xl border border-white/5 bg-white/5 p-3">
                    <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{bar.label}</p>
                    <div className="mt-2 h-2 overflow-hidden rounded-full bg-black/40">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: bar.width }}
                        transition={{ duration: 1, delay: 0.5 + i * 0.2 }}
                        className="h-full rounded-full" 
                        style={{ backgroundColor: bar.color }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </motion.section>

        <section id="features" className="scroll-mt-24 pb-0">
          <h2 className="sf-title text-3xl font-semibold text-white md:text-4xl text-center md:text-left">Features</h2>
          <div style={{ height: "360px", position: "relative", marginTop: 0, marginBottom: 0 }}>
            <CardSwap
              cardDistance={60}
              verticalDistance={70}
              delay={5000}
              pauseOnHover={false}
            >
              <Card>
                <h3 className="font-space text-2xl font-semibold" style={{ color: 'var(--accent-primary)' }}>Skill Gap Analysis</h3>
                <p className="mt-4" style={{ color: 'var(--text-secondary)' }}>
                  Detect missing capabilities between current strengths and role requirements using Bayesian inference.
                </p>
              </Card>
              <Card>
                <h3 className="font-space text-2xl font-semibold" style={{ color: 'var(--accent-secondary)' }}>Adaptive Learning Path</h3>
                <p className="mt-4" style={{ color: 'var(--text-secondary)' }}>
                  Dynamic roadmaps optimized via Pareto-frontier scheduling for speed and ROI.
                </p>
              </Card>
              <Card>
                <h3 className="font-space text-2xl font-semibold" style={{ color: 'var(--accent-primary)' }}>
                  Explainable AI recommendations
                </h3>
                <p className="mt-4" style={{ color: 'var(--text-secondary)' }}>
                  Transparent reasoning trace for every skill identified and learning resource suggested.
                </p>
              </Card>
            </CardSwap>
          </div>
        </section>

        <section id="how-it-works" className="scroll-mt-24 pb-24">
          <h2 className="sf-title text-3xl font-semibold text-white md:text-4xl text-center md:text-left">How it works</h2>
          <div className="mt-8 grid gap-5 md:grid-cols-3">
            {[
              { step: 1, label: "Upload", colors: ["#22d3ee", "#818cf8", "#f472b6"] },
              { step: 2, label: "Analyze", colors: ["#c084fc", "#f472b6", "#38bdf8"] },
              { step: 3, label: "Learn", colors: ["#38bdf8", "#22d3ee", "#a78bfa"] }
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
              >
                <BorderGlow
                  edgeSensitivity={30}
                  glowColor="40 80 80"
                  backgroundColor="var(--bg-primary)"
                  borderRadius={28}
                  glowRadius={40}
                  glowIntensity={1}
                  coneSpread={25}
                  animated={false}
                  colors={item.colors}
                >
                  <div style={{ padding: "2em" }}>
                    <p className="text-sm uppercase tracking-[0.2em]" style={{ color: 'var(--text-secondary)' }}>Step {item.step}</p>
                    <p className="mt-2 font-space text-2xl font-semibold text-white">{item.label}</p>
                  </div>
                </BorderGlow>
              </motion.div>
            ))}
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-800/90">
        <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-10 text-sm text-slate-400">
          <p>SkillForge AI — IISc Hackathon 2026</p>
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
