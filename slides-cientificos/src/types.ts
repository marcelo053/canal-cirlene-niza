export type LayoutId =
  | "StatCard"
  | "CircleStat"
  | "ComparisonBar"
  | "StudyQuote"
  | "BenefitsList"
  | "TimelineProgress"
  | "ScientificDefinition";

export interface StatCardProps {
  stat: string;
  description: string;
  source: string;
  topic?: string;
}

export interface CircleStatProps {
  value: number;
  unit?: string;
  description: string;
  source: string;
  topic?: string;
}

export interface ComparisonBarProps {
  title: string;
  before: { label: string; value: number };
  after: { label: string; value: number };
  unit: string;
  source: string;
}

export interface StudyQuoteProps {
  quote: string;
  highlight: string;
  study: string;
  year: number;
  topic?: string;
}

export interface BenefitsListProps {
  title: string;
  items: Array<{ icon: string; text: string }>;
  source?: string;
  topic?: string;
}

export interface TimelineProgressProps {
  title: string;
  milestones: Array<{ label: string; value: string; description: string }>;
  source?: string;
  topic?: string;
}

export interface ScientificDefinitionProps {
  term: string;
  pronunciation?: string;
  definition: string;
  analogy: string;
  topic?: string;
}

export type SlideProps =
  | ({ layout: "StatCard" } & StatCardProps)
  | ({ layout: "CircleStat" } & CircleStatProps)
  | ({ layout: "ComparisonBar" } & ComparisonBarProps)
  | ({ layout: "StudyQuote" } & StudyQuoteProps)
  | ({ layout: "BenefitsList" } & BenefitsListProps)
  | ({ layout: "TimelineProgress" } & TimelineProgressProps)
  | ({ layout: "ScientificDefinition" } & ScientificDefinitionProps);
