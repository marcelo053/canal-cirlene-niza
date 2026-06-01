import './index.css';
import React from 'react';
import { Composition } from 'remotion';
import { StatCard } from './components/StatCard';
import { ComparisonBar } from './components/ComparisonBar';
import { StudyQuote } from './components/StudyQuote';
import { BenefitsList } from './components/BenefitsList';
import { TimelineProgress } from './components/TimelineProgress';
import { CircleStat } from './components/CircleStat';
import { ScientificDefinition } from './components/ScientificDefinition';
import type { StatCardProps } from './components/StatCard';
import type { ComparisonBarProps } from './components/ComparisonBar';
import type { StudyQuoteProps } from './components/StudyQuote';
import type { BenefitsListProps } from './components/BenefitsList';
import type { TimelineProgressProps } from './components/TimelineProgress';
import type { CircleStatProps } from './components/CircleStat';
import type { ScientificDefinitionProps } from './components/ScientificDefinition';

const W = 1080;
const H = 1920;
const FPS = 30;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const AnyComp = (c: React.FC<any>) => c as React.FC<Record<string, unknown>>;

const defaultStatCard: StatCardProps = {
  stat: '73%',
  description: 'das pessoas que reduziram glúten relataram melhora digestiva em 30 dias',
  source: 'Journal of Nutrition, 2023',
  topic: 'Glúten',
};

const defaultComparison: ComparisonBarProps = {
  title: 'Inflamação intestinal\nantes e depois da dieta',
  before: { label: 'Antes', value: 82 },
  after: { label: 'Depois (90 dias)', value: 31 },
  unit: '%',
  source: 'Gut Microbiome Research, 2022',
};

const defaultStudyQuote: StudyQuoteProps = {
  quote:
    'A redução do glúten melhorou significativamente marcadores inflamatórios em 68% dos participantes',
  highlight: '68% dos participantes',
  study: 'New England Journal of Medicine',
  year: 2023,
  topic: 'Glúten',
};

const defaultBenefitsList: BenefitsListProps = {
  title: '5 sinais de intolerância ao glúten',
  items: [
    { icon: '🫃', text: 'Inchaço e gases após refeições' },
    { icon: '😴', text: 'Cansaço persistente sem causa aparente' },
    { icon: '🧠', text: 'Névoa mental e dificuldade de concentração' },
    { icon: '🦴', text: 'Dores nas articulações sem lesão' },
    { icon: '😖', text: 'Dor de cabeça frequente pós-refeição' },
  ],
  source: 'American Journal of Gastroenterology, 2022',
  topic: 'Glúten',
};

const defaultTimeline: TimelineProgressProps = {
  title: 'Sua melhora semana a semana',
  milestones: [
    { label: 'Semana 1', value: '-30%', description: 'Inchaço reduz' },
    { label: 'Semana 4', value: '-58%', description: 'Inflamação cai' },
    { label: 'Semana 8', value: '-80%', description: 'Energia normaliza' },
  ],
  source: 'Clinical Nutrition Journal, 2023',
  topic: 'Glúten',
};

const defaultCircleStat: CircleStatProps = {
  value: 68,
  unit: '%',
  description: 'dos participantes eliminaram sintomas em apenas 8 semanas sem glúten',
  source: 'Gut Health Research Institute, 2023',
  topic: 'Glúten',
};

const defaultScientificDef: ScientificDefinitionProps = {
  term: 'Permeabilidade Intestinal',
  pronunciation: '/per·me·a·bi·li·da·de/',
  definition:
    'Condição em que a parede do intestino se torna porosa, permitindo que substâncias indesejadas entrem na corrente sanguínea.',
  analogy:
    'Imagine uma peneira com furos grandes demais — coisas que não deveriam passar, passam.',
  topic: 'Intestino',
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="StatCard"
        component={AnyComp(StatCard)}
        durationInFrames={120}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={defaultStatCard as unknown as Record<string, unknown>}
      />
      <Composition
        id="ComparisonBar"
        component={AnyComp(ComparisonBar)}
        durationInFrames={150}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={defaultComparison as unknown as Record<string, unknown>}
      />
      <Composition
        id="StudyQuote"
        component={AnyComp(StudyQuote)}
        durationInFrames={120}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={defaultStudyQuote as unknown as Record<string, unknown>}
      />
      <Composition
        id="BenefitsList"
        component={AnyComp(BenefitsList)}
        durationInFrames={160}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={defaultBenefitsList as unknown as Record<string, unknown>}
      />
      <Composition
        id="TimelineProgress"
        component={AnyComp(TimelineProgress)}
        durationInFrames={150}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={defaultTimeline as unknown as Record<string, unknown>}
      />
      <Composition
        id="CircleStat"
        component={AnyComp(CircleStat)}
        durationInFrames={150}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={defaultCircleStat as unknown as Record<string, unknown>}
      />
      <Composition
        id="ScientificDefinition"
        component={AnyComp(ScientificDefinition)}
        durationInFrames={150}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={defaultScientificDef as unknown as Record<string, unknown>}
      />
    </>
  );
};
