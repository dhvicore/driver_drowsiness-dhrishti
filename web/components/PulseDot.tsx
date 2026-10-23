"use client";

import { motion } from "framer-motion";

/**
 * Status dot. When `active`, it breathes in sage: the core eases between
 * full and softened opacity while a thin ring expands and dissolves.
 */
export function PulseDot({
  active,
  tone = "bg-ink-3",
  size = 6,
}: {
  active: boolean;
  tone?: string;
  size?: number;
}) {
  return (
    <span
      className="relative inline-grid shrink-0 place-items-center"
      style={{ width: size, height: size }}
    >
      {active && (
        <motion.span
          aria-hidden
          className="absolute inset-0 rounded-full border border-sage"
          initial={{ scale: 1, opacity: 0.55 }}
          animate={{ scale: 2.8, opacity: 0 }}
          transition={{ duration: 2.6, repeat: Infinity, ease: "easeOut" }}
        />
      )}
      <motion.span
        className={`h-full w-full rounded-full transition-colors duration-500 ${
          active ? "bg-sage" : tone
        }`}
        animate={active ? { opacity: [1, 0.55, 1], scale: [1, 0.92, 1] } : { opacity: 1, scale: 1 }}
        transition={active ? { duration: 2.6, repeat: Infinity, ease: "easeInOut" } : { duration: 0.3 }}
      />
    </span>
  );
}
