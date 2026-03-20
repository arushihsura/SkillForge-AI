import { useState } from "react";

function Profile() {
  const [name, setName] = useState(localStorage.getItem("name") || "");
  const [email, setEmail] = useState(localStorage.getItem("email") || "");
  const [role, setRole] = useState(localStorage.getItem("role") || "Learner");
  const [savedResume, setSavedResume] = useState(localStorage.getItem("savedResume") || "");
  const [weeklyGoal, setWeeklyGoal] = useState(localStorage.getItem("weeklyGoal") || "3");
  const [notifications, setNotifications] = useState(localStorage.getItem("notifications") !== "off");
  const [message, setMessage] = useState("");

  const handleSave = (event) => {
    event.preventDefault();

    localStorage.setItem("name", name);
    localStorage.setItem("email", email);
    localStorage.setItem("role", role);
    localStorage.setItem("savedResume", savedResume);
    localStorage.setItem("weeklyGoal", weeklyGoal);
    localStorage.setItem("notifications", notifications ? "on" : "off");

    setMessage("Profile saved successfully.");
  };

  return (
    <div className="sf-page px-4 py-8 md:px-6">
      <div className="sf-shell max-w-4xl space-y-7">
        <header className="sf-card p-7 md:p-8">
          <h1 className="sf-title text-3xl font-bold text-white md:text-5xl">User Profile</h1>
          <p className="mt-3 text-base text-slate-300">Manage your account details and onboarding preferences.</p>
        </header>

        <form onSubmit={handleSave} className="space-y-6">
          <section className="sf-card p-7">
            <h2 className="font-space text-xl font-semibold text-white">User Info</h2>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <label className="space-y-2">
                <span className="text-sm text-slate-300">Name</span>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="sf-input"
                />
              </label>

              <label className="space-y-2">
                <span className="text-sm text-slate-300">Email</span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="sf-input"
                />
              </label>

              <label className="space-y-2 md:col-span-2">
                <span className="text-sm text-slate-300">Role</span>
                <input
                  type="text"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="sf-input"
                />
              </label>
            </div>
          </section>

          <section className="sf-card p-7">
            <h2 className="font-space text-xl font-semibold text-white">Saved Resume</h2>
            <label className="mt-4 block space-y-2">
              <span className="text-sm text-slate-300">Resume Link or File Name</span>
              <input
                type="text"
                value={savedResume}
                onChange={(e) => setSavedResume(e.target.value)}
                placeholder="resume.pdf"
                className="sf-input"
              />
            </label>
          </section>

          <section className="sf-card p-7">
            <h2 className="font-space text-xl font-semibold text-white">Preferences</h2>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <label className="space-y-2">
                <span className="text-sm text-slate-300">Weekly Learning Goal (hours)</span>
                <input
                  type="number"
                  min="1"
                  max="40"
                  value={weeklyGoal}
                  onChange={(e) => setWeeklyGoal(e.target.value)}
                  className="sf-input"
                />
              </label>

              <label className="flex items-center justify-between rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-2.5">
                <span className="text-sm text-slate-300">Email Notifications</span>
                <input
                  type="checkbox"
                  checked={notifications}
                  onChange={(e) => setNotifications(e.target.checked)}
                  className="h-4 w-4 accent-cyan-400"
                />
              </label>
            </div>
          </section>

          <div className="flex items-center gap-3">
            <button type="submit" className="sf-btn-primary px-5 py-2.5">
              Save Profile
            </button>
            {message && <p className="text-sm text-emerald-300">{message}</p>}
          </div>
        </form>
      </div>
    </div>
  );
}

export default Profile;
