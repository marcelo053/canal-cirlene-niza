#!/usr/bin/env node
/**
 * CLI: node render.mjs --props '{"layout":"StatCard",...}' --out output.mp4
 * Used by n8n gerador-slides-cirl workflow.
 */
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { createRequire } from "module";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const args = process.argv.slice(2);
const getArg = (flag) => {
  const i = args.indexOf(flag);
  return i !== -1 ? args[i + 1] : null;
};

const propsRaw = getArg("--props");
const outFile = getArg("--out") || "out/slide.mp4";

if (!propsRaw) {
  console.error("Usage: node render.mjs --props '{...}' --out output.mp4");
  process.exit(1);
}

const props = JSON.parse(propsRaw);
const layout = props.layout;

if (!layout) {
  console.error("props.layout is required");
  process.exit(1);
}

const DURATIONS = {
  StatCard: 120,
  CircleStat: 150,
  ComparisonBar: 150,
  StudyQuote: 120,
  BenefitsList: 160,
  TimelineProgress: 150,
  ScientificDefinition: 150,
};

const durationInFrames = DURATIONS[layout] || 150;

console.log(`Rendering ${layout} → ${outFile}`);

const bundleLocation = await bundle({
  entryPoint: path.join(__dirname, "src/index.ts"),
  webpackOverride: (config) => config,
});

const composition = await selectComposition({
  serveUrl: bundleLocation,
  id: layout,
  inputProps: props,
});

await renderMedia({
  composition: { ...composition, durationInFrames },
  serveUrl: bundleLocation,
  codec: "h264",
  outputLocation: outFile,
  inputProps: props,
  fps: 30,
  onProgress: ({ progress }) => {
    process.stdout.write(`\r  ${Math.round(progress * 100)}%`);
  },
});

console.log(`\nDone: ${outFile}`);
