"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ActivityStream } from "@/components/dashboard/ActivityStream";
import { Meter, Panel, Row } from "@/components/dashboard/Panel";
import { useDrishti } from "@/components/dashboard/useDrishti";
import { ease, LiftButton, ScrollProgress, Stagger, StaggerItem } from "@/components/motion";
import { PulseDot } from "@/components/PulseDot";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Wordmark } from "@/components/Wordmark";
import { API, formatDuration, toneFor } from "@/lib/drishti";

function titleCase(value: string) {
  return value
    .toLowerCase()
    .split(" ")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export default function Dashboard() {
  const { snapshot, online, pending, streamKey, start, stop, setOverlay } =
    useDrishti();
  const { metrics: m, running, totals, events } = snapshot;
  const tone = toneFor(running ? m.severity : 0);
  const healthy = running && m.face && m.severity === 0;

  return (
    <div className="min-h-screen bg-canvas">
      <header className="sticky top-0 z-50 border-b border-line bg-canvas/85 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-[1440px] items-center justify-between gap-6 px-6">
          <div className="flex items-center gap-6">
            <Wordmark />
            <span className="hidden h-4 w-px bg-line sm:block" />
            <span className="label hidden sm:block">Live monitor</span>
          </div>

          <div className="flex items-center gap-5">
            <div className="hidden items-center gap-2.5 sm:flex">
              <PulseDot
                active={healthy}
                tone={
                  online === false || (running && m.severity >= 2)
                    ? "bg-burgundy"
                    : running
                      ? "bg-ink-2"
                      : "bg-ink-3"
                }
              />
              <span className="num text-[11px] text-ink-3">
                {online === false
                  ? "backend offline"
                  : running
                    ? `${snapshot.fps.toFixed(0)} fps`
                    : "standby"}
              </span>
            </div>
            <span className="num text-[13px] font-medium text-ink tabular-nums">
              {formatDuration(snapshot.duration)}
            </span>
            <ThemeToggle />
          </div>
        </div>
        <ScrollProgress />
      </header>

      <main className="mx-auto max-w-[1440px] px-6 py-6">
        <AnimatePresence>
          {(online === false || snapshot.error) && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.4, ease }}
              className="overflow-hidden"
            >
              <div className="mb-6 rounded-xl border border-burgundy bg-burgundy-wash px-5 py-3.5">
                <p className="text-[13px] font-medium text-burgundy">
                  {online === false
                    ? "Backend unreachable — start it with: python server.py"
                    : snapshot.error}
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <Stagger
          className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_380px]"
          stagger={0.09}
        >
          {/* Left: camera + signal groups */}
          <div className="flex min-w-0 flex-col gap-6">
            <StaggerItem>
              <Panel
                title="Camera"
                bodyClass=""
                aside={
                  <button
                    onClick={() => setOverlay(!snapshot.raw_overlay)}
                    className={`num text-[10px] font-semibold uppercase tracking-[0.12em] transition-colors duration-300 ${
                      snapshot.raw_overlay ? "text-blue" : "text-ink-3 hover:text-ink"
                    }`}
                  >
                    Raw overlay
                  </button>
                }
              >
                <div className="relative aspect-video w-full overflow-hidden bg-raised">
                  <AnimatePresence mode="wait">
                    {running ? (
                      <motion.img
                        key={`stream-${streamKey}`}
                        src={`${API}/api/stream?s=${streamKey}`}
                        alt="Driver camera"
                        initial={{ opacity: 0, scale: 1.01 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.6, ease }}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <motion.div
                        key="idle"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.4 }}
                        className="absolute inset-0 grid place-items-center"
                      >
                        <div className="text-center">
                          <p className="text-[14px] font-medium text-ink-2">Camera idle</p>
                          <p className="num mt-2 text-[11px] text-ink-3">
                            Start monitoring to open the feed
                          </p>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  <AnimatePresence>
                    {running && (
                      <motion.div
                        initial={{ opacity: 0, y: -4 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.4, ease }}
                        className="pointer-events-none absolute left-4 top-4 flex items-center gap-2 rounded-full bg-canvas/90 px-3 py-1.5 backdrop-blur"
                      >
                        <motion.span
                          animate={{ opacity: [1, 0.3, 1] }}
                          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                          className="h-1.5 w-1.5 rounded-full bg-burgundy"
                        />
                        <span className="num text-[10px] font-semibold uppercase tracking-[0.12em] text-ink">
                          Live
                        </span>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-4 border-t border-line px-5 py-4">
                  <LiftButton
                    onClick={running ? stop : start}
                    disabled={pending || online === false}
                    className={`rounded-full px-6 py-2.5 text-[13px] font-semibold disabled:opacity-40 ${
                      running ? "bg-burgundy text-burgundy-on" : "bg-ink text-canvas"
                    }`}
                  >
                    {pending ? "Working…" : running ? "Stop monitoring" : "Start monitoring"}
                  </LiftButton>

                  <div className="flex items-center gap-7">
                    <Stat label="Blinks" value={totals.blinks} />
                    <Stat label="Yawns" value={totals.yawns} />
                    <Stat label="Closures" value={totals.long_closures} hot />
                    <Stat label="Phone" value={totals.phone_events} hot />
                  </div>
                </div>
              </Panel>
            </StaggerItem>

            <StaggerItem>
              <Stagger className="grid gap-6 sm:grid-cols-2" stagger={0.08} inView>
                <StaggerItem>
                <Panel title="Ocular" lift>
                  <Row label="EAR" value={m.ear.toFixed(3)} />
                  <Row label="PERCLOS" value={m.perclos.toFixed(2)} />
                  <Row label="Closed for" value={`${m.closed_duration.toFixed(1)}s`} />
                  <Row label="Blinks" value={m.blinks} />
                </Panel>
                </StaggerItem>

                <StaggerItem>
                <Panel title="Yawn" lift>
                  <Row label="MAR" value={m.mar.toFixed(3)} />
                  <Row
                    label="State"
                    value={m.yawn ? "Yawning" : "Clear"}
                    tone={m.yawn ? "text-burgundy" : undefined}
                  />
                  <Row label="Total" value={m.yawn_count} />
                  <Row label="Recent" value={m.recent_yawns} />
                </Panel>
                </StaggerItem>

                <StaggerItem>
                <Panel title="Head pose" lift>
                  <Row label="Direction" value={titleCase(m.head_direction)} />
                  <Row label="Pitch" value={m.pitch.toFixed(1)} />
                  <Row label="Yaw" value={m.yaw.toFixed(1)} />
                  <Row label="Dwell" value={`${m.head_duration.toFixed(1)}s`} />
                </Panel>
                </StaggerItem>

                <StaggerItem>
                <Panel title="Phone" lift>
                  <Row
                    label="State"
                    value={m.phone_using ? "In use" : m.phone_detected ? "Detected" : "Clear"}
                    tone={m.phone_using ? "text-burgundy" : undefined}
                  />
                  <Row label="Confidence" value={m.phone_confidence.toFixed(2)} />
                  <Row label="Duration" value={`${m.phone_duration.toFixed(1)}s`} />
                  <Row label="Source" value={titleCase(m.phone_source)} />
                </Panel>
                </StaggerItem>
              </Stagger>
            </StaggerItem>
          </div>

          {/* Right rail: status, risk, live activity */}
          <div className="flex flex-col gap-6">
            <StaggerItem>
              <section
                className={`overflow-hidden rounded-xl border transition-colors duration-500 ${tone.border} ${tone.bg}`}
              >
                <div className="flex items-center justify-between px-5 pt-5">
                  <p className="label">Driver status</p>
                  <PulseDot
                    active={healthy}
                    tone={running && m.severity >= 2 ? "bg-burgundy" : "bg-ink-3"}
                  />
                </div>
                <div className="px-5 pb-5 pt-4">
                  <AnimatePresence mode="wait">
                    <motion.p
                      key={running ? m.status : "standby"}
                      initial={{ opacity: 0, y: 8, filter: "blur(2px)" }}
                      animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                      exit={{ opacity: 0, y: -8, filter: "blur(2px)" }}
                      transition={{ duration: 0.4, ease }}
                      className={`text-[34px] font-extrabold leading-none tracking-[-0.04em] ${tone.text}`}
                    >
                      {titleCase(running ? m.status : "Standby")}
                    </motion.p>
                  </AnimatePresence>

                  <div className="mt-5 border-t border-current/15 pt-4">
                    <Row label="Attention" value={running ? titleCase(m.attention) : "—"} tone={tone.text} />
                    <Row label="Eyes" value={running ? titleCase(m.eye_state) : "—"} tone={tone.text} />
                    <Row label="Head" value={running ? titleCase(m.head_direction) : "—"} tone={tone.text} />
                  </div>
                </div>
              </section>
            </StaggerItem>

            <StaggerItem>
              <Panel title="Risk">
                <div className="space-y-5">
                  <Meter label="Drowsiness" value={m.drowsiness_score} />
                  <Meter label="Distraction" value={m.distraction_score} />
                  <Meter label="Evidence" value={m.evidence_score} />
                </div>
              </Panel>
            </StaggerItem>

            {/* Absolutely filled so the log scrolls instead of stretching the row */}
            <StaggerItem className="relative min-h-[420px] flex-1">
              <ActivityStream
                events={events}
                running={running}
                healthy={healthy}
                className="absolute inset-0"
              />
            </StaggerItem>
          </div>
        </Stagger>
      </main>
    </div>
  );
}

function Stat({ label, value, hot = false }: { label: string; value: number; hot?: boolean }) {
  return (
    <div className="text-right">
      <p className="label">{label}</p>
      <motion.p
        key={value}
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease }}
        className={`num mt-1 text-[15px] font-semibold ${hot && value ? "text-burgundy" : "text-ink"}`}
      >
        {value}
      </motion.p>
    </div>
  );
}
