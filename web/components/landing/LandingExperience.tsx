"use client";

import { motion, useScroll, useSpring, useTransform } from "framer-motion";
import { useRef } from "react";
import { LandingHeader } from "@/components/landing/LandingHeader";
import { PipelineRail } from "@/components/landing/PipelineRail";
import { RoadBackground } from "@/components/landing/RoadScene";
import { LiftCard, LiftLink, Parallax, Stagger, StaggerItem } from "@/components/motion";
import { Reveal } from "@/components/Reveal";

const signals = ["EAR", "MAR", "PERCLOS", "PITCH / YAW", "YOLO v11"];

const features = [
  {
    index: "01",
    title: "Drowsiness",
    body: "Eye aspect ratio is smoothed across a rolling window and fused with PERCLOS and closure duration — so a long blink never reads as sleep, and microsleep never reads as a blink.",
    signals: ["Eye aspect ratio", "PERCLOS", "Closure duration", "Blink rate"],
  },
  {
    index: "02",
    title: "Yawn cadence",
    body: "Mouth aspect ratio is tracked over time rather than per frame. Completed yawns are counted and recent clusters weighted, because cadence predicts fatigue far better than any single event.",
    signals: ["Mouth aspect ratio", "Yawn count", "Recent cluster"],
  },
  {
    index: "03",
    title: "Distraction",
    body: "Head pose contributes direction and dwell time; a periodic YOLO pass locates the phone. Held together, looking down with a phone in hand scores far higher than either signal alone.",
    signals: ["Head direction", "Dwell time", "Phone confidence", "Fusion score"],
  },
];

const glass = "rounded-2xl border border-line bg-canvas/70 backdrop-blur-xl";

export function LandingExperience() {
  const driftRef = useRef<HTMLElement>(null);

  // Opacity is driven from spring values, never raw scroll: Framer hands raw
  // scroll-linked opacity to a native ViewTimeline that mis-maps keyframe offsets.
  const { scrollYProgress } = useScroll();
  const progress = useSpring(scrollYProgress, { stiffness: 110, damping: 28, mass: 0.35 });

  const { scrollYProgress: driftRaw } = useScroll({
    target: driftRef,
    offset: ["start end", "end start"],
  });
  const drift = useSpring(driftRaw, { stiffness: 110, damping: 28, mass: 0.35 });

  const heroOpacity = useTransform(progress, [0, 0.08], [1, 0]);
  const heroY = useTransform(progress, [0, 0.08], [0, -50]);
  const driftCopyOpacity = useTransform(drift, [0.15, 0.3, 0.7, 0.85], [0, 1, 1, 0]);

  return (
    <div className="relative isolate min-h-screen">
      <RoadBackground progress={progress} drift={drift} />
      <LandingHeader />

      {/* Hero */}
      <section className="relative flex min-h-screen flex-col">
        <motion.div
          style={{ opacity: heroOpacity, y: heroY }}
          className="mx-auto w-full max-w-[1140px] px-6 pt-28 md:pt-32"
        >
          <Stagger stagger={0.1}>
            <StaggerItem>
              <p className="label">Real-time vigilance, powered by foresight</p>
            </StaggerItem>
            <StaggerItem>
              <h1 className="mt-7 max-w-[15ch] text-[44px] font-extrabold leading-[0.98] tracking-[-0.045em] text-ink md:text-[76px]">
                Watch the driver, not just the road.
              </h1>
            </StaggerItem>
            <StaggerItem>
              <p className="mt-8 max-w-[52ch] text-[17px] leading-relaxed text-ink-2 md:text-[19px]">
                Drishti reads ocular state, yawn cadence, head pose and phone use
                from a single camera — then calls the risk out loud, before it
                becomes an incident.
              </p>
            </StaggerItem>
            <StaggerItem>
              <div className="mt-12 flex flex-wrap items-center gap-3">
                <LiftLink
                  href="/dashboard"
                  className="rounded-full bg-blue px-7 py-3 text-[14px] font-semibold text-blue-on"
                >
                  Launch dashboard
                </LiftLink>
                <LiftLink
                  href="#capability"
                  className="rounded-full border border-line-strong bg-canvas/60 px-7 py-3 text-[14px] font-semibold text-ink backdrop-blur"
                >
                  What it measures
                </LiftLink>
              </div>
            </StaggerItem>
          </Stagger>
        </motion.div>

        <motion.div
          style={{ opacity: heroOpacity }}
          className="pointer-events-none mt-auto flex flex-col items-center gap-3 pb-8"
        >
          <span className="label">Scroll to drive</span>
          <span className="relative h-10 w-px overflow-hidden bg-line-strong">
            <motion.span
              className="absolute inset-x-0 h-3 bg-ink"
              animate={{ y: [-12, 40] }}
              transition={{ duration: 1.8, repeat: Infinity, ease: [0.65, 0, 0.35, 1] }}
            />
          </span>
        </motion.div>
      </section>

      <main className="mx-auto max-w-[1140px] px-6">
        {/* Caption — what it watches */}
        <section className="flex min-h-[80vh] items-start pt-[12vh]">
          <Parallax distance={40}>
            <Reveal>
              <p className="label">Every frame, both ways</p>
              <h2 className="mt-5 max-w-[18ch] text-[36px] font-bold leading-[1.02] tracking-[-0.04em] text-ink md:text-[58px]">
                Your eyes are on the road. Ours are on you.
              </h2>
              <div className="mt-8 flex flex-wrap gap-x-8 gap-y-2">
                {[
                  ["EAR", "0.31"],
                  ["PERCLOS", "0.04"],
                  ["HEAD", "Forward"],
                  ["PHONE", "Clear"],
                ].map(([k, v]) => (
                  <span key={k} className="num text-[12px] text-ink-3">
                    {k} <span className="text-ink">{v}</span>
                  </span>
                ))}
              </div>
            </Reveal>
          </Parallax>
        </section>

        {/* Signal strip */}
        <Stagger
          className={`${glass} flex flex-wrap items-center gap-x-8 gap-y-3 px-7 py-5`}
          stagger={0.06}
          inView
        >
          <StaggerItem>
            <span className="label">Signals</span>
          </StaggerItem>
          {signals.map((signal) => (
            <StaggerItem key={signal}>
              <span className="num text-[12px] font-medium text-ink-2">{signal}</span>
            </StaggerItem>
          ))}
          <StaggerItem className="ml-auto">
            <span className="num text-[12px] text-ink-3">single camera · on-device</span>
          </StaggerItem>
        </Stagger>

        {/* Capability */}
        <section id="capability" className="scroll-mt-24 pt-32 pb-24">
          <Parallax distance={24}>
            <Reveal>
              <h2 className="max-w-[20ch] text-[30px] font-bold leading-[1.1] tracking-[-0.035em] text-ink md:text-[40px]">
                Three independent signals, weighed against each other.
              </h2>
            </Reveal>
          </Parallax>

          <Stagger className="mt-14 grid gap-4 md:grid-cols-3" stagger={0.12} inView>
            {features.map((feature) => (
              <StaggerItem key={feature.index} className="h-full">
                <LiftCard className="flex h-full flex-col rounded-xl border border-line bg-canvas/85 p-8 backdrop-blur-xl md:p-9">
                  <span className="num text-[12px] font-medium text-blue">{feature.index}</span>
                  <h3 className="mt-6 text-[21px] font-bold tracking-[-0.025em] text-ink">
                    {feature.title}
                  </h3>
                  <p className="mt-4 text-[14px] leading-relaxed text-ink-2">{feature.body}</p>
                  <div className="pt-8">
                    <ul className="space-y-2.5 border-t border-line pt-6">
                      {feature.signals.map((signal) => (
                        <li
                          key={signal}
                          className="num flex items-center gap-2.5 text-[11px] text-ink-3"
                        >
                          <span className="h-px w-3 bg-line-strong" />
                          {signal}
                        </li>
                      ))}
                    </ul>
                  </div>
                </LiftCard>
              </StaggerItem>
            ))}
          </Stagger>
        </section>
      </main>

      {/* The lapse — road left clear so the drift reads */}
      <section ref={driftRef} className="relative h-[200vh]">
        <motion.div
          style={{ opacity: driftCopyOpacity }}
          className="sticky top-[16vh] mx-auto max-w-[1140px] px-6"
        >
          <p className="label">Foresight</p>
          <h2 className="mt-5 max-w-[16ch] text-[36px] font-bold leading-[1.02] tracking-[-0.04em] text-ink md:text-[58px]">
            Fatigue builds quietly. Drishti notices first.
          </h2>
          <p className="mt-6 max-w-[46ch] text-[15px] leading-relaxed text-ink-2">
            Watch the car ahead. A half-second drift toward the centre line is
            the kind of lapse Drishti flags — before the driver knows it happened.
          </p>
        </motion.div>
      </section>

      <main className="mx-auto max-w-[1140px] px-6">
        <div className={`${glass} px-7`}>
          <PipelineRail />
        </div>

        {/* Close */}
        <section className="py-28 md:py-36">
          <Reveal y={28}>
            <div className={`${glass} flex flex-col items-start justify-between gap-10 p-8 md:flex-row md:items-end md:p-12`}>
              <h2 className="max-w-[16ch] text-[30px] font-bold leading-[1.1] tracking-[-0.035em] text-ink md:text-[44px]">
                The camera is already there. Put it to work.
              </h2>
              <LiftLink
                href="/dashboard"
                className="shrink-0 rounded-full bg-ink px-8 py-3.5 text-[14px] font-semibold text-canvas"
              >
                Launch dashboard
              </LiftLink>
            </div>
          </Reveal>
        </section>
      </main>

      <footer className="border-t border-line bg-canvas/70 backdrop-blur-xl">
        <Reveal y={8}>
          <div className="mx-auto flex max-w-[1140px] flex-col gap-3 px-6 py-8 md:flex-row md:items-center md:justify-between">
            <p className="text-[13px] font-semibold text-ink">Drishti</p>
            <p className="num text-[11px] text-ink-3">Real-time vigilance, powered by foresight</p>
          </div>
        </Reveal>
      </footer>
    </div>
  );
}
