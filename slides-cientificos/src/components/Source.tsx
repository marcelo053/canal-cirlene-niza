import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";
import { C } from "../tokens";

export const Source: React.FC<{ text: string; startFrame?: number }> = ({
  text,
  startFrame = 51,
}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [startFrame, startFrame + 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  return (
    <div
      style={{
        opacity,
        display: "flex",
        alignItems: "center",
        gap: 16,
        fontSize: 26,
        color: C.medium,
        fontStyle: "italic",
        fontFamily: "Inter, sans-serif",
        fontWeight: 400,
      }}
    >
      <div style={{ width: 45, height: 2, background: C.primary, borderRadius: 2 }} />
      {text}
      <div style={{ width: 45, height: 2, background: C.primary, borderRadius: 2 }} />
    </div>
  );
};
