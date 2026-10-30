#!/usr/bin/env node
// print non-air block count for a region via mcpfabric bridge
// usage: node tools/probe_region.mjs --game <dir> --from x,y,z --to x,y,z
import fs from "node:fs";
import path from "node:path";
const argv = process.argv.slice(2);
const arg = (n, d) => { const i = argv.indexOf("--" + n); return i >= 0 ? argv[i + 1] : d; };
const game = arg("game");
const f = arg("from", "0,0,0").split(",").map(Number);
const t = arg("to", "16,64,16").split(",").map(Number);
const cfg = JSON.parse(fs.readFileSync(path.join(game, "config", "mcpfabric.config.json"), "utf8"));
const base = "http://" + cfg.host + ":" + cfg.port;
const headers = { "content-type": "application/json", authorization: "Bearer " + cfg.token };
async function call(m, p = {}) {
  const res = await fetch(base + "/rpc", { method: "POST", headers, body: JSON.stringify({ method: m, params: p }) });
  return await res.json();
}
const r = await call("world.getBlocks", { from: { x: f[0], y: f[1], z: f[2] }, to: { x: t[0], y: t[1], z: t[2] } });
if (!r.ok) { console.log(JSON.stringify(r)); process.exit(1); }
const res = r.result;
console.log(JSON.stringify({ volume: res.volume, count: res.count, sample: (res.blocks || []).slice(0, 12) }, null, 2));
