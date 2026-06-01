import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { BRAND } from './brand';

export interface ScientificDefinitionProps {
  term: string;
  pronunciation?: string;
  definition: string;
  analogy: string;
  topic?: string;
}

export const ScientificDefinition: React.FC<ScientificDefinitionProps> = ({
  term,
  pronunciation,
  definition,
  analogy,
  topic,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const bgOpacity = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: 'clamp' });

  const termScale = spring({
    fps,
    frame: frame - 5,
    config: { damping: 12, stiffness: 90, mass: 0.6 },
  });

  const dividerWidth = interpolate(frame, [25, 50], [0, 100], { extrapolateRight: 'clamp' });

  const defOpacity = interpolate(frame, [45, 65], [0, 1], { extrapolateRight: 'clamp' });
  const defY = interpolate(frame, [45, 65], [24, 0], { extrapolateRight: 'clamp' });

  const analogyOpacity = interpolate(frame, [70, 90], [0, 1], { extrapolateRight: 'clamp' });
  const analogyY = interpolate(frame, [70, 90], [24, 0], { extrapolateRight: 'clamp' });

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        backgroundColor: BRAND.bg,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        fontFamily: BRAND.font,
        opacity: bgOpacity,
        padding: '100px 80px',
        boxSizing: 'border-box',
      }}
    >
      {topic && (
        <div
          style={{
            backgroundColor: BRAND.light,
            color: BRAND.primary,
            fontSize: 26,
            fontWeight: 700,
            padding: '10px 28px',
            borderRadius: 100,
            letterSpacing: 3,
            textTransform: 'uppercase',
            alignSelf: 'flex-start',
            marginBottom: 48,
          }}
        >
          {topic}
        </div>
      )}

      {/* Term */}
      <div
        style={{
          transform: `scale(${0.8 + termScale * 0.2})`,
          transformOrigin: 'left center',
          marginBottom: 16,
        }}
      >
        <div
          style={{
            fontSize: 96,
            fontWeight: 900,
            color: BRAND.primary,
            lineHeight: 1,
            letterSpacing: -2,
          }}
        >
          {term}
        </div>
        {pronunciation && (
          <div
            style={{
              fontSize: 34,
              color: BRAND.medium,
              fontStyle: 'italic',
              marginTop: 8,
              letterSpacing: 1,
            }}
          >
            {pronunciation}
          </div>
        )}
      </div>

      {/* Divider */}
      <div
        style={{
          height: 4,
          width: `${dividerWidth}%`,
          backgroundColor: BRAND.primary,
          borderRadius: 2,
          marginBottom: 48,
        }}
      />

      {/* Definition */}
      <div
        style={{
          opacity: defOpacity,
          transform: `translateY(${defY}px)`,
          marginBottom: 48,
        }}
      >
        <div
          style={{
            fontSize: 28,
            fontWeight: 700,
            color: BRAND.primary,
            letterSpacing: 2,
            textTransform: 'uppercase',
            marginBottom: 16,
          }}
        >
          O que é
        </div>
        <div
          style={{
            fontSize: 46,
            fontWeight: 500,
            color: BRAND.dark,
            lineHeight: 1.5,
          }}
        >
          {definition}
        </div>
      </div>

      {/* Analogy — simplified language */}
      <div
        style={{
          opacity: analogyOpacity,
          transform: `translateY(${analogyY}px)`,
          backgroundColor: BRAND.light,
          borderRadius: 24,
          padding: '36px 44px',
          borderLeft: `6px solid ${BRAND.primary}`,
        }}
      >
        <div
          style={{
            fontSize: 26,
            fontWeight: 700,
            color: BRAND.primary,
            letterSpacing: 2,
            textTransform: 'uppercase',
            marginBottom: 12,
          }}
        >
          Em palavras simples
        </div>
        <div
          style={{
            fontSize: 42,
            color: BRAND.dark,
            lineHeight: 1.5,
            fontStyle: 'italic',
          }}
        >
          {analogy}
        </div>
      </div>
    </div>
  );
};
