import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { BRAND } from './brand';

export interface BenefitsListProps {
  title: string;
  items: Array<{ icon: string; text: string }>;
  source?: string;
  topic?: string;
}

const BenefitItem: React.FC<{
  icon: string;
  text: string;
  startFrame: number;
}> = ({ icon, text, startFrame }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const itemSpring = spring({
    fps,
    frame: frame - startFrame,
    config: { damping: 14, stiffness: 100, mass: 0.5 },
  });

  const opacity = interpolate(frame, [startFrame, startFrame + 10], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const x = interpolate(frame, [startFrame, startFrame + 20], [-60, 0], {
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 36,
        opacity,
        transform: `translateX(${x}px) scale(${0.85 + itemSpring * 0.15})`,
        marginBottom: 40,
      }}
    >
      <div
        style={{
          width: 90,
          height: 90,
          borderRadius: 24,
          backgroundColor: BRAND.light,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 44,
          flexShrink: 0,
        }}
      >
        {icon}
      </div>
      <div
        style={{
          fontSize: 44,
          fontWeight: 600,
          color: BRAND.dark,
          lineHeight: 1.3,
          flex: 1,
        }}
      >
        {text}
      </div>
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

  const titleOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });
  const titleY = interpolate(frame, [0, 20], [-30, 0], { extrapolateRight: 'clamp' });
  const sourceOpacity = interpolate(frame, [110, 130], [0, 1], { extrapolateRight: 'clamp' });

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
        padding: '100px 80px',
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
            alignSelf: 'flex-start',
            marginBottom: 48,
            opacity: titleOpacity,
          }}
        >
          {topic}
        </div>
      )}

      <div
        style={{
          fontSize: 60,
          fontWeight: 800,
          color: BRAND.dark,
          lineHeight: 1.2,
          marginBottom: 64,
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
        }}
      >
        {title}
      </div>

      <div>
        {items.map((item, i) => (
          <BenefitItem
            key={i}
            icon={item.icon}
            text={item.text}
            startFrame={25 + i * 18}
          />
        ))}
      </div>

      {source && (
        <div
          style={{
            fontSize: 26,
            color: BRAND.medium,
            opacity: sourceOpacity,
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            fontStyle: 'italic',
            marginTop: 40,
          }}
        >
          <div
            style={{ width: 40, height: 2, backgroundColor: BRAND.primary, flexShrink: 0 }}
          />
          {source}
        </div>
      )}
    </div>
  );
};
