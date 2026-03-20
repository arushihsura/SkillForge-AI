import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

const themes = [
  { id: "default", name: "Onyx", color: "#22d3ee" },
  { id: "emerald", name: "Emerald", color: "#34d399" },
  { id: "rose", name: "Midnight Rose", color: "#fb7185" },
  { id: "gold", name: "Royal Gold", color: "#ffb012" },
];

const ThemeToggle = () => {
  const [currentTheme, setCurrentTheme] = useState(localStorage.getItem("sf-theme") || "default");
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", currentTheme);
    localStorage.setItem("sf-theme", currentTheme);
  }, [currentTheme]);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="sf-btn-secondary px-4 py-2 flex items-center gap-2 border-opacity-40"
      >
        <div 
          className="w-3 h-3 rounded-full" 
          style={{ backgroundColor: themes.find(t => t.id === currentTheme).color }}
        />
        <span className="text-sm font-medium hidden md:block">
          {themes.find(t => t.id === currentTheme).name}
        </span>
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <div 
              className="fixed inset-0 z-10" 
              onClick={() => setIsOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              className="absolute right-0 mt-2 w-48 sf-card z-20 overflow-hidden"
            >
              <div className="p-2 flex flex-col gap-1">
                {themes.map((theme) => (
                  <button
                    key={theme.id}
                    onClick={() => {
                      setCurrentTheme(theme.id);
                      setIsOpen(false);
                    }}
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-left ${
                      currentTheme === theme.id ? "bg-white/10" : "hover:bg-white/5"
                    }`}
                  >
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: theme.color }}
                    />
                    <span className="text-sm">{theme.name}</span>
                    {currentTheme === theme.id && (
                      <div className="ml-auto w-1 h-1 rounded-full bg-white" />
                    )}
                  </button>
                ))}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ThemeToggle;
