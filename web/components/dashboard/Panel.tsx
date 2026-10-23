import type { ReactNode } from "react";
import { LiftCard } from "@/components/motion";

export function Panel({
  title,
  aside,
  children,
  className = "",
  bodyClass = "p-5",
  lift = false,
}: {
  title?: string;
  aside?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClass?: string;
  lift?: boolean;
}) {
  const shell = `flex flex-col overflow-hidden rounded-xl border border-line bg-surface ${className}`;
  const body = (
    <>
      {title && (
        <header className="flex h-11 shrink-0 items-center justify-between border-b border-line px-5">
          <h2 className="label">{title}</h2>
          {aside}
        </header>
      )}
      <div className={`flex-1 ${bodyClass}`}>{children}</div>
    </>
  );

  return lift ? (
    <LiftCard className={shell}>{body}</LiftCard>
  ) : (
    <section className={shell}>{body}</section>
  );
}

export function Row({
  label,
  value,
  tone = "",
}: {
  label: string;
  value: ReactNode;
  tone?: string;
}) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-[7px]">
      <span className="text-[12.5px] text-ink-3">{label}</span>
      <span className={`num text-[12.5px] font-medium ${tone || "text-ink"}`}>
        {value}
      </span>
    </div>
  );
}

export function Meter({
  label,
  value,
  max = 100,
}: {
  label: string;
  value: number;
  max?: number;
}) {
  const pct = Math.min(100, (value / max) * 100);
  const hot = pct >= 60;

  return (
    <div>
      <div className="flex items-baseline justify-between">
        <span className="text-[12.5px] text-ink-3">{label}</span>
        <span
          className={`num text-[13px] font-semibold ${hot ? "text-burgundy" : "text-ink"}`}
        >
          {Math.round(value)}
          <span className="text-ink-3">/{max}</span>
        </span>
      </div>
      <div className="mt-2.5 h-[3px] overflow-hidden rounded-full bg-raised">
        <div
          className={`h-full rounded-full transition-[width,background-color] duration-500 ease-out ${
            hot ? "bg-burgundy" : "bg-blue"
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
