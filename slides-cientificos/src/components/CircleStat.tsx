import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { BRAND } from './brand';

export interface CircleStatProps {
  value: number;
  unit?: string;
  description: string;
  source: string;
  topic?: string;
}

export const CircleStat: React.FC<CircleStatProps> = ({
  value,
  unit = '%',
  description,
  source,
  topic,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const radius = 300;
  const stroke = 32;
  const normalizedRadius = radius - stroke / 2;
  const circumference = 2 * Math.PI * normalizedRadius;

  const arcProgress = interpolate(frame, [15, 75], [0, value / 100], {
    extrapolateRight: 'clamp',
  });
  const strokeDashoffset = circumference * (1 - arcProgress);

  const displayValue = Math.round(
    interpolate(frame, [15, 75], [0, value], { extrapolateRight: 'clamp' })
  );

  const numScale = spring({
    fps,
    frame: frame - 15,
    config: { damping: 14, stiffness: 80, mass: 0.7 },
  });

  const descOpacity = interpolate(frame, [70, 90], [0, 1], { extrapolateRight: 'clamp' });
  const descY = interpolate(frame, [70, 90], [20, 0], { extrapolateRight: 'clamp' });

  const sourceOpacity = interpolate(frame, [95, 115], [0, 1], { extrapolateRight: 'clamp' });
  const bgOpacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: 'clamp' });

  const svgSize = radius * 2;

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
        opacity: bgOpacity,
        padding: '80px 60px',
        boxSizing: 'border-box',
      }}
    >
      {topic && (
        <div
          style={{
            backgroundColor: BRAND.light,
            color: BRAND.primary,
            fontSize: 28,
            fontWeight: 700,
            padding: '10px 32px',
            borderRadius: 100,
            letterSpacing: 3,
            textTransform: 'uppercase',
            marginBottom: 56,
          }}
        >
          {topic}
        </div>
      )}

      <div style={{ position: 'relative', width: svgSize, height: svgSize, marginBottom: 60 }}>
        <svg width={svgSize} height={svgSize} style={{ transform: 'rotate(-90deg)' }}>
          {/* Track */}
          <circle
            cx={radius}
            cy={radius}
            r={normalizedRadius}
            fill="none"
            stroke={BRAND.light}
            strokeWidth={stroke}
          />
          {/* Progress arc */}
          <circle
            cx={radius}
            cy={radius}
            r={normalizedRadius}
            fill="none"
            stroke={BRAND.primary}
            strokeWidth={stroke}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
          />
        </svg>

        {/* Center number */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            transform: `scale(${0.6 + numScale * 0.4})`,
          }}
        >
          <span
            style={{
              fontSize: 160,
              fontWeight: 900,
              color: BRAND.dark,
              lineHeight: 1,
              letterSpacing: -4,
            }}
          >
            {displayValue}
          </span>
          <span
            style={{
              fontSize: 64,
              fontWeight: 700,
              color: BRAND.primary,
              lineHeight: 1,
              marginTop: -8,
            }}
          >
            {unit}
          </span>
        </div>
      </div>

      <div
        style={{
          fontSize: 50,
          fontWeight: 500,
          color: BRAND.dark,
          textAlign: 'center',
          lineHeight: 1.4,
          maxWidth: 900,
          opacity: descOpacity,
          transform: `translateY(${descY}px)`,
          marginBottom: 60,
        }}
      >
        {description}
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
        }}
      >
        <div style={{ width: 50, height: 2, backgroundColor: BRAND.primary, flexShrink: 0 }} />
        {source}
        <div style={{ width: 50, height: 2, backgroundColor: BRAND.primary, flexShrink: 0 }} />
      </div>
    </div>
  );
};
