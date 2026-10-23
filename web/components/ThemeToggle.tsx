"use client";

import { useEffect, useState } from "react";

export function ThemeToggle() {
  const [dark, setDark] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      setDark(document.documentElement.classList.contains("dark"));
      setReady(true);
    });
    return () => cancelAnimationFrame(frame);
  }, []);

  function toggle() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("drishti-theme", next ? "dark" : "light");
    } catch {}
  }

  return (
    <button
      onClick={toggle}
      aria-label="Toggle colour scheme"
      className="group relative h-8 w-8 rounded-full border border-line text-ink-3 transition-colors duration-300 hover:border-line-strong hover:text-ink"
    >
      <span
        className="absolute inset-0 grid place-items-center transition-all duration-300"
        style={{
          opacity: ready && dark ? 0 : 1,
          transform: `rotate(${ready && dark ? -90 : 0}deg) scale(${ready && dark ? 0.6 : 1})`,
        }}
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="4.5" />
          <path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.5 1.5M17.6 17.6l1.5 1.5M19.1 4.9l-1.5 1.5M6.4 17.6l-1.5 1.5" />
        </svg>
      </span>
      <span
        className="absolute inset-0 grid place-items-center transition-all duration-300"
        style={{
          opacity: ready && dark ? 1 : 0,
          transform: `rotate(${ready && dark ? 0 : 90}deg) scale(${ready && dark ? 1 : 0.6})`,
        }}
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a6.8 6.8 0 0 0 10.5 10.5Z" />
        </svg>
      </span>
    </button>
  );
}
