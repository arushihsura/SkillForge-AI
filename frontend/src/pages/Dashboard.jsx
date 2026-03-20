import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

const itemVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: { opacity: 1, x: 0 }
};

function Dashboard() {
  const navigate = useNavigate();
  const userName = localStorage.getItem("name") || "User";

  const recentAnalyses = [
    { id: "a1", role: "Frontend Developer", date: "Mar 18, 2026" },
    { id: "a2", role: "Data Analyst", date: "Mar 14, 2026" },
    { id: "a3", role: "ML Engineer", date: "Mar 10, 2026" },
  ];

  const logout = () => {
    localStorage.removeItem("token");
    navigate("/");
  };

  return (
    <div className="sf-page">
      <div className="sf-shell grid grid-cols-1 gap-7 px-4 py-8 md:grid-cols-[280px_1fr] md:px-6 md:py-10">
        <motion.aside 
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          className="sf-card p-6 h-fit sticky top-24"
        >
          <p className="mb-6 font-space text-xl font-semibold md:hidden" style={{ color: 'var(--accent-primary)' }}>SkillForge AI</p>

          <nav className="space-y-2">
            {[
              { to: "/dashboard", label: "Dashboard", active: true },
              { to: "/analyze", label: "New Analysis" },
              { to: "/history", label: "History" },
              { to: "/profile", label: "Profile" }
            ].map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className="block rounded-xl border px-4 py-3 text-sm font-medium transition-all"
                style={{
                  borderColor: link.active ? 'color-mix(in srgb, var(--accent-primary) 30%, transparent)' : 'var(--border-color)',
                  backgroundColor: link.active ? 'color-mix(in srgb, var(--accent-primary) 10%, transparent)' : 'transparent',
                  color: link.active ? 'var(--text-primary)' : 'var(--text-secondary)'
                }}
              >
                {link.label}
              </Link>
            ))}
            <button
              onClick={logout}
              className="w-full mt-4 rounded-xl border px-4 py-3 text-left text-sm font-medium transition"
              style={{
                borderColor: 'rgba(251, 113, 133, 0.3)',
                backgroundColor: 'rgba(251, 113, 133, 0.1)',
                color: '#fda4af'
              }}
            >
              Logout
            </button>
          </nav>
        </motion.aside>

        <motion.main 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="space-y-7"
        >
          <section className="sf-card p-7 md:p-8">
            <h1 className="sf-title text-3xl font-bold text-white md:text-5xl">Welcome back, {userName}</h1>
            <p className="mt-3 text-base" style={{ color: 'var(--text-secondary)' }}>Start a new analysis or review past results</p>
          </section>

          <section className="grid gap-4 sm:grid-cols-2">
            <Link
              to="/analyze"
              className="sf-card group p-7 transition"
              style={{ borderColor: 'var(--border-color)' }}
            >
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Quick Action</p>
              <h2 className="mt-1 font-space text-2xl font-semibold text-white">New Analysis</h2>
              <p className="mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>Run an AI skill-gap analysis for a new role.</p>
              <p className="mt-4 text-sm font-medium transition" style={{ color: 'var(--accent-primary)' }}>Open &rarr;</p>
            </Link>

            <Link
              to="/history"
              className="sf-card group p-7 transition"
              style={{ borderColor: 'var(--border-color)' }}
            >
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Quick Action</p>
              <h2 className="mt-1 font-space text-2xl font-semibold text-white">View History</h2>
              <p className="mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>Review previous reports and recommendations.</p>
              <p className="mt-4 text-sm font-medium transition" style={{ color: 'var(--accent-secondary)' }}>Go to list &rarr;</p>
            </Link>
          </section>

          <section className="sf-card p-6 border-accent-glow bg-accent-primary/5 flex items-center justify-between gap-4">
            <div className="flex-1">
              <h3 className="font-space text-lg font-semibold text-white">ByteWorks Motivation 💡</h3>
              <p className="mt-1 text-sm text-slate-300">"Upskilling is a journey of a thousand steps. Today, you take one more. You've got this!"</p>
            </div>
            <button 
              onClick={() => document.getElementById('ai-chatbot-toggle')?.click()} 
              className="sf-btn-primary px-4 py-2 text-xs"
            >
              Talk to Coach
            </button>
          </section>

          <section id="recent-activity" className="sf-card p-7">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-space text-2xl font-semibold text-white">Recent activity</h2>
              <span className="rounded-full border px-3 py-1 text-xs" style={{ borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }}>
                {recentAnalyses.length} items
              </span>
            </div>

            <motion.div 
              initial="hidden"
              animate="visible"
              variants={{
                visible: { transition: { staggerChildren: 0.1 } }
              }}
              className="space-y-3"
            >
              {recentAnalyses.map((item) => (
                <motion.article
                  key={item.id}
                  variants={itemVariants}
                  className="rounded-xl border p-4 transition"
                  style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-soft)' }}
                >
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{item.date}</p>
                  <p className="mt-1 text-base font-medium text-white">{item.role}</p>
                </motion.article>
              ))}
            </motion.div>
          </section>
        </motion.main>
      </div>
    </div>
  );
}

export default Dashboard;
