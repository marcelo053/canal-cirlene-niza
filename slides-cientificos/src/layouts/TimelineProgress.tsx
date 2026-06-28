import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";
import { C } from "../tokens";
import { Chip } from "../components/Chip";
import { Source } from "../components/Source";
import { TimelineProgressProps } from "../types";

const Milestone: React.FC<{
  label: string;
  value: string;
  description: string;
  index: number;
  total: number;
}> = ({ label, value, description, index, total }) => {
  const frame = useCurrentFrame();
  const startFrame = 18 + index * 20;
  const opacity = interpolate(frame, [startFrame, startFrame + 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.quad),
  });
  const x = interpolate(frame, [startFrame, startFrame + 15], [-40, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.quad),
  });
  const isLast = index === total - 1;

  return (
    <div
      style={{
        display: "flex",
        gap: 28,
        opacity,
        transform: `translateX(${x}px)`,
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div
          style={{
            width: 20,
            height: 20,
            borderRadius: "50%",
            background: C.primary,
            flexShrink: 0,
            marginTop: 8,
          }}
        />
        {!isLast && (
          <div style={{ width: 3, flex: 1, background: C.light, minHeight: 40, marginTop: 8 }} />
        )}
      </div>
      <div style={{ paddingBottom: isLast ? 0 : 32 }}>
        <div
          style={{
            fontSize: 56,
            fontWeight: 900,
            color: C.primary,
            lineHeight: 1.0,
            letterSpacing: -2,
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {value}
        </div>
        <div style={{ fontSize: 30, fontWeight: 700, color: C.medium, letterSpacing: 2, textTransform: "uppercase", marginTop: 4 }}>
          {label}
        </div>
        <div style={{ fontSize: 40, fontWeight: 500, color: C.dark, marginTop: 8, lineHeight: 1.3 }}>
          {description}
        </div>
      </div>
    </div>
  );
};

export const TimelineProgress: React.FC<TimelineProgressProps> = ({
  title,
  milestones,
  source,
  topic,
}) => {
  const frame = useCurrentFrame();

  const bgOpacity = interpolate(frame, [0, 9], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const titleOpacity = interpolate(frame, [0, 21], [0, 1], {
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
          fontSize: 60,
          fontWeight: 800,
          color: C.dark,
          lineHeight: 1.2,
          opacity: titleOpacity,
        }}
      >
        {title}
      </div>

      <div style={{ display: "flex", flexDirection: "column" }}>
        {milestones.map((m, i) => (
          <Milestone
            key={i}
            label={m.label}
            value={m.value}
            description={m.description}
            index={i}
            total={milestones.length}
          />
        ))}
      </div>

      {source && (
        <Source
          text={source}
          startFrame={18 + milestones.length * 20 + 15}
        />
      )}
    </div>
  );
};
