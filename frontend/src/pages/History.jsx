import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

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
      <div className="sf-shell space-y-7">
        <header className="sf-card p-7 md:p-8">
          <h1 className="sf-title text-3xl font-bold text-white md:text-5xl">Analysis History</h1>
          <p className="mt-3 text-base text-slate-300">Search and filter your past analyses.</p>
        </header>

        <section className="sf-card p-5 md:p-6">
          <div className="grid gap-3 md:grid-cols-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by role"
              className="sf-input text-sm"
            />

            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="sf-input text-sm"
            >
              {roleOptions.map((role) => (
                <option key={role} value={role}>
                  {role === "all" ? "All Roles" : role}
                </option>
              ))}
            </select>

            <input
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="sf-input text-sm"
            />
          </div>
        </section>

        <section className="sf-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="bg-slate-950/70 text-slate-300">
                <tr>
                  <th className="px-5 py-3 font-medium">Date</th>
                  <th className="px-5 py-3 font-medium">Job Role</th>
                  <th className="px-5 py-3 font-medium">Skill Coverage</th>
                  <th className="px-5 py-3 font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-5 py-8 text-center text-slate-400">
                      No analyses found for the selected filters.
                    </td>
                  </tr>
                ) : (
                  filtered.map((item) => (
                    <tr key={`${item.id}-${item.createdAt}`} className="border-t border-slate-800 transition hover:bg-slate-800/50">
                      <td className="px-5 py-4 text-slate-300">{item.displayDate}</td>
                      <td className="px-5 py-4 text-slate-100">{item.role}</td>
                      <td className="px-5 py-4">
                        <span className="rounded-full bg-cyan-400/15 px-3 py-1 text-xs font-medium text-cyan-200">
                          {item.coverage}%
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <Link
                          to={`/results/${item.id}`}
                          className="rounded-lg border border-slate-600 px-3 py-1.5 text-xs font-medium text-slate-100 transition hover:border-cyan-400 hover:text-cyan-200"
                        >
                          View
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}

export default History;
