#!/usr/bin/env node
// Systematic block placement sweep over the mcpfabric bridge.
// Detects: unknown/unregistered blocks, placement errors, client crashes, and returns failures list.
// Usage: node tools/sweep_blocks.mjs --game <gameDir> [--ids <block_ids.json>] [--ns create,tfmg] [--limit 50] [--y 120] [--resume 0]
import fs from "node:fs";
import path from "node:path";

const argv = process.argv.slice(2);
function arg(name, def) { const i = argv.indexOf("--" + name); return i >= 0 ? argv[i + 1] : def; }
const game = arg("game", "work/run26/port/g33/game-mcpfab");
const idsFile = arg("ids", "work/run26/port/g29/block_ids.json");
const nsFilter = arg("ns", "") ? arg("ns", "").split(",") : null;
const limit = parseInt(arg("limit", "100000"), 10);
const baseY = parseInt(arg("y", "120"), 10);
const resume = parseInt(arg("resume", "0"), 10);

const cfgPath = path.join(game, "config", "mcpfabric.config.json");
const cfg = JSON.parse(fs.readFileSync(cfgPath, "utf8"));
const base = "http://" + (cfg.host || "127.0.0.1") + ":" + (cfg.port || 25599);
const headers = { "content-type": "application/json" };
if (cfg.token) headers.authorization = "Bearer " + cfg.token;

async function call(method, params = {}) {
  const res = await fetch(base + "/rpc", { method: "POST", headers, body: JSON.stringify({ method, params }) });
  const body = await res.json().catch(() => ({ error: { message: "bad json" } }));
  return body;
}
async function alive() { try { const r = await call("screen.get"); return r?.ok !== false; } catch { return false; } }

const all = JSON.parse(fs.readFileSync(idsFile, "utf8"));
let ids = [];
for (const [ns, list] of Object.entries(all)) {
  if (nsFilter && !nsFilter.includes(ns)) continue;
  for (const id of list) ids.push(id);
}
ids = ids.slice(resume, resume + limit);
console.log("sweep ids:", ids.length, "of", Object.values(all).reduce((a, b) => a + b.length, 0));

const failures = [];
const unknown = [];
let placed = 0;
let x = Math.floor(Math.random() * 2000) - 1000;
let z = Math.floor(Math.random() * 2000) - 1000;
for (let i = 0; i < ids.length; i++) {
  const id = ids[i];
  const px = x + (i % 16);
  const pz = z + Math.floor(i / 16) * 2;
  const r = await call("command.run", { command: `setblock ${px} ${baseY} ${pz} ${id}` });
  const out = JSON.stringify(r?.result ?? r?.error ?? r);
  if (out.includes("Unknown block") || out.includes("unknown block") || out.includes("Expected")) {
    unknown.push(id + " :: " + out.slice(0, 180));
  } else if (r?.ok === false) {
    failures.push(id + " :: " + out.slice(0, 200));
  } else {
    placed++;
  }
  if ((i + 1) % 64 === 0) {
    // clear the row and verify client is alive
    await call("command.run", { command: `fill ${x} ${baseY} ${z - 1} ${x + 16} ${baseY} ${pz + 2} air` }).catch(() => {});
    const ok = await alive();
    process.stdout.write(`progress ${i + 1}/${ids.length} placed=${placed} ok=${ok}\\n`);
    if (!ok) { console.log("CLIENT DIED after: " + id); break; }
  }
  if (placed + failures.length + unknown.length >= limit) break;
}
console.log(JSON.stringify({ placed, failures: failures.length, unknown: unknown.length }, null, 2));
fs.writeFileSync("work/run26/port/g29/sweep_failures.json", JSON.stringify({ failures, unknown }, null, 2));
console.log("sample failures:", failures.slice(0, 10));
console.log("sample unknown:", unknown.slice(0, 10));