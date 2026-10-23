"use client";

import { motion, useMotionValueEvent, useScroll, useSpring } from "framer-motion";
import { useRef, useState } from "react";

const steps = [
  ["Capture", "1280×720 frame, mirrored"],
  ["Landmarks", "478-point face mesh"],
  ["Temporal fusion", "EAR · MAR · PERCLOS"],
  ["Risk score", "Drowsiness + distraction"],
  ["Alert", "Status, log, overlay"],
];

/** Pipeline steps that light up in order as the rail fills with scroll. */
export function PipelineRail() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start 85%", "end 45%"] });
  const fill = useSpring(scrollYProgress, { stiffness: 120, damping: 30 });
  const [reached, setReached] = useState(-1);

  useMotionValueEvent(fill, "change", (v) => {
    setReached(Math.floor(v * steps.length - 0.001));
  });

  return (
    <div ref={ref} className="py-10">
      <div className="flex items-center justify-between">
        <span className="label">Pipeline</span>
        <span className="num text-[11px] text-ink-3">per frame · ~30 fps</span>
      </div>

      <div className="relative mt-10">
        <div className="absolute left-0 right-0 top-[5px] h-px bg-line" />
        <motion.div
          style={{ scaleX: fill }}
          className="absolute left-0 right-0 top-[5px] h-px origin-left bg-blue"
        />
        <ol className="relative grid grid-cols-2 gap-y-8 md:grid-cols-5">
          {steps.map(([name, detail], i) => {
            const on = i <= reached;
            return (
              <li key={name} className="pr-4">
                <span
                  className={`block h-[11px] w-[11px] rounded-full border-2 transition-colors duration-500 ${
                    on ? "border-blue bg-blue" : "border-line-strong bg-canvas"
                  }`}
                />
                <p
                  className={`mt-5 text-[14px] font-semibold transition-colors duration-500 ${
                    on ? "text-ink" : "text-ink-3"
                  }`}
                >
                  {name}
                </p>
                <p className="num mt-1.5 text-[11px] text-ink-3">{detail}</p>
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
