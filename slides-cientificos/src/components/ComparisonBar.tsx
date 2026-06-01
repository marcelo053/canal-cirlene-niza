import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { BRAND } from './brand';

export interface ComparisonBarProps {
  title: string;
  before: { label: string; value: number };
  after: { label: string; value: number };
  unit: string;
  source: string;
}

const Bar: React.FC<{
  label: string;
  value: number;
  maxValue: number;
  color: string;
  startFrame: number;
  unit: string;
}> = ({ label, value, maxValue, color, startFrame, unit }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    fps,
    frame: frame - startFrame,
    config: { damping: 15, stiffness: 80, mass: 0.8 },
  });

  const barWidth = `${(value / maxValue) * 100 * progress}%`;
  const labelOpacity = interpolate(frame, [startFrame, startFrame + 15], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <div style={{ width: '100%', marginBottom: 48 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: 16,
          opacity: labelOpacity,
        }}
      >
        <span style={{ fontSize: 38, fontWeight: 600, color: BRAND.dark }}>{label}</span>
        <span style={{ fontSize: 38, fontWeight: 800, color }}>
          {Math.round(value * progress)}
          {unit}
        </span>
      </div>
      <div
        style={{
          height: 32,
          backgroundColor: BRAND.light,
          borderRadius: 16,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: '100%',
            width: barWidth,
            backgroundColor: color,
            borderRadius: 16,
            transition: 'width 0.1s',
          }}
        />
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
  const maxValue = Math.max(before.value, after.value);

  const titleOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });
  const titleY = interpolate(frame, [0, 20], [40, 0], { extrapolateRight: 'clamp' });
  const sourceOpacity = interpolate(frame, [80, 100], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        backgroundColor: BRAND.bg,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: BRAND.font,
        padding: '100px 80px',
        boxSizing: 'border-box',
      }}
    >
      <div
        style={{
          fontSize: 56,
          fontWeight: 800,
          color: BRAND.dark,
          textAlign: 'center',
          lineHeight: 1.3,
          marginBottom: 100,
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
        }}
      >
        {title}
      </div>

      <div style={{ width: '100%' }}>
        <Bar
          label={before.label}
          value={before.value}
          maxValue={maxValue}
          color={BRAND.medium}
          startFrame={20}
          unit={unit}
        />
        <Bar
          label={after.label}
          value={after.value}
          maxValue={maxValue}
          color={BRAND.primary}
          startFrame={45}
          unit={unit}
        />
      </div>

      <div
        style={{
          fontSize: 28,
          color: BRAND.medium,
          opacity: sourceOpacity,
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          fontStyle: 'italic',
          marginTop: 80,
        }}
      >
        <div style={{ width: 50, height: 2, backgroundColor: BRAND.primary, flexShrink: 0 }} />
        {source}
        <div style={{ width: 50, height: 2, backgroundColor: BRAND.primary, flexShrink: 0 }} />
      </div>
    </div>
  );
};
