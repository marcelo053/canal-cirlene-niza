import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { BRAND } from './brand';

export interface StudyQuoteProps {
  quote: string;
  highlight: string;
  study: string;
  year: number;
  topic?: string;
}

export const StudyQuote: React.FC<StudyQuoteProps> = ({
  quote,
  highlight,
  study,
  year,
  topic,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const bgOpacity = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: 'clamp' });

  const quoteScale = spring({
    fps,
    frame: frame - 8,
    config: { damping: 14, stiffness: 90, mass: 0.6 },
  });

  const highlightOpacity = interpolate(frame, [35, 55], [0, 1], { extrapolateRight: 'clamp' });
  const highlightScale = spring({
    fps,
    frame: frame - 35,
    config: { damping: 10, stiffness: 120, mass: 0.4 },
  });

  const metaOpacity = interpolate(frame, [60, 80], [0, 1], { extrapolateRight: 'clamp' });
  const metaY = interpolate(frame, [60, 80], [20, 0], { extrapolateRight: 'clamp' });

  const renderQuote = () => {
    if (!highlight || !quote.includes(highlight)) {
      return (
        <span style={{ color: BRAND.dark }}>{quote}</span>
      );
    }
    const parts = quote.split(highlight);
    return (
      <>
        <span style={{ color: BRAND.dark }}>{parts[0]}</span>
        <span
          style={{
            color: BRAND.primary,
            fontWeight: 800,
            opacity: highlightOpacity,
            display: 'inline-block',
            transform: `scale(${highlightScale})`,
            transformOrigin: 'center',
          }}
        >
          {highlight}
        </span>
        <span style={{ color: BRAND.dark }}>{parts[1]}</span>
      </>
    );
  };

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
        padding: '100px 80px',
        boxSizing: 'border-box',
      }}
    >
      {topic && (
        <div
          style={{
            backgroundColor: BRAND.light,
            color: BRAND.primary,
            fontSize: 30,
            fontWeight: 700,
            padding: '12px 36px',
            borderRadius: 100,
            marginBottom: 60,
            letterSpacing: 3,
            textTransform: 'uppercase',
          }}
        >
          {topic}
        </div>
      )}

      <div
        style={{
          fontSize: 44,
          color: BRAND.primary,
          fontWeight: 900,
          marginBottom: 32,
          transform: `scale(${quoteScale})`,
          lineHeight: 1,
        }}
      >
        "
      </div>

      <div
        style={{
          fontSize: 52,
          lineHeight: 1.5,
          textAlign: 'center',
          maxWidth: 920,
          transform: `scale(${quoteScale})`,
          marginBottom: 32,
        }}
      >
        {renderQuote()}
      </div>

      <div
        style={{
          fontSize: 44,
          color: BRAND.primary,
          fontWeight: 900,
          marginBottom: 60,
          transform: `scale(${quoteScale})`,
          lineHeight: 1,
        }}
      >
        "
      </div>

      <div
        style={{
          opacity: metaOpacity,
          transform: `translateY(${metaY}px)`,
          textAlign: 'center',
        }}
      >
        <div
          style={{
            width: 60,
            height: 3,
            backgroundColor: BRAND.primary,
            margin: '0 auto 24px',
            borderRadius: 2,
          }}
        />
        <div style={{ fontSize: 32, fontWeight: 700, color: BRAND.dark }}>{study}</div>
        <div style={{ fontSize: 28, color: BRAND.medium, marginTop: 8 }}>{year}</div>
      </div>
    </div>
  );
};
