#!/usr/bin/env node
/**
 * CLI: node render.mjs --props '{"layout":"StatCard",...}' --out output.mp4
 * Used by n8n gerador-slides-cirl workflow.
 *
 * Env vars:
 *   CHROME_EXECUTABLE_PATH  — path to Chromium binary (Docker: /usr/bin/chromium)
 *   REMOTION_CACHE_DIR      — writable dir for webpack + browser cache (default: /tmp/remotion-cache)
 */
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import path from "path";
import { fileURLToPath } from "url";
import { mkdirSync } from "fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const args = process.argv.slice(2);
const getArg = (flag) => {
  const i = args.indexOf(flag);
  return i !== -1 ? args[i + 1] : null;
};

const propsRaw = getArg("--props");
const outFile  = getArg("--out") || "out/slide.mp4";

if (!propsRaw) {
  console.error("Usage: node render.mjs --props '{...}' --out output.mp4");
  process.exit(1);
}

const props  = JSON.parse(propsRaw);
const layout = props.layout;

if (!layout) {
  console.error("props.layout is required");
  process.exit(1);
}

const DURATIONS = {
  StatCard: 90,       // 3s
  CircleStat: 100,    // 3.3s
  ComparisonBar: 100, // 3.3s
  StudyQuote: 90,     // 3s
  BenefitsList: 110,  // 3.7s
  TimelineProgress: 100,
  ScientificDefinition: 100,
};

const durationInFrames = DURATIONS[layout] || 150;

// Writable cache dir — critical when /slides is read-only (Docker)
const CACHE_DIR = process.env.REMOTION_CACHE_DIR || "/tmp/remotion-cache";
mkdirSync(CACHE_DIR, { recursive: true });

// System Chromium (Docker) or auto-download (local dev)
const browserExecutable = process.env.CHROME_EXECUTABLE_PATH || undefined;

console.log(`Rendering ${layout} → ${outFile}`);
if (browserExecutable) console.log(`Using browser: ${browserExecutable}`);

const bundleLocation = await bundle({
  entryPoint: path.join(__dirname, "src/index.ts"),
  webpackOverride: (config) => ({
    ...config,
    cache: false,
  }),
  outDir: path.join(CACHE_DIR, "bundle"),
});

const composition = await selectComposition({
  serveUrl: bundleLocation,
  id: layout,
  inputProps: props,
  browserExecutable,
});

await renderMedia({
  composition: { ...composition, durationInFrames },
  serveUrl: bundleLocation,
  codec: "h264",
  outputLocation: outFile,
  inputProps: props,
  fps: 30,
  browserExecutable,
  chromiumOptions: {
    disableWebSecurity: true,
  },
  onProgress: ({ progress }) => {
    process.stdout.write(`\r  ${Math.round(progress * 100)}%`);
  },
});

console.log(`\nDone: ${outFile}`);
