import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";
import { C } from "../tokens";
import { Chip } from "../components/Chip";
import { Divider } from "../components/Divider";
import { Source } from "../components/Source";
import { StudyQuoteProps } from "../types";

export const StudyQuote: React.FC<StudyQuoteProps> = ({
  quote,
  highlight,
  study,
  year,
  topic,
}) => {
  const frame = useCurrentFrame();

  const bgOpacity = interpolate(frame, [0, 9], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const quoteOpacity = interpolate(frame, [15, 33], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const quoteY = interpolate(frame, [15, 33], [30, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  const highlightOpacity = interpolate(frame, [33, 51], [0, 1], {
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

      <div
        style={{
          fontSize: 52,
          fontWeight: 500,
          color: C.medium,
          lineHeight: 1.5,
          opacity: quoteOpacity,
          transform: `translateY(${quoteY}px)`,
        }}
      >
        "{quote}"
      </div>

      <Divider startFrame={24} />

      <div
        style={{
          fontSize: 60,
          fontWeight: 800,
          color: C.primary,
          lineHeight: 1.3,
          opacity: highlightOpacity,
        }}
      >
        {highlight}
      </div>

      <Source text={`${study}, ${year}`} startFrame={51} />
    </div>
  );
};
