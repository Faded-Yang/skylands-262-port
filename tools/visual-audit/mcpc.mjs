#!/usr/bin/env node
// [port-repo] 原路径 scratch/mcpc.mjs（skylands-262 工程目录）；2026-10-30 同步到 tools/visual-audit/。
// 脚本内的绝对工程路径/配套数据不随仓库发布，跑之前按本机路径替换。
// mcpc.mjs -- generic mcpfabric bridge runner (avoids shell quoting).
// usage: node mcpc.mjs <gameDir> <spec.json|method> [outDir]
import fs from "node:fs";
import path from "node:path";

const gameDir = process.argv[2];
const spec = process.argv[3];
const outDir = process.argv[4] || path.join(gameDir, "shots");
fs.mkdirSync(outDir, { recursive: true });
const cfg = JSON.parse(fs.readFileSync(path.join(gameDir, "config", "mcpfabric.config.json"), "utf8"));
const url = "http://" + (cfg.host || "127.0.0.1") + ":" + (cfg.port || 25599);
const headers = { "content-type": "application/json" };
if (cfg.token) headers.authorization = "Bearer " + cfg.token;

let calls;
if (spec.endsWith(".json")) calls = JSON.parse(fs.readFileSync(spec, "utf8"));
else calls = [{ method: spec, params: {} }];

function saveImages(obj, tag, idx) {
  const saved = [];
  const walk = (o, p) => {
    if (o === null || o === undefined) return;
    if (typeof o === "string") {
      if (o.length > 5000 && /^[A-Za-z0-9+/=\r\n]+$/.test(o.slice(0, 200))) {
        const f = path.join(outDir, tag + "-" + idx + "-" + saved.length + ".png");
        fs.writeFileSync(f, Buffer.from(o, "base64"));
        saved.push(f);
      }
      return;
    }
    if (Array.isArray(o)) { o.forEach((v, i) => walk(v, p + "[" + i + "]")); return; }
    if (typeof o === "object") for (const k of Object.keys(o)) walk(o[k], p + "." + k);
  };
  walk(obj, "");
  return saved;
}

const results = [];
for (let i = 0; i < calls.length; i++) {
  const c = calls[i];
  const tag = c.tag || c.method.replace(/\W/g, "_");
  let body, status;
  try {
    const res = await fetch(url + "/rpc", { method: "POST", headers, body: JSON.stringify({ method: c.method, params: c.params || {} }) });
    status = res.status;
    const text = await res.text();
    try { body = JSON.parse(text); } catch { body = { raw: text.slice(0, 400) }; }
  } catch (e) {
    body = { transportError: String(e) }; status = 0;
  }
  const imgs = body ? saveImages(body, tag, i) : [];
  const r = { method: c.method, status, imgs, body };
  results.push(r);
  const brief = JSON.stringify(body);
  console.log("### " + c.method + " status=" + status + (imgs.length ? " images=" + imgs.join(",") : ""));
  console.log(brief.length > (c.full ? 100000 : 2500) ? brief.slice(0, 2500) + " ..." : brief);
  if (c.waitMs) await new Promise(r => setTimeout(r, c.waitMs));
}
