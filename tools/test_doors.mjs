#!/usr/bin/env node
// Door double-half regression: place door (lower+upper), break upper, assert both halves gone.
// usage: node tools/test_doors.mjs --game <dir> [--out <json>]
import fs from "node:fs";
import path from "node:path";
const argv = process.argv.slice(2);
const arg = (n, d) => { const i = argv.indexOf("--" + n); return i >= 0 ? argv[i + 1] : d; };
const game = arg("game");
const outFile = arg("out", "work/run26/port/g29/lab_doors.json");
const idsFile = arg("ids", "work/run26/port/g29/block_ids.json");
const cfg = JSON.parse(fs.readFileSync(path.join(game, "config", "mcpfabric.config.json"), "utf8"));
const base = "http://" + cfg.host + ":" + cfg.port;
const headers = { "content-type": "application/json", authorization: "Bearer " + cfg.token };
async function call(m, p = {}) { const r = await fetch(base + "/rpc", { method: "POST", headers, body: JSON.stringify({ method: m, params: p }) }); return await r.json(); }
const all = JSON.parse(fs.readFileSync(idsFile, "utf8"));
let ids = [];
for (const [ns, list] of Object.entries(all)) for (const raw of list) { const id = raw.includes(":") ? raw : ns + ":" + raw; if (/(_door|_trapdoor|_fence_gate)$/.test(id)) ids.push(id); }
console.log("door-like:", ids.length);
const Y = 210, X = 4100, Z = 4100;
await call("command.run", { command: `fill ${X - 3} ${Y - 1} ${Z - 3} ${X + 30} ${Y - 1} ${Z + 30} stone` });
const res = { tested: [], failures: [] };
for (let i = 0; i < ids.length; i++) {
  const id = ids[i];
  const px = X + (i % 8) * 2, pz = Z + Math.floor(i / 8) * 2;
  const nm = await call("command.run", { command: `setblock ${px} ${Y} ${pz} ${id}` });
  const out = JSON.stringify(nm?.result?.output || []);
  if (out.includes("Unknown block")) { res.failures.push({ id, why: "unknown-block" }); continue; }
  // place explicit lower/upper for double blocks
  await call("command.run", { command: `setblock ${px} ${Y} ${pz} ${id}[half=lower,facing=north,hinge=left,open=false,powered=false]` });
  await call("command.run", { command: `setblock ${px} ${Y + 1} ${pz} ${id}[half=upper,facing=north,hinge=left,open=false,powered=false]` });
  const lowerBefore = await call("world.getBlock", { x: px, y: Y, z: pz });
  const upperBefore = await call("world.getBlock", { x: px, y: Y + 1, z: pz });
  const isDouble = (lowerBefore?.result?.id === id) && (upperBefore?.result?.id === id);
  if (!isDouble) { res.tested.push({ id, double: false, note: "single-block or state rejected" }); continue; }
  await call("command.run", { command: `setblock ${px} ${Y + 1} ${pz} air destroy` });
  await new Promise(r => setTimeout(r, 300));
  const l = await call("world.getBlock", { x: px, y: Y, z: pz });
  const u = await call("world.getBlock", { x: px, y: Y + 1, z: pz });
  const ok = l?.result?.air === true && u?.result?.air === true;
  const row = { id, double: true, lowerAfter: l?.result?.id, upperAfter: u?.result?.id, pass: ok };
  res.tested.push(row);
  if (!ok) res.failures.push({ id, why: "half-left-behind", row });
  if (i % 20 === 19) console.log(`progress ${i + 1}/${ids.length} failures=${res.failures.length}`);
}
fs.writeFileSync(outFile, JSON.stringify(res, null, 2));
console.log("done: tested=" + res.tested.length + " failures=" + res.failures.length);
