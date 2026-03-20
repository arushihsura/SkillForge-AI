import { Link, useNavigate } from "react-router-dom";

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
        <aside className="sf-card p-6">
          <p className="mb-6 font-space text-xl font-semibold text-cyan-300">SkillForge AI</p>

          <nav className="space-y-2">
            <Link
              to="/dashboard"
              className="block rounded-xl border border-cyan-400/30 bg-cyan-500/10 px-4 py-3 text-sm font-medium text-cyan-200"
            >
              Dashboard
            </Link>
            <Link
              to="/analyze"
              className="block rounded-xl border border-slate-700 px-4 py-3 text-sm text-slate-300 transition hover:-translate-y-0.5 hover:border-slate-500 hover:bg-slate-800/70"
            >
              New Analysis
            </Link>
            <Link
              to="/history"
              className="block rounded-xl border border-slate-700 px-4 py-3 text-sm text-slate-300 transition hover:-translate-y-0.5 hover:border-slate-500 hover:bg-slate-800/70"
            >
              History
            </Link>
            <Link
              to="/profile"
              className="block rounded-xl border border-slate-700 px-4 py-3 text-sm text-slate-300 transition hover:-translate-y-0.5 hover:border-slate-500 hover:bg-slate-800/70"
            >
              Profile
            </Link>
            <button
              onClick={logout}
              className="w-full rounded-xl border border-rose-400/30 bg-rose-400/10 px-4 py-3 text-left text-sm font-medium text-rose-200 transition hover:-translate-y-0.5 hover:border-rose-300/60 hover:bg-rose-400/15"
            >
              Logout
            </button>
          </nav>
        </aside>

        <main className="space-y-7">
          <section className="sf-card p-7 md:p-8">
            <h1 className="sf-title text-3xl font-bold text-white md:text-5xl">Welcome back, {userName}</h1>
            <p className="mt-3 text-base text-slate-300">Start a new analysis or review past results</p>
          </section>

          <section className="grid gap-4 sm:grid-cols-2">
            <Link
              to="/analyze"
              className="sf-card group p-7 transition hover:-translate-y-1 hover:border-cyan-400/40"
            >
              <p className="text-sm text-slate-400">Quick Action</p>
              <h2 className="mt-1 font-space text-2xl font-semibold text-white">New Analysis</h2>
              <p className="mt-2 text-sm text-slate-300">Run an AI skill-gap analysis for a new role.</p>
              <p className="mt-4 text-sm font-medium text-cyan-300 transition group-hover:text-cyan-200">Open</p>
            </Link>

            <Link
              to="/history"
              className="sf-card group p-7 transition hover:-translate-y-1 hover:border-indigo-400/40"
            >
              <p className="text-sm text-slate-400">Quick Action</p>
              <h2 className="mt-1 font-space text-2xl font-semibold text-white">View History</h2>
              <p className="mt-2 text-sm text-slate-300">Review previous reports and recommendations.</p>
              <p className="mt-4 text-sm font-medium text-indigo-300 transition group-hover:text-indigo-200">Go to list</p>
            </Link>
          </section>

          <section id="recent-activity" className="sf-card p-7">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-space text-2xl font-semibold text-white">Recent activity</h2>
              <span className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300">
                {recentAnalyses.length} items
              </span>
            </div>

            <div className="space-y-3">
              {recentAnalyses.map((item) => (
                <article
                  key={item.id}
                  className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 transition hover:border-slate-600 hover:bg-slate-950"
                >
                  <p className="text-sm text-slate-400">{item.date}</p>
                  <p className="mt-1 text-base font-medium text-slate-100">{item.role}</p>
                </article>
              ))}
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

export default Dashboard;
