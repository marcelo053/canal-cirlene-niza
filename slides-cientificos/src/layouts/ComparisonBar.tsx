import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";
import { C } from "../tokens";
import { Source } from "../components/Source";
import { ComparisonBarProps } from "../types";

const Bar: React.FC<{
  label: string;
  value: number;
  maxValue: number;
  color: string;
  startFrame: number;
}> = ({ label, value, maxValue, color, startFrame }) => {
  const frame = useCurrentFrame();
  const width = interpolate(frame, [startFrame, startFrame + 45], [0, (value / maxValue) * 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.quad),
  });
  const opacity = interpolate(frame, [startFrame - 6, startFrame + 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div style={{ opacity, width: "100%" }}>
      <div
        style={{
          fontSize: 36,
          fontWeight: 700,
          color: C.medium,
          marginBottom: 12,
          fontFamily: "Inter, sans-serif",
          letterSpacing: 2,
          textTransform: "uppercase",
        }}
      >
        {label}
      </div>
      <div
        style={{
          width: "100%",
          height: 48,
          background: C.light,
          borderRadius: 16,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${width}%`,
            height: "100%",
            background: color,
            borderRadius: 16,
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-end",
            paddingRight: 16,
            boxSizing: "border-box",
          }}
        >
          {width > 15 && (
            <span
              style={{
                color: C.white,
                fontWeight: 700,
                fontSize: 28,
                fontFamily: "Inter, sans-serif",
              }}
            >
              {value}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export const ComparisonBar: React.FC<ComparisonBarProps> = ({
  title,
  before,
  after,
  unit,
  source,
}) => {
  const frame = useCurrentFrame();
  const maxValue = Math.max(before.value, after.value) * 1.1;

  const bgOpacity = interpolate(frame, [0, 9], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const titleOpacity = interpolate(frame, [0, 21], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const titleY = interpolate(frame, [0, 21], [20, 0], {
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
        gap: 50,
        fontFamily: "Inter, sans-serif",
      }}
    >
      <div
        style={{
          fontSize: 60,
          fontWeight: 800,
          color: C.dark,
          lineHeight: 1.2,
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
        }}
      >
        {title}
      </div>

      <div
        style={{
          fontSize: 30,
          color: C.medium,
          fontWeight: 500,
          letterSpacing: 2,
          textTransform: "uppercase",
        }}
      >
        {unit}
      </div>

      <Bar label={before.label} value={before.value} maxValue={maxValue} color={C.medium} startFrame={18} />
      <Bar label={after.label} value={after.value} maxValue={maxValue} color={C.primary} startFrame={36} />

      <Source text={source} startFrame={90} />
    </div>
  );
};
