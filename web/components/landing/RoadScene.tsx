"use client";

import {
  useAnimationFrame,
  useMotionValueEvent,
  useReducedMotion,
  type MotionValue,
} from "framer-motion";
import { useEffect, useState } from "react";

/* ---------- perspective model ----------
 * World depth z (1 = bottom edge of the frame). A point at depth z lands at
 *   y = HORIZON + K / z,   x = VX + (xAtBottom - VX) / z
 * so everything converges on the vanishing point (VX, HORIZON).
 */
const W = 1920;
const H = 1080;
const HORIZON = 690;
const VX = 1005;
const K = 390;
const Z_NEAR = 0.8;
const Z_FAR = 90;

const sy = (z: number) => HORIZON + K / z;
const sx = (xb: number, z: number) => VX + (xb - VX) / z;

const LEFT_EDGE = 40;
const RIGHT_EDGE = 1880;
const CENTER = 935;
const LANE = (LEFT_EDGE + CENTER) / 2; // left-hand lane

const DASH_PERIOD = 1.1;
const DASH_LENGTH = 0.42;
const SCROLL_TRAVEL = 90; // world units covered from top to bottom of the page
const IDLE_SPEED = 0.18; // world units per second while not scrolling

/** On narrow screens, pan the frame left so the car's lane stays in view. */
function useViewBox() {
  const [box, setBox] = useState(`0 0 ${W} ${H}`);
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 640px)");
    const apply = () => setBox(`${mq.matches ? -150 : 0} 0 ${W} ${H}`);
    apply();
    mq.addEventListener("change", apply);
    return () => mq.removeEventListener("change", apply);
  }, []);
  return box;
}

function lerpKeys(p: number, input: number[], output: number[]) {
  if (p <= input[0]) return output[0];
  for (let i = 1; i < input.length; i++) {
    if (p <= input[i]) {
      const t = (p - input[i - 1]) / (input[i] - input[i - 1]);
      const s = t * t * (3 - 2 * t);
      return output[i - 1] + (output[i] - output[i - 1]) * s;
    }
  }
  return output[output.length - 1];
}

function edgePolygon(xb: number, width: number) {
  const a = sx(xb, Z_NEAR);
  const b = sx(xb, Z_FAR);
  return `${a - width / Z_NEAR},${sy(Z_NEAR)} ${a + width / Z_NEAR},${sy(Z_NEAR)} ${
    b + width / Z_FAR
  },${sy(Z_FAR)} ${b - width / Z_FAR},${sy(Z_FAR)}`;
}

const surface = [
  [sx(LEFT_EDGE, Z_NEAR), sy(Z_NEAR)],
  [sx(RIGHT_EDGE, Z_NEAR), sy(Z_NEAR)],
  [sx(RIGHT_EDGE, Z_FAR), sy(Z_FAR)],
  [sx(LEFT_EDGE, Z_FAR), sy(Z_FAR)],
]
  .map(([x, y]) => `${x},${y}`)
  .join(" ");

/** Static layer: ground, road surface, haze and edge lines. Colours follow the theme. */
function Backdrop({ viewBox }: { viewBox: string }) {
  return (
    <svg
      viewBox={viewBox}
      preserveAspectRatio="xMidYMax slice"
      className="absolute inset-0 h-full w-full"
      aria-hidden
    >
      <defs>
        <linearGradient id="ground" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" style={{ stopColor: "var(--road-sky)" }} />
          <stop offset="0.6" style={{ stopColor: "var(--road-sky)" }} />
          <stop offset="1" style={{ stopColor: "var(--road-ground)" }} />
        </linearGradient>
        <radialGradient id="haze" cx="0.52" cy="0.63" r="0.35">
          <stop offset="0" style={{ stopColor: "var(--road-haze)", stopOpacity: 0.35 }} />
          <stop offset="1" style={{ stopColor: "var(--road-haze)", stopOpacity: 0 }} />
        </radialGradient>
      </defs>
      <rect x={-400} width={W + 800} height={H} fill="url(#ground)" />
      <rect x={-400} width={W + 800} height={H} fill="url(#haze)" />
      <polygon points={surface} style={{ fill: "var(--road-surface)" }} />
      <polygon points={edgePolygon(LEFT_EDGE, 7)} style={{ fill: "var(--road-edge)" }} opacity="0.85" />
      <polygon points={edgePolygon(RIGHT_EDGE, 7)} style={{ fill: "var(--road-edge)" }} opacity="0.85" />
    </svg>
  );
}

/** Moving layer: lane dashes, headlight beam, car and readout. */
function Road({
  progress,
  drift: driftProgress,
  viewBox,
}: {
  progress: MotionValue<number>;
  drift: MotionValue<number>;
  viewBox: string;
}) {
  const reduce = useReducedMotion();
  const [p, setP] = useState(0);
  const [d, setD] = useState(0);
  const [idle, setIdle] = useState(0);

  useMotionValueEvent(progress, "change", setP);
  useMotionValueEvent(driftProgress, "change", setD);
  useAnimationFrame((_, delta) => {
    if (!reduce) setIdle((v) => v + (delta / 1000) * IDLE_SPEED);
  });

  const offset = p * SCROLL_TRAVEL + idle;
  const phase = offset % DASH_PERIOD;

  const dashes: { points: string; opacity: number }[] = [];
  for (let n = 0; n < 80; n++) {
    const zn = Z_NEAR + n * DASH_PERIOD - phase;
    const zf = zn + DASH_LENGTH;
    if (zf <= Z_NEAR) continue;
    const a = Math.max(zn, Z_NEAR);
    if (a > 80) break;
    const w1 = 9 / a;
    const w2 = 9 / zf;
    const c1 = sx(CENTER, a);
    const c2 = sx(CENTER, zf);
    dashes.push({
      points: `${c1 - w1},${sy(a)} ${c1 + w1},${sy(a)} ${c2 + w2},${sy(zf)} ${c2 - w2},${sy(zf)}`,
      opacity: Math.min(1, 7 / a),
    });
  }

  // The car eases ahead over the whole page; the lapse plays out in its own section.
  const zCar = 2.6 + Math.pow(p, 1.8) * 12;
  const drift = lerpKeys(d, [0, 0.25, 0.45, 0.65, 1], [0, 0, 210, 0, 0]);
  const yaw = lerpKeys(d, [0, 0.25, 0.33, 0.47, 0.65, 1], [0, 0, -2.2, 1.4, 0, 0]);
  const carX = sx(LANE + drift, zCar);
  const carY = sy(zCar);
  const carScale = 2.2 / zCar;

  const beamNear = zCar + 0.15;
  const beamFar = zCar + 5.5;
  const beam = [
    [sx(LANE + drift - 150, beamNear), sy(beamNear)],
    [sx(LANE + drift + 150, beamNear), sy(beamNear)],
    [sx(LANE + drift + 300, beamFar), sy(beamFar)],
    [sx(LANE + drift - 300, beamFar), sy(beamFar)],
  ]
    .map(([x, y]) => `${x},${y}`)
    .join(" ");

  const lapse = d > 0.27 && d < 0.55;
  const recovered = d >= 0.55;
  const chipOpacity = lerpKeys(d, [0.08, 0.18, 0.85, 0.95], [0, 1, 1, 0]);

  return (
    <svg
      viewBox={viewBox}
      preserveAspectRatio="xMidYMax slice"
      className="absolute inset-0 h-full w-full"
      aria-hidden
    >
      <defs>
        <linearGradient id="beam" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0" style={{ stopColor: "var(--road-beam)", stopOpacity: 0.11 }} />
          <stop offset="1" style={{ stopColor: "var(--road-beam)", stopOpacity: 0 }} />
        </linearGradient>
        <filter id="soft" x="-50%" y="-200%" width="200%" height="500%">
          <feGaussianBlur stdDeviation="7" />
        </filter>
      </defs>

      {dashes.map((dash, i) => (
        <polygon
          key={i}
          points={dash.points}
          style={{ fill: "var(--road-dash)" }}
          opacity={dash.opacity * 0.92}
        />
      ))}

      <polygon points={beam} fill="url(#beam)" />

      <g transform={`translate(${carX} ${carY}) scale(${carScale}) rotate(${yaw})`}>
        <Car />
      </g>

      {/* Drishti readout following the car */}
      <g transform={`translate(${carX} ${carY - 190 * carScale - 30})`} opacity={chipOpacity}>
        <rect
          x={-150}
          y={-26}
          width={300}
          height={40}
          rx={20}
          fill={lapse ? "#2a1119" : "#101a14"}
          stroke={lapse ? "#e0607a" : "#8ab99a"}
          strokeOpacity="0.55"
        />
        <circle cx={-126} cy={-6} r={4.5} fill={lapse ? "#e0607a" : "#8ab99a"} />
        <text
          x={-112}
          y={-1}
          fill={lapse ? "#f1a7b6" : "#cfe6d7"}
          fontSize="15"
          fontFamily="var(--font-jetbrains), monospace"
          letterSpacing="0.06em"
        >
          {lapse
            ? "LANE DRIFT · DROWSY 72/100"
            : recovered
              ? "CORRECTED · DRIVER ALERT"
              : "DRIVER ALERT · EAR 0.31"}
        </text>
      </g>
    </svg>
  );
}

/** Rear view of a car, anchored at bottom centre (0,0). */
function Car() {
  return (
    <g>
      <ellipse cx="0" cy="2" rx="170" ry="12" fill="#000" opacity="0.55" />
      <ellipse cx="-110" cy="10" rx="55" ry="7" fill="#e0607a" opacity="0.14" filter="url(#soft)" />
      <ellipse cx="110" cy="10" rx="55" ry="7" fill="#e0607a" opacity="0.14" filter="url(#soft)" />

      <rect x="-152" y="-36" width="46" height="36" rx="7" fill="#050608" />
      <rect x="106" y="-36" width="46" height="36" rx="7" fill="#050608" />

      <path d="M-120 -112 L-98 -168 Q-93 -178 -80 -178 L80 -178 Q93 -178 98 -168 L120 -112 Z" fill="#0e1016" />
      <path d="M-101 -118 L-85 -160 Q-81 -168 -72 -168 L72 -168 Q81 -168 85 -160 L101 -118 Z" fill="#181d2a" />
      <path d="M-60 -163 L-30 -163 L-52 -124 L-78 -124 Z" fill="#232a3b" opacity="0.6" />
      <path d="M-80 -177 H80" stroke="#3b4358" strokeWidth="2" opacity="0.7" />

      <rect x="-162" y="-116" width="324" height="88" rx="24" fill="#12141b" />
      <path d="M-150 -112 H150" stroke="#2a2f3e" strokeWidth="2" />

      <rect x="-150" y="-98" width="80" height="13" rx="6.5" fill="#e0607a" filter="url(#soft)" opacity="0.55" />
      <rect x="70" y="-98" width="80" height="13" rx="6.5" fill="#e0607a" filter="url(#soft)" opacity="0.55" />
      <rect x="-150" y="-98" width="80" height="13" rx="6.5" fill="#e0607a" />
      <rect x="70" y="-98" width="80" height="13" rx="6.5" fill="#e0607a" />
      <rect x="-70" y="-93" width="140" height="3" rx="1.5" fill="#e0607a" opacity="0.45" />

      <rect x="-36" y="-70" width="72" height="20" rx="3" fill="#262a36" />
      <path d="M-152 -40 H152" stroke="#1f2230" strokeWidth="4" />
    </g>
  );
}

/**
 * The road, fixed behind the whole page. `progress` is page scroll (0–1);
 * `drift` is the scroll progress of the section where the lapse plays out.
 */
export function RoadBackground({
  progress,
  drift,
}: {
  progress: MotionValue<number>;
  drift: MotionValue<number>;
}) {
  const viewBox = useViewBox();
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-canvas">
      <Backdrop viewBox={viewBox} />
      <Road progress={progress} drift={drift} viewBox={viewBox} />
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 75% 75% at 50% 58%, transparent 55%, var(--road-vignette) 100%)",
        }}
      />
    </div>
  );
}
