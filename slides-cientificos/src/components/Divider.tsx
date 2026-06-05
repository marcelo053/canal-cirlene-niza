import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";
import { C } from "../tokens";

export const Divider: React.FC<{ startFrame?: number }> = ({ startFrame = 24 }) => {
  const frame = useCurrentFrame();
  const width = interpolate(frame, [startFrame, startFrame + 27], [0, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.quad),
  });

  return (
    <div
      style={{
        height: 3,
        width: `${width}%`,
        background: C.primary,
        borderRadius: 2,
      }}
    />
  );
};
