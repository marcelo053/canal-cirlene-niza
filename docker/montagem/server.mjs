/**
 * Montagem HTTP service — concatena clips via ffmpeg + faz upload para MinIO.
 *
 * POST /concat
 * {
 *   "production_id": "prod-123",
 *   "clips": [
 *     "http://minio:9000/cirlene-video/prod-123/intro.mp4",
 *     "http://minio:9000/cirlene-slides/slides/slide-0.mp4",
 *     "http://minio:9000/cirlene-slides/slides/slide-1.mp4",
 *     "http://minio:9000/cirlene-video/prod-123/outro.mp4"
 *   ],
 *   "output_bucket": "cirlene-video",
 *   "output_key": "prod-123/final.mp4"
 * }
 *
 * → { ok: true, path: "minio://cirlene-video/prod-123/final.mp4", url: "<presigned>" }
 */
import express from "express";
import { exec } from "child_process";
import { promisify } from "util";
import { createWriteStream, unlinkSync, writeFileSync } from "fs";
import { Client as MinioClient } from "minio";
import { tmpdir } from "os";
import { join } from "path";
import { randomUUID } from "crypto";
import { pipeline } from "stream/promises";
import https from "https";
import http from "http";

const execAsync = promisify(exec);
const app = express();
app.use(express.json());

const MINIO_ENDPOINT = process.env.MINIO_ENDPOINT || "minio";
const MINIO_PORT    = parseInt(process.env.MINIO_PORT    || "9000");
const MINIO_ACCESS  = process.env.MINIO_ACCESS_KEY || "minioadmin";
const MINIO_SECRET  = process.env.MINIO_SECRET_KEY || "minioadmin";
const PORT          = parseInt(process.env.PORT || "3000");

const minio = new MinioClient({
  endPoint: MINIO_ENDPOINT,
  port: MINIO_PORT,
  useSSL: false,
  accessKey: MINIO_ACCESS,
  secretKey: MINIO_SECRET,
});

async function download(url, dest) {
  const client = url.startsWith("https") ? https : http;
  await new Promise((resolve, reject) => {
    client.get(url, (res) => {
      if (res.statusCode !== 200) return reject(new Error(`HTTP ${res.statusCode} for ${url}`));
      const ws = createWriteStream(dest);
      res.pipe(ws);
      ws.on("finish", resolve);
      ws.on("error", reject);
    }).on("error", reject);
  });
}

app.get("/health", (_req, res) => res.json({ ok: true }));

app.post("/concat", async (req, res) => {
  const { production_id, segments, clips, output_bucket, output_key } = req.body;

  if (!output_bucket || !output_key) {
    return res.status(400).json({ error: "clips[], output_bucket, output_key required" });
  }

  // Support both legacy clips[] and new segments[] format
  const hasSegments = Array.isArray(segments) && segments.length > 0;
  const hasAudio = hasSegments && segments.some(s => s.audio);

  if (!hasSegments && !clips?.length) {
    return res.status(400).json({ error: "clips[] or segments[] required" });
  }

  const id = production_id || randomUUID();
  const workDir = join(tmpdir(), `montagem-${id}`);
  const { mkdirSync } = await import("fs");
  mkdirSync(workDir, { recursive: true });

  const tempFiles = [];

  try {
    if (hasAudio) {
      // ── New path: segments with per-clip audio overlay ──────────────
      console.log(`[${id}] Segments mode: ${segments.length} segments with audio overlay`);

      // 1. Download each video + audio, apply audio overlay per segment
      const segFiles = [];
      for (let i = 0; i < segments.length; i++) {
        const seg = segments[i];
        const videoPath = join(workDir, `seg-${i}-video.mp4`);
        console.log(`  [${i}] Downloading video: ${seg.video}`);
        await download(seg.video, videoPath);
        tempFiles.push(videoPath);

        if (seg.audio) {
          const audioPath = join(workDir, `seg-${i}-audio.mp3`);
          console.log(`  [${i}] Downloading audio: ${seg.audio}`);
          await download(seg.audio, audioPath);
          tempFiles.push(audioPath);

          // ffmpeg: overlay audio, optionally mute original video audio
          const mixedPath = join(workDir, `seg-${i}-mixed.mp4`);
          tempFiles.push(mixedPath);

          // Both cases: replace/add TTS audio, discard original video audio
          // -filter_complex pads TTS to video length; -map picks video + padded audio
          const ffCmd = [
            "ffmpeg -y",
            `-i "${videoPath}"`,
            `-i "${audioPath}"`,
            `-filter_complex "[1:a]apad[aout]"`,
            `-map 0:v -map "[aout]"`,
            `-c:v copy`,
            `-c:a aac -b:a 192k`,
            `-shortest`,
            `-movflags +faststart`,
            `"${mixedPath}"`,
          ].join(" ");
          await execAsync(ffCmd, { timeout: 120_000 });
          segFiles.push(mixedPath);
        } else {
          // No audio override — use video as-is (re-encode to ensure consistent streams)
          const normPath = join(workDir, `seg-${i}-norm.mp4`);
          tempFiles.push(normPath);
          const ffCmd = [
            "ffmpeg -y",
            `-i "${videoPath}"`,
            `-an -c:v copy`,
            `"${normPath}"`,
          ].join(" ");
          await execAsync(ffCmd, { timeout: 60_000 });
          segFiles.push(normPath);
        }
      }

      // 2. Concat all processed segments
      const listFile = join(workDir, "list.txt");
      writeFileSync(listFile, segFiles.map(p => `file '${p}'`).join("\n"));
      tempFiles.push(listFile);

      const outFile = join(workDir, "final.mp4");
      tempFiles.push(outFile);
      const concatCmd = [
        "ffmpeg -y",
        `-f concat -safe 0 -i "${listFile}"`,
        `-vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black"`,
        `-c:v libx264 -preset fast -crf 22`,
        `-c:a aac -b:a 192k`,
        `-movflags +faststart`,
        `"${outFile}"`,
      ].join(" ");

      console.log(`  Concatenating ${segFiles.length} processed segments...`);
      await execAsync(concatCmd, { timeout: 300_000 });

      // 3. Upload
      const bucket = output_bucket;
      const exists = await minio.bucketExists(bucket);
      if (!exists) await minio.makeBucket(bucket);
      await minio.fPutObject(bucket, output_key, outFile, { "content-type": "video/mp4" });
      const presigned = await minio.presignedGetObject(bucket, output_key, 7 * 24 * 3600);
      res.json({ ok: true, path: `minio://${bucket}/${output_key}`, url: presigned });

    } else {
      // ── Legacy path: simple clips[] concat ─────────────────────────
      const clipList = hasSegments ? segments.map(s => s.video) : clips;
      console.log(`[${id}] Simple concat: ${clipList.length} clips`);

      const localClips = [];
      for (let i = 0; i < clipList.length; i++) {
        const dest = join(workDir, `clip-${i}.mp4`);
        console.log(`  Downloading clip ${i}: ${clipList[i]}`);
        await download(clipList[i], dest);
        localClips.push(dest);
        tempFiles.push(dest);
      }

      const listFile = join(workDir, "list.txt");
      writeFileSync(listFile, localClips.map(p => `file '${p}'`).join("\n"));
      tempFiles.push(listFile);

      const outFile = join(workDir, "final.mp4");
      tempFiles.push(outFile);
      const ffCmd = [
        "ffmpeg -y",
        `-f concat -safe 0 -i "${listFile}"`,
        `-vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black"`,
        `-c:v libx264 -preset fast -crf 22`,
        `-c:a aac -b:a 192k`,
        `-movflags +faststart`,
        `"${outFile}"`,
      ].join(" ");

      console.log(`  Running ffmpeg concat...`);
      await execAsync(ffCmd, { timeout: 300_000 });

      const bucket = output_bucket;
      const exists = await minio.bucketExists(bucket);
      if (!exists) await minio.makeBucket(bucket);
      await minio.fPutObject(bucket, output_key, outFile, { "content-type": "video/mp4" });
      const presigned = await minio.presignedGetObject(bucket, output_key, 7 * 24 * 3600);
      res.json({ ok: true, path: `minio://${bucket}/${output_key}`, url: presigned });
    }

  } catch (err) {
    console.error(err);
    res.status(500).json({ error: String(err) });
  } finally {
    for (const f of tempFiles) {
      try { unlinkSync(f); } catch (_) {}
    }
  }
});

/**
 * POST /upload-from-url
 * { url: "https://...", bucket: "cirlene-video", key: "prod-001/intro.mp4" }
 * → { ok: true, path: "minio://bucket/key", url: "<presigned 7d>" }
 */
app.post("/upload-from-url", async (req, res) => {
  const { url, bucket, key } = req.body;
  if (!url || !bucket || !key) {
    return res.status(400).json({ error: "url, bucket, key required" });
  }

  const id = randomUUID();
  const tmpFile = join(tmpdir(), `upload-${id}.mp4`);

  try {
    console.log(`  Downloading ${url} → ${tmpFile}`);
    await download(url, tmpFile);

    const exists = await minio.bucketExists(bucket);
    if (!exists) await minio.makeBucket(bucket);

    await minio.fPutObject(bucket, key, tmpFile, { "content-type": "video/mp4" });

    const presigned = await minio.presignedGetObject(bucket, key, 7 * 24 * 3600);

    res.json({ ok: true, path: `minio://${bucket}/${key}`, url: presigned });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: String(err) });
  } finally {
    try { unlinkSync(tmpFile); } catch (_) {}
  }
});

app.listen(PORT, () => console.log(`Montagem service :${PORT}`));
