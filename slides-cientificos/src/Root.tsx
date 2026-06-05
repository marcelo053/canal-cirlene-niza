import React from "react";
import { Composition } from "remotion";
import { Slide } from "./Slide";
import { SlideProps } from "./types";
import { FPS, W, H } from "./tokens";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const SlideAny = Slide as React.FC<any>;

const DURATIONS: Record<string, number> = {
  StatCard: 120,
  CircleStat: 150,
  ComparisonBar: 150,
  StudyQuote: 120,
  BenefitsList: 160,
  TimelineProgress: 150,
  ScientificDefinition: 150,
};

const DEFAULT_PROPS: SlideProps = {
  layout: "StatCard",
  stat: "73%",
  description: "dos adultos têm deficiência de vitamina D",
  source: "Journal of Nutrition, 2024",
  topic: "NUTRIÇÃO",
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {(Object.keys(DURATIONS) as Array<keyof typeof DURATIONS>).map((layout) => (
        <Composition
          key={layout}
          id={layout}
          component={SlideAny}
          durationInFrames={DURATIONS[layout]}
          fps={FPS}
          width={W}
          height={H}
          defaultProps={{ ...DEFAULT_PROPS, layout } as SlideProps}
        />
      ))}
      <Composition
        id="SlideFromJSON"
        component={SlideAny}
        durationInFrames={150}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={DEFAULT_PROPS}
      />
    </>
  );
};
