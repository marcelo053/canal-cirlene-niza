import React from "react";
import { useCurrentFrame, interpolate, spring, useVideoConfig, Easing } from "remotion";
import { C, FPS } from "../tokens";
import { Chip } from "../components/Chip";
import { Divider } from "../components/Divider";
import { Source } from "../components/Source";
import { StatCardProps } from "../types";

export const StatCard: React.FC<StatCardProps> = ({ stat, description, source, topic }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const bgOpacity = interpolate(frame, [0, 9], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const statScale = spring({
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
  const descY = interpolate(frame, [27, 45], [20, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

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
        gap: 40,
        fontFamily: "Inter, sans-serif",
      }}
    >
      {topic && <Chip label={topic} />}

      <div
        style={{
          fontSize: 220,
          fontWeight: 900,
          color: C.primary,
          lineHeight: 1.0,
          letterSpacing: -6,
          fontVariantNumeric: "tabular-nums",
          transform: `scale(${statScale})`,
        }}
      >
        {stat}
      </div>

      <Divider startFrame={24} />

      <div
        style={{
          fontSize: 52,
          fontWeight: 500,
          color: C.dark,
          textAlign: "center",
          lineHeight: 1.4,
          opacity: descOpacity,
          transform: `translateY(${descY}px)`,
        }}
      >
        {description}
      </div>

      <Source text={source} startFrame={51} />
    </div>
  );
};
