import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { BRAND } from './brand';

export interface TimelineMilestone {
  label: string;
  value: string;
  description: string;
}

export interface TimelineProgressProps {
  title: string;
  milestones: TimelineMilestone[];
  unit?: string;
  source?: string;
  topic?: string;
}

const Milestone: React.FC<{
  milestone: TimelineMilestone;
  index: number;
  total: number;
  startFrame: number;
  isLast: boolean;
}> = ({ milestone, startFrame, isLast }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const ms = spring({
    fps,
    frame: frame - startFrame,
    config: { damping: 12, stiffness: 90, mass: 0.6 },
  });

  const opacity = interpolate(frame, [startFrame, startFrame + 12], [0, 1], {
    extrapolateRight: 'clamp',
  });

  const lineProgress = interpolate(frame, [startFrame + 10, startFrame + 35], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
      <div
        style={{
          fontSize: 28,
          fontWeight: 700,
          color: BRAND.primary,
          letterSpacing: 1,
          textTransform: 'uppercase',
          opacity,
          marginBottom: 16,
          textAlign: 'center',
        }}
      >
        {milestone.label}
      </div>

      <div
        style={{
          width: 72,
          height: 72,
          borderRadius: '50%',
          backgroundColor: BRAND.primary,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transform: `scale(${ms})`,
          marginBottom: 16,
          flexShrink: 0,
        }}
      >
        <div
          style={{
            fontSize: 28,
            fontWeight: 900,
            color: BRAND.white,
            lineHeight: 1,
          }}
        >
          ✓
        </div>
      </div>

      {!isLast && (
        <div
          style={{
            position: 'absolute',
            top: 36 + 72 / 2,
            left: '50%',
            width: `${lineProgress * 100}%`,
            height: 4,
            backgroundColor: BRAND.primary,
            borderRadius: 2,
          }}
        />
      )}

      <div
        style={{
          fontSize: 60,
          fontWeight: 900,
          color: BRAND.dark,
          opacity,
          transform: `scale(${0.7 + ms * 0.3})`,
          marginBottom: 12,
          textAlign: 'center',
        }}
      >
        {milestone.value}
      </div>

      <div
        style={{
          fontSize: 30,
          color: BRAND.medium,
          opacity,
          textAlign: 'center',
          lineHeight: 1.3,
        }}
      >
        {milestone.description}
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

  const titleOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });
  const titleY = interpolate(frame, [0, 20], [-30, 0], { extrapolateRight: 'clamp' });
  const sourceOpacity = interpolate(frame, [100, 120], [0, 1], { extrapolateRight: 'clamp' });

  const lineFullProgress = interpolate(
    frame,
    [20, 20 + milestones.length * 30],
    [0, 1],
    { extrapolateRight: 'clamp' }
  );

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
          textAlign: 'center',
          lineHeight: 1.2,
          marginBottom: 80,
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
        }}
      >
        {title}
      </div>

      {/* Track line */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          marginBottom: 80,
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: 36 + 72 / 2,
            left: '5%',
            height: 4,
            width: `${lineFullProgress * 90}%`,
            backgroundColor: BRAND.light,
            borderRadius: 2,
          }}
        />
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-around',
            position: 'relative',
          }}
        >
          {milestones.map((m, i) => (
            <Milestone
              key={i}
              milestone={m}
              index={i}
              total={milestones.length}
              startFrame={20 + i * 28}
              isLast={i === milestones.length - 1}
            />
          ))}
        </div>
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
