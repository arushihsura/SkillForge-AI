import React from "react";
import { Link } from "react-router-dom";
import ThemeToggle from "./ThemeToggle";

const Navbar = () => {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-transparent backdrop-blur-md border-b border-white/10">
      <div className="sf-shell px-6 h-20 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-indigo-500 flex items-center justify-center sf-card border-none group-hover:scale-105 transition-transform">
            <span className="text-white font-bold text-xl">S</span>
          </div>
          <span className="sf-title text-2xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70">
            SkillForge<span className="text-cyan-400">AI</span>
          </span>
        </Link>

        <div className="flex items-center gap-8">
          <div className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-400">
            <Link to="/dashboard" className="hover:text-white transition-colors">Dashboard</Link>
            <Link to="/history" className="hover:text-white transition-colors">History</Link>
            <Link to="/profile" className="hover:text-white transition-colors">Profile</Link>
          </div>
          
          <div className="h-6 w-[1px] bg-white/10 mx-2 hidden md:block" />
          
          <ThemeToggle />
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
