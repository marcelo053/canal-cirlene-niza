import React from "react";
import { useCurrentFrame, interpolate, spring, useVideoConfig, Easing } from "remotion";
import { C } from "../tokens";
import { Chip } from "../components/Chip";
import { Source } from "../components/Source";
import { CircleStatProps } from "../types";

const RADIUS = 280;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export const CircleStat: React.FC<CircleStatProps> = ({
  value,
  unit = "%",
  description,
  source,
  topic,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const bgOpacity = interpolate(frame, [0, 9], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const arcProgress = interpolate(frame, [15, 75], [0, value / 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.quad),
  });

  const strokeDashoffset = CIRCUMFERENCE * (1 - arcProgress);

  const numScale = spring({
    frame: frame - 9,
    fps,
    config: { damping: 12, stiffness: 180, mass: 1 },
    from: 0,
    to: 1,
  });

  const descOpacity = interpolate(frame, [27, 45], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  const currentValue = Math.round(value * arcProgress);

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        background: C.bg,
        opacity: bgOpacity,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        padding: "100px 80px",
        boxSizing: "border-box",
        gap: 50,
        fontFamily: "Inter, sans-serif",
      }}
    >
      {topic && <Chip label={topic} />}

      <div style={{ position: "relative", width: 700, height: 700 }}>
        <svg width={700} height={700} style={{ position: "absolute", top: 0, left: 0 }}>
          <circle
            cx={350}
            cy={350}
            r={RADIUS}
            fill="none"
            stroke={C.light}
            strokeWidth={24}
          />
          <circle
            cx={350}
            cy={350}
            r={RADIUS}
            fill="none"
            stroke={C.primary}
            strokeWidth={24}
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={strokeDashoffset}
            transform="rotate(-90 350 350)"
          />
        </svg>
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: 700,
            height: 700,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
            transform: `scale(${numScale})`,
          }}
        >
          <span
            style={{
              fontSize: 180,
              fontWeight: 900,
              color: C.dark,
              lineHeight: 1.0,
              letterSpacing: -6,
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {currentValue}
          </span>
          <span style={{ fontSize: 60, fontWeight: 700, color: C.primary }}>
            {unit}
          </span>
        </div>
      </div>

      <div
        style={{
          fontSize: 48,
          fontWeight: 500,
          color: C.dark,
          textAlign: "center",
          lineHeight: 1.4,
          opacity: descOpacity,
        }}
      >
        {description}
      </div>

      <Source text={source} startFrame={51} />
    </div>
  );
};
