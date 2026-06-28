import React from "react";
import { SlideProps } from "./types";
import { StatCard } from "./layouts/StatCard";
import { CircleStat } from "./layouts/CircleStat";
import { ComparisonBar } from "./layouts/ComparisonBar";
import { StudyQuote } from "./layouts/StudyQuote";
import { BenefitsList } from "./layouts/BenefitsList";
import { TimelineProgress } from "./layouts/TimelineProgress";
import { ScientificDefinition } from "./layouts/ScientificDefinition";

export const Slide: React.FC<SlideProps> = (props) => {
  switch (props.layout) {
    case "StatCard":
      return <StatCard {...props} />;
    case "CircleStat":
      return <CircleStat {...props} />;
    case "ComparisonBar":
      return <ComparisonBar {...props} />;
    case "StudyQuote":
      return <StudyQuote {...props} />;
    case "BenefitsList":
      return <BenefitsList {...props} />;
    case "TimelineProgress":
      return <TimelineProgress {...props} />;
    case "ScientificDefinition":
      return <ScientificDefinition {...props} />;
  }
};
