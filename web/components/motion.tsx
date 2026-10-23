"use client";

import {
  motion,
  useScroll,
  useSpring,
  useTransform,
  type Variants,
} from "framer-motion";
import Link from "next/link";
import { useRef, type ComponentProps, type ReactNode } from "react";

/** Hairline that fills left-to-right with page scroll. */
export function ScrollProgress({ className = "" }: { className?: string }) {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 140, damping: 30, mass: 0.3 });
  return (
    <motion.div
      aria-hidden
      style={{ scaleX }}
      className={`pointer-events-none absolute inset-x-0 bottom-[-1px] h-px origin-left bg-blue ${className}`}
    />
  );
}

/** Drifts its content vertically as it crosses the viewport. */
export function Parallax({
  children,
  className,
  distance = 40,
}: {
  children: ReactNode;
  className?: string;
  distance?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], [distance, -distance]);
  return (
    <motion.div ref={ref} style={{ y }} className={className}>
      {children}
    </motion.div>
  );
}

export const ease = [0.22, 1, 0.36, 1] as const;

const container: Variants = {
  hidden: {},
  show: (stagger: number = 0.08) => ({
    transition: { staggerChildren: stagger, delayChildren: 0.05 },
  }),
};

export const rise: Variants = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.7, ease } },
};

/** Staggers its StaggerItem children in on mount. */
export function Stagger({
  children,
  className,
  stagger = 0.08,
  inView = false,
}: {
  children: ReactNode;
  className?: string;
  stagger?: number;
  inView?: boolean;
}) {
  return (
    <motion.div
      className={className}
      variants={container}
      custom={stagger}
      initial="hidden"
      {...(inView
        ? { whileInView: "show", viewport: { once: true, margin: "-60px" } }
        : { animate: "show" })}
    >
      {children}
    </motion.div>
  );
}

export function StaggerItem({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <motion.div className={className} variants={rise}>
      {children}
    </motion.div>
  );
}

const lift = {
  whileHover: { y: -2 },
  whileTap: { y: 0, scale: 0.985 },
  transition: { duration: 0.25, ease },
};

/** Card that lifts 2px and gains a soft shadow on hover. */
export function LiftCard({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <motion.div
      {...lift}
      whileTap={undefined}
      className={`transition-shadow duration-300 hover:shadow-lift ${className}`}
    >
      {children}
    </motion.div>
  );
}

const MotionLink = motion.create(Link);

export function LiftLink({
  className = "",
  ...props
}: ComponentProps<typeof MotionLink>) {
  return (
    <MotionLink
      {...lift}
      {...props}
      className={`inline-block transition-shadow duration-300 hover:shadow-lift ${className}`}
    />
  );
}

export function LiftButton({
  className = "",
  ...props
}: ComponentProps<typeof motion.button>) {
  return (
    <motion.button
      {...lift}
      {...props}
      className={`transition-shadow duration-300 hover:shadow-lift disabled:pointer-events-none ${className}`}
    />
  );
}
