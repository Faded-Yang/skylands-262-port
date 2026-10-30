#!/usr/bin/env node
// Broad block interaction sweep: place each block, right-click it (empty hand), record result + state change.
// Log markers "/say LAB:<id>" are emitted so exceptions in latest.log can be attributed to a block.
// usage: node tools/test_blocks_use.mjs --game <dir> [--limit N] [--ids <json>] [--out <json>]
import fs from "node:fs";
import path from "node:path";
const argv = process.argv.slice(2);
const arg = (n, d) => { const i = argv.indexOf("--" + n); return i >= 0 ? argv[i + 1] : d; };
const game = arg("game");
const idsFile = arg("ids", "work/run26/port/g29/block_ids.json");
const outFile = arg("out", "work/run26/port/g29/lab_blocks_use.json");
const limit = parseInt(arg("limit", "100000"), 10);
const cfg = JSON.parse(fs.readFileSync(path.join(game, "config", "mcpfabric.config.json"), "utf8"));
const base = "http://" + cfg.host + ":" + cfg.port;
const headers = { "content-type": "application/json", authorization: "Bearer " + cfg.token };
async function call(m, p = {}) {
  const res = await fetch(base + "/rpc", { method: "POST", headers, body: JSON.stringify({ method: m, params: p }) });
  return await res.json();
}
const all = JSON.parse(fs.readFileSync(idsFile, "utf8"));
let ids = [];
for (const [ns, list] of Object.entries(all)) for (const raw of list) ids.push(raw.includes(":") ? raw : ns + ":" + raw);
ids = ids.slice(0, limit);
console.log("blocks:", ids.length);
// flat test platform high in the sky
const Y = 200, X = 4000, Z = 4000;
await call("command.run", { command: `fill ${X - 2} ${Y - 1} ${Z - 2} ${X + 40} ${Y - 1} ${Z + 40} stone` });
const result = { interactive: [], noninteractive: [], errors: [], changed: [] };
for (let i = 0; i < ids.length; i++) {
  const id = ids[i];
  const px = X + (i % 16), pz = Z + Math.floor(i / 16);
  const st = await call("command.run", { command: `setblock ${px} ${Y} ${pz} ${id}` });
  const blocked = JSON.stringify(st?.result?.output || []);
  if (blocked.includes("Unknown block")) { result.errors.push(id + " :: unknown"); continue; }
  // stand next to it, aim, right-click with empty hand
  await call("command.run", { command: `tp @p ${px + 0.5} ${Y + 1} ${pz + 2.5} 180 30` });
  const use = await call("player.useItem", {});
  const useOk = use?.ok && use.result?.result?.toString().startsWith("Success");
  const after = await call("world.getBlock", { x: px, y: Y, z: pz });
  const afterId = after?.result?.id || "?";
  const changed = afterId !== id;
  const entry = { id, useResult: use?.result?.result ?? use?.error?.message ?? null, afterId, changed };
  if (useOk) result.interactive.push(entry); else result.noninteractive.push(entry);
  if (changed) result.changed.push(entry);
  if (i % 200 === 199) {
    fs.writeFileSync(outFile, JSON.stringify({ total: ids.length, done: i + 1, ...summary(result) }, null, 2));
    console.log(`progress ${i + 1}/${ids.length} interactive=${result.interactive.length} changed=${result.changed.length} errors=${result.errors.length}`);
  }
}
function summary(r) { return { interactive: r.interactive.length, changed: r.changed.length, errors: r.errors.length }; }
fs.writeFileSync(outFile, JSON.stringify({ total: ids.length, done: ids.length, ...result }, null, 2));
console.log("done", JSON.stringify(summary(result)));
