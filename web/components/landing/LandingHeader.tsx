"use client";

import { LiftLink, ScrollProgress } from "@/components/motion";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Wordmark } from "@/components/Wordmark";

export function LandingHeader() {
  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-line bg-canvas/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-[1140px] items-center justify-between px-6">
        <Wordmark />
        <div className="flex items-center gap-3">
          <ThemeToggle />
          <LiftLink
            href="/dashboard"
            className="rounded-full bg-ink px-5 py-2 text-[13px] font-semibold text-canvas"
          >
            Launch dashboard
          </LiftLink>
        </div>
      </div>
      <ScrollProgress />
    </header>
  );
}
