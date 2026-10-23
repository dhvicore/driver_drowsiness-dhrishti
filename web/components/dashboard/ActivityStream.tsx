"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { PulseDot } from "@/components/PulseDot";
import { ease } from "@/components/motion";
import type { DrishtiEvent } from "@/lib/drishti";

type Kind = "Drowsiness" | "Distraction" | "Yawn" | "Phone" | "Session" | "Status";

const KINDS: Kind[] = ["Drowsiness", "Distraction", "Yawn", "Phone"];

function kindOf(message: string): Kind {
  const m = message.toLowerCase();
  if (m.includes("phone")) return "Phone";
  if (m.includes("yawn")) return "Yawn";
  if (m.includes("distract") || m.includes("not in frame")) return "Distraction";
  if (m.includes("drows") || m.includes("fatigue") || m.includes("closure") || m.includes("critical"))
    return "Drowsiness";
  if (m.includes("session")) return "Session";
  return "Status";
}

function useNow(interval = 1000) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), interval);
    return () => clearInterval(id);
  }, [interval]);
  return now;
}

function ago(at: number, now: number) {
  const s = Math.max(0, Math.round(now / 1000 - at));
  if (s < 5) return "now";
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  return `${Math.floor(m / 60)}h ago`;
}

const dot = {
  critical: "bg-burgundy",
  warning: "bg-ink-2",
  info: "bg-blue",
} as const;

export function ActivityStream({
  events,
  running,
  healthy,
  className = "",
}: {
  events: DrishtiEvent[];
  running: boolean;
  healthy: boolean;
  className?: string;
}) {
  const now = useNow();

  const counts = useMemo(() => {
    const tally = Object.fromEntries(KINDS.map((k) => [k, 0])) as Record<Kind, number>;
    for (const e of events) {
      const k = kindOf(e.message);
      if (k in tally && e.level !== "info") tally[k] += 1;
    }
    return tally;
  }, [events]);

  return (
    <section
      className={`flex min-h-0 flex-col overflow-hidden rounded-xl border border-line bg-surface ${className}`}
    >
      <header className="flex h-11 shrink-0 items-center justify-between border-b border-line px-5">
        <h2 className="label">Activity</h2>
        <div className="flex items-center gap-2">
          <PulseDot active={running && healthy} tone={running ? "bg-burgundy" : "bg-ink-3"} />
          <span className="num text-[10px] font-semibold uppercase tracking-[0.12em] text-ink-3">
            {running ? "Streaming" : "Paused"}
          </span>
        </div>
      </header>

      <div className="grid shrink-0 grid-cols-4 border-b border-line">
        {KINDS.map((k, i) => (
          <div key={k} className={`px-3 py-3 ${i ? "border-l border-line" : ""}`}>
            <p className="truncate text-[10px] font-medium text-ink-3">{k}</p>
            <motion.p
              key={counts[k]}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, ease }}
              className={`num mt-1 text-[15px] font-semibold ${
                counts[k] ? "text-ink" : "text-ink-3"
              }`}
            >
              {counts[k]}
            </motion.p>
          </div>
        ))}
      </div>

      {events.length === 0 ? (
        <div className="grid flex-1 place-items-center px-6 py-14 text-center">
          <div>
            <p className="text-[13px] font-medium text-ink-2">
              {running ? "Listening for events" : "No session activity"}
            </p>
            <p className="num mt-2 text-[11px] text-ink-3">
              Drowsiness, yawns, distraction and phone use appear here.
            </p>
          </div>
        </div>
      ) : (
        <ol className="relative min-h-0 flex-1 overflow-y-auto px-5 py-4">
          <span aria-hidden className="absolute bottom-4 left-[23px] top-4 w-px bg-line" />
          <AnimatePresence initial={false}>
            {events.map((event, i) => {
              const kind = kindOf(event.message);
              return (
                <motion.li
                  key={event.id}
                  layout="position"
                  initial={{ opacity: 0, x: -6, height: 0 }}
                  animate={{ opacity: 1, x: 0, height: "auto" }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.45, ease }}
                  className="relative overflow-hidden"
                >
                  <div className="flex gap-4 py-2.5">
                    <span className="relative z-10 mt-[5px] grid h-2 w-2 shrink-0 place-items-center rounded-full bg-surface">
                      <span
                        className={`h-[7px] w-[7px] rounded-full ${dot[event.level]} ${
                          i === 0 && running ? "" : "opacity-80"
                        }`}
                      />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p
                        className={`text-[13px] leading-snug ${
                          event.level === "critical"
                            ? "font-semibold text-burgundy"
                            : "text-ink"
                        }`}
                      >
                        {event.message}
                      </p>
                      <div className="mt-1 flex items-center gap-2">
                        <span className="text-[10px] font-semibold uppercase tracking-[0.1em] text-ink-3">
                          {kind}
                        </span>
                        <span className="h-2.5 w-px bg-line" />
                        <span className="num text-[10.5px] text-ink-3">
                          {new Date(event.at * 1000).toLocaleTimeString([], {
                            hour12: false,
                          })}
                        </span>
                      </div>
                    </div>
                    <span className="num shrink-0 pt-[2px] text-[10.5px] text-ink-3">
                      {ago(event.at, now)}
                    </span>
                  </div>
                </motion.li>
              );
            })}
          </AnimatePresence>
        </ol>
      )}
    </section>
  );
}
