import React from "react";
import { useCurrentFrame, interpolate, spring, useVideoConfig, Easing } from "remotion";
import { C } from "../tokens";
import { Chip } from "../components/Chip";
import { Divider } from "../components/Divider";
import { Source } from "../components/Source";
import { ScientificDefinitionProps } from "../types";

export const ScientificDefinition: React.FC<ScientificDefinitionProps> = ({
  term,
  pronunciation,
  definition,
  analogy,
  topic,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const bgOpacity = interpolate(frame, [0, 9], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const termScale = spring({
    frame: frame - 9,
    fps,
    config: { damping: 12, stiffness: 180, mass: 1 },
    from: 0,
    to: 1,
  });

  const defOpacity = interpolate(frame, [27, 45], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const defY = interpolate(frame, [27, 45], [20, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  const analogyOpacity = interpolate(frame, [51, 66], [0, 1], {
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
        padding: "100px 80px",
        boxSizing: "border-box",
        gap: 44,
        fontFamily: "Inter, sans-serif",
      }}
    >
      {topic && <Chip label={topic} />}

      <div style={{ transform: `scale(${termScale})`, transformOrigin: "left center" }}>
        <div
          style={{
            fontSize: 96,
            fontWeight: 900,
            color: C.primary,
            lineHeight: 1.0,
            letterSpacing: -2,
          }}
        >
          {term}
        </div>
        {pronunciation && (
          <div style={{ fontSize: 36, color: C.medium, fontStyle: "italic", marginTop: 8 }}>
            {pronunciation}
          </div>
        )}
      </div>

      <Divider startFrame={24} />

      <div
        style={{
          fontSize: 46,
          fontWeight: 500,
          color: C.dark,
          lineHeight: 1.4,
          opacity: defOpacity,
          transform: `translateY(${defY}px)`,
        }}
      >
        {definition}
      </div>

      <div
        style={{
          borderLeft: `6px solid ${C.primary}`,
          paddingLeft: 28,
          borderRadius: 4,
          opacity: analogyOpacity,
        }}
      >
        <div style={{ fontSize: 42, fontWeight: 500, color: C.medium, lineHeight: 1.4, fontStyle: "italic" }}>
          {analogy}
        </div>
      </div>
    </div>
  );
};
