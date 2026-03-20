import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

function Login() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSignup, setIsSignup] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    try {
      if (isSignup) {
        await axios.post("/api/auth/signup", { name, email, password });
      }

      const res = await axios.post("/api/auth/login", {
        email,
        password,
      });

      localStorage.setItem("token", res.data.token);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data || "Authentication failed");
    }
  };

  return (
    <div className="sf-page relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute -left-24 -top-24 h-72 w-72 rounded-full bg-cyan-500/20 blur-3xl" />
        <div className="absolute -bottom-24 right-0 h-72 w-72 rounded-full bg-indigo-500/20 blur-3xl" />
      </div>

      <div className="sf-shell grid min-h-screen grid-cols-1 items-center gap-14 px-6 py-12 md:grid-cols-2 md:px-8">
        <section className="space-y-6 md:pr-10">
          <p className="inline-flex rounded-full border border-cyan-300/30 bg-cyan-300/10 px-4 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-cyan-200">
            SkillForge AI
          </p>
          <h1 className="sf-title text-4xl font-bold leading-tight text-white md:text-6xl">
            Build Smarter Teams With Adaptive AI Onboarding
          </h1>
          <p className="max-w-md text-base leading-relaxed text-slate-300 md:text-lg">
            Personalized onboarding journeys that identify skill gaps, recommend precise learning steps, and accelerate time to productivity.
          </p>
        </section>

        <section>
          <div className="sf-card p-7 md:p-9">
            <h2 className="sf-title text-2xl font-semibold text-white md:text-3xl">
              {isSignup ? "Create your account" : "Welcome back"}
            </h2>
            <p className="mt-2 text-sm text-slate-300">
              {isSignup ? "Start your AI onboarding journey." : "Sign in to continue."}
            </p>

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              {isSignup && (
                <div className="space-y-2">
                  <label htmlFor="name" className="text-sm text-slate-200">
                    Name
                  </label>
                  <input
                    id="name"
                    type="text"
                    placeholder="Enter your name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="sf-input"
                  />
                </div>
              )}

              <div className="space-y-2">
                <label htmlFor="email" className="text-sm text-slate-200">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="sf-input"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="text-sm text-slate-200">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="sf-input"
                />
              </div>

              <button
                type="submit"
                className="sf-btn-primary w-full px-4 py-3"
              >
                {isSignup ? "Signup" : "Login"}
              </button>
            </form>

            {error && <p className="mt-4 text-sm text-rose-300">{error}</p>}

            <button
              onClick={() => setIsSignup((prev) => !prev)}
              className="mt-5 text-sm text-slate-300 transition hover:text-cyan-200"
            >
              {isSignup ? "Already have an account? Login" : "Don't have an account? Sign up"}
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}

export default Login;
