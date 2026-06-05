import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";
import { C } from "../tokens";
import { Chip } from "../components/Chip";
import { Divider } from "../components/Divider";
import { Source } from "../components/Source";
import { BenefitsListProps } from "../types";

const Item: React.FC<{ icon: string; text: string; index: number }> = ({
  icon,
  text,
  index,
}) => {
  const frame = useCurrentFrame();
  const startFrame = 24 + index * 18;
  const opacity = interpolate(frame, [startFrame, startFrame + 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.quad),
  });
  const x = interpolate(frame, [startFrame, startFrame + 15], [-60, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.quad),
  });

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 36,
        opacity,
        transform: `translateX(${x}px)`,
      }}
    >
      <div
        style={{
          width: 80,
          height: 80,
          borderRadius: 24,
          background: C.light,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 40,
          flexShrink: 0,
        }}
      >
        {icon}
      </div>
      <span
        style={{
          fontSize: 44,
          fontWeight: 500,
          color: C.dark,
          lineHeight: 1.4,
          fontFamily: "Inter, sans-serif",
        }}
      >
        {text}
      </span>
    </div>
  );
};

export const BenefitsList: React.FC<BenefitsListProps> = ({
  title,
  items,
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
        gap: 40,
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
          transform: `translateY(${titleY}px)`,
        }}
      >
        {title}
      </div>

      <Divider startFrame={24} />

      <div style={{ display: "flex", flexDirection: "column", gap: 40 }}>
        {items.map((item, i) => (
          <Item key={i} icon={item.icon} text={item.text} index={i} />
        ))}
      </div>

      {source && <Source text={source} startFrame={24 + items.length * 18 + 15} />}
    </div>
  );
};
