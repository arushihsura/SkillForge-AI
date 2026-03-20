import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.05 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, x: -10 },
  show: { opacity: 1, x: 0 }
};

function History() {
  const [query, setQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [dateFilter, setDateFilter] = useState("");

  const analyses = useMemo(() => {
    const raw = JSON.parse(localStorage.getItem("savedAnalyses") || "[]");
    return raw.map((item) => {
      const created = item.createdAt ? new Date(item.createdAt) : new Date();
      const safeDate = Number.isNaN(created.getTime()) ? new Date() : created;

      return {
        ...item,
        role: item.role || "General Role",
        createdAt: safeDate.toISOString(),
        displayDate: safeDate.toLocaleDateString("en-US", {
          year: "numeric",
          month: "short",
          day: "numeric",
        }),
        coverage: item.coverage ?? 0,
      };
    });
  }, []);

  const roleOptions = useMemo(() => {
    const roles = new Set(analyses.map((a) => a.role));
    return ["all", ...Array.from(roles)];
  }, [analyses]);

  const filtered = analyses.filter((item) => {
    const q = query.trim().toLowerCase();
    const matchesQuery = !q || item.role.toLowerCase().includes(q);
    const matchesRole = roleFilter === "all" || item.role === roleFilter;
    const matchesDate = !dateFilter || item.createdAt.startsWith(dateFilter);

    return matchesQuery && matchesRole && matchesDate;
  });

  return (
    <div className="sf-page px-4 py-8 md:px-6">
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="sf-shell space-y-7"
      >
        <motion.header variants={itemVariants} className="sf-card p-7 md:p-8">
          <h1 className="sf-title text-3xl font-bold text-white md:text-5xl">Analysis History</h1>
          <p className="mt-3 text-base" style={{ color: 'var(--text-secondary)' }}>Track your career intelligence journey.</p>
        </motion.header>

        <motion.section variants={itemVariants} className="sf-card p-5 md:p-6">
          <div className="grid gap-3 md:grid-cols-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by role"
              className="sf-input text-sm"
              style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-soft)' }}
            />

            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="sf-input text-sm"
              style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-soft)' }}
            >
              {roleOptions.map((role) => (
                <option key={role} value={role} style={{ backgroundColor: 'var(--bg-primary)' }}>
                  {role === "all" ? "All Roles" : role}
                </option>
              ))}
            </select>

            <input
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="sf-input text-sm"
              style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-soft)' }}
            />
          </div>
        </motion.section>

        <motion.section variants={itemVariants} className="sf-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead style={{ backgroundColor: 'rgba(255, 255, 255, 0.05)', color: 'var(--text-secondary)' }}>
                <tr>
                  <th className="px-5 py-4 font-semibold uppercase tracking-wider text-[11px]">Date</th>
                  <th className="px-5 py-4 font-semibold uppercase tracking-wider text-[11px]">Job Role</th>
                  <th className="px-5 py-4 font-semibold uppercase tracking-wider text-[11px]">Coverage</th>
                  <th className="px-5 py-4 font-semibold uppercase tracking-wider text-[11px]">Actions</th>
                </tr>
              </thead>
              <tbody style={{ borderColor: 'var(--border-color)' }}>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-5 py-12 text-center italic" style={{ color: 'var(--text-secondary)' }}>
                      No records found. Start a new analysis to see results here.
                    </td>
                  </tr>
                ) : (
                  filtered.map((item) => (
                    <motion.tr 
                      key={`${item.id}-${item.createdAt}`} 
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="transition-colors"
                      style={{ borderTop: '1px solid var(--border-color)' }}
                    >
                      <td className="px-5 py-4" style={{ color: 'var(--text-secondary)' }}>{item.displayDate}</td>
                      <td className="px-5 py-4 font-medium text-white">{item.role}</td>
                      <td className="px-5 py-4">
                        <span className="rounded-full px-3 py-1 text-[11px] font-bold" style={{ color: 'var(--accent-primary)', backgroundColor: 'color-mix(in srgb, var(--accent-primary) 15%, transparent)' }}>
                          {item.coverage}%
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <Link
                          to={`/results/${item.id}`}
                          className="sf-btn-secondary px-4 py-1.5 text-xs font-semibold"
                        >
                          View Report
                        </Link>
                      </td>
                    </motion.tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </motion.section>
      </motion.div>
    </div>
  );
}

export default History;
