import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";
import { C } from "../tokens";

export const Chip: React.FC<{ label: string }> = ({ label }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [6, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const y = interpolate(frame, [6, 15], [10, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  return (
    <div
      style={{
        opacity,
        transform: `translateY(${y}px)`,
        display: "inline-block",
        background: C.light,
        color: C.primary,
        fontSize: 30,
        fontWeight: 700,
        fontFamily: "Inter, sans-serif",
        padding: "12px 38px",
        borderRadius: 100,
        letterSpacing: 3,
        textTransform: "uppercase",
      }}
    >
      {label}
    </div>
  );
};
