import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { BRAND } from './brand';

export interface StatCardProps {
  stat: string;
  description: string;
  source: string;
  topic?: string;
}

export const StatCard: React.FC<StatCardProps> = ({ stat, description, source, topic }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const containerOpacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: 'clamp' });

  const statScale = spring({
    fps,
    frame: frame - 10,
    config: { damping: 12, stiffness: 100, mass: 0.5 },
  });

  const descOpacity = interpolate(frame, [28, 45], [0, 1], { extrapolateRight: 'clamp' });
  const descY = interpolate(frame, [28, 45], [30, 0], { extrapolateRight: 'clamp' });

  const sourceOpacity = interpolate(frame, [50, 65], [0, 1], { extrapolateRight: 'clamp' });

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
        opacity: containerOpacity,
        padding: '100px 80px',
        boxSizing: 'border-box',
      }}
    >
      {topic && (
        <div
          style={{
            backgroundColor: BRAND.light,
            color: BRAND.primary,
            fontSize: 32,
            fontWeight: 700,
            padding: '14px 40px',
            borderRadius: 100,
            marginBottom: 80,
            letterSpacing: 3,
            textTransform: 'uppercase',
          }}
        >
          {topic}
        </div>
      )}

      <div
        style={{
          fontSize: 220,
          fontWeight: 900,
          color: BRAND.primary,
          lineHeight: 1,
          transform: `scale(${statScale})`,
          marginBottom: 60,
          letterSpacing: -6,
        }}
      >
        {stat}
      </div>

      <div
        style={{
          fontSize: 52,
          fontWeight: 500,
          color: BRAND.dark,
          textAlign: 'center',
          lineHeight: 1.4,
          maxWidth: 900,
          opacity: descOpacity,
          transform: `translateY(${descY}px)`,
          marginBottom: 80,
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
