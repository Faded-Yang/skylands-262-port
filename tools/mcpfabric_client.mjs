#!/usr/bin/env node
// mcpfabric bridge CLI (dev-only harness; not part of the delivered pack)
// Usage:
//   node tools/mcpfabric_client.mjs --game <gameDir> info
//   node tools/mcpfabric_client.mjs --game <gameDir> call ui.widgets
//   node tools/mcpfabric_client.mjs --game <gameDir> call vision.screenshot '{"out":"x.png"}'
//   node tools/mcpfabric_client.mjs --url http://127.0.0.1:25599 --token <t> call player.getState
import fs from "node:fs";
import path from "node:path";

function parseArgs(argv) {
  const out = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) { const k = a.slice(2); const v = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : "true"; out[k] = v; }
    else out._.push(a);
  }
  return out;
}
const args = parseArgs(process.argv.slice(2));
let url = args.url || "http://127.0.0.1:25599";
let token = args.token || "";
if (args.game) {
  const cfgPath = path.join(args.game, "config", "mcpfabric.config.json");
  if (!fs.existsSync(cfgPath)) { console.error("no config: " + cfgPath); process.exit(2); }
  const cfg = JSON.parse(fs.readFileSync(cfgPath, "utf8"));
  url = "http://" + (cfg.host || "127.0.0.1") + ":" + (cfg.port || 25599);
  token = cfg.token || "";
}
const headers = { "content-type": "application/json" };
if (token) headers.authorization = "Bearer " + token;

async function call(method, params = {}) {
  const res = await fetch(url + "/rpc", { method: "POST", headers, body: JSON.stringify({ method, params }) });
  const text = await res.text();
  let body; try { body = JSON.parse(text); } catch { body = { raw: text }; }
  return { status: res.status, body };
}
const cmd = args._[0] || "info";
if (cmd === "info") {
  const res = await fetch(url + "/info", { headers });
  console.log(JSON.stringify({ status: res.status, body: await res.json().catch(() => null) }, null, 2));
} else if (cmd === "call") {
  const method = args._[1];
  if (!method) { console.error("need method"); process.exit(2); }
  let params = {};
  if (args._[2]) params = JSON.parse(args._[2]);
  const r = await call(method, params);
  console.log(JSON.stringify(r.body, null, 2));
  if (r.status !== 200 || r.body?.error) process.exit(1);
} else if (cmd === "shot") {
  const out = args._[1] || "shot.png";
  const r = await call("vision.screenshot", {});
  const data = r.body?.result ?? r.body;
  console.log(JSON.stringify({ status: r.status, keys: data && typeof data === "object" ? Object.keys(data) : typeof data }).slice(0, 800));
  if (process.env.MCPFABRIC_RAW) console.log(JSON.stringify(data).slice(0, 200));
} else { console.error("unknown cmd " + cmd); process.exit(2); }