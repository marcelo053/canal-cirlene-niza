/**
 * Remotion render HTTP service.
 * POST /render  { props: {...}, output: "filename.mp4" }
 * → renders slide, uploads to MinIO, returns { url, path }
 */
import express from "express";
import { exec } from "child_process";
import { promisify } from "util";
import { createReadStream, unlinkSync, symlinkSync, existsSync } from "fs";
import { Client as MinioClient } from "minio";
import path from "path";
import { tmpdir } from "os";
import { randomUUID } from "crypto";

const execAsync = promisify(exec);
const app = express();
app.use(express.json());

const SLIDES_DIR = process.env.SLIDES_DIR || "/slides";
const MINIO_ENDPOINT = process.env.MINIO_ENDPOINT || "minio";
const MINIO_PORT = parseInt(process.env.MINIO_PORT || "9000");
const MINIO_ACCESS_KEY = process.env.MINIO_ACCESS_KEY || "minioadmin";
const MINIO_SECRET_KEY = process.env.MINIO_SECRET_KEY || "minioadmin";
const MINIO_BUCKET = process.env.MINIO_BUCKET || "cirlene-slides";
const PORT = parseInt(process.env.PORT || "3000");

const minio = new MinioClient({
  endPoint: MINIO_ENDPOINT,
  port: MINIO_PORT,
  useSSL: false,
  accessKey: MINIO_ACCESS_KEY,
  secretKey: MINIO_SECRET_KEY,
});

async function ensureBucket() {
  const exists = await minio.bucketExists(MINIO_BUCKET);
  if (!exists) await minio.makeBucket(MINIO_BUCKET);
}

app.get("/health", (_req, res) => res.json({ ok: true }));

app.post("/render", async (req, res) => {
  const { props, output } = req.body;
  if (!props?.layout) {
    return res.status(400).json({ error: "props.layout required" });
  }

  const outName = output || `${props.layout}-${randomUUID()}.mp4`;
  const tmpOut = path.join(tmpdir(), outName);

  try {
    const propsJson = JSON.stringify(props).replace(/'/g, "'\\''");
    const cmd = `node "${SLIDES_DIR}/render.mjs" --props '${propsJson}' --out "${tmpOut}"`;

    const { stdout, stderr } = await execAsync(cmd, {
      cwd: SLIDES_DIR,
      env: {
        ...process.env,
        NODE_PATH: "/srv/node_modules",
        CHROME_EXECUTABLE_PATH: process.env.CHROME_EXECUTABLE_PATH,
      },
      timeout: 120_000,
    });

    await ensureBucket();

    const objectName = `slides/${outName}`;
    await minio.fPutObject(MINIO_BUCKET, objectName, tmpOut, {
      "content-type": "video/mp4",
    });

    const presigned = await minio.presignedGetObject(MINIO_BUCKET, objectName, 7 * 24 * 3600);

    try { unlinkSync(tmpOut); } catch (_) {}

    res.json({
      ok: true,
      path: `minio://${MINIO_BUCKET}/${objectName}`,
      url: presigned,
    });
  } catch (err) {
    console.error(err);
    try { unlinkSync(tmpOut); } catch (_) {}
    res.status(500).json({ error: String(err) });
  }
});

// ESM resolution: node_modules must be adjacent to render.mjs in /slides
// Since /slides is a read-only volume, create symlink at /slides/node_modules -> /srv/node_modules
const slidesNodeModules = path.join(SLIDES_DIR, "node_modules");
if (!existsSync(slidesNodeModules)) {
  try {
    symlinkSync("/srv/node_modules", slidesNodeModules, "dir");
    console.log(`Symlinked ${slidesNodeModules} -> /srv/node_modules`);
  } catch (e) {
    console.warn(`Could not symlink node_modules (read-only?): ${e.message}`);
    console.warn("render.mjs may fail to resolve @remotion/* imports");
  }
}

app.listen(PORT, () => {
  console.log(`Renderer listening on :${PORT}`);
});
