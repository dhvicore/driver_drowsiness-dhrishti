import { useId } from "react";

/**
 * Drishti mark: an open eye whose lower lid is a steering wheel, with a
 * trailing "Zzz". Colours follow the theme via CSS variables.
 */
export function LogoMark({
  className = "h-7 w-auto",
  zzz = true,
}: {
  className?: string;
  zzz?: boolean;
}) {
  const id = useId().replace(/:/g, "");
  const iris = `iris-${id}`;
  const metal = `metal-${id}`;
  const wheel = `wheel-${id}`;

  return (
    <svg
      viewBox={zzz ? "335 375 600 495" : "335 440 580 430"}
      className={className}
      role="img"
      aria-label="Drishti"
    >
      <defs>
        <radialGradient id={iris} cx="0.45" cy="0.42" r="0.62">
          <stop offset="0" stopColor="#c3d5ff" />
          <stop offset="1" stopColor="#6d8ee2" />
        </radialGradient>
        <linearGradient id={metal} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="var(--logo-metal-hi)" />
          <stop offset="1" stopColor="var(--logo-metal)" />
        </linearGradient>
        <mask id={wheel} maskUnits="userSpaceOnUse" x="335" y="375" width="600" height="495">
          <circle cx="627" cy="790" r="122" fill="#fff" />
          <circle cx="627" cy="790" r="90" fill="#000" />
          <path d="M520 752 Q627 728 734 752 L734 797 L520 797 Z" fill="#fff" />
          <rect x="604" y="780" width="46" height="90" fill="#fff" />
          <circle cx="627" cy="779" r="17" fill="#000" />
          <rect x="335" y="852" width="600" height="20" fill="#000" />
        </mask>
      </defs>

      {/* eye outline */}
      <path
        d="M355 640 Q627 330 900 640 Q627 900 355 640 Z"
        fill="none"
        stroke={`url(#${metal})`}
        strokeWidth="30"
      />

      {/* iris, pupil, catch-light */}
      <circle cx="627" cy="640" r="135" fill={`url(#${iris})`} />
      <circle cx="627" cy="640" r="70" fill="#0b0e17" />
      <circle cx="660" cy="611" r="14" fill="#f4f7ff" />

      {/* separation gap, dark wheel well, then the wheel */}
      <circle cx="627" cy="790" r="129" fill="none" stroke="var(--canvas)" strokeWidth="14" />
      <path d="M537 790 A90 90 0 0 1 717 790 V852 H537 Z" fill="#0b0e17" />
      <rect
        x="490"
        y="660"
        width="275"
        height="200"
        fill={`url(#${metal})`}
        mask={`url(#${wheel})`}
      />

      {zzz && (
        <g
          fill="none"
          stroke="var(--logo-z)"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M872 398 H914 L872 440 H916" strokeWidth="15" />
          <path d="M810 447 H849 L810 489 H851" strokeWidth="14" />
          <path d="M861 518 H887 L861 543 H889" strokeWidth="10" />
        </g>
      )}
    </svg>
  );
}
