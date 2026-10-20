#!/usr/bin/env node
// Item registration/name sweep over mcpfabric bridge.
// For each item id: /give, capture localized name from output, /clear. Flags unknown ids and raw-key names.
import fs from "node:fs";
import path from "node:path";
const argv = process.argv.slice(2);
function arg(n, d) { const i = argv.indexOf("--" + n); return i >= 0 ? argv[i + 1] : d; }
const game = arg("game", "work/run26/port/g33/game-mcpfab");
const idsFile = arg("ids", "work/run26/port/g29/item_ids.json");
const nsFilter = arg("ns", "") ? arg("ns", "").split(",") : null;
const outFile = arg("out", "work/run26/port/g29/sweep_items.json");
const cfg = JSON.parse(fs.readFileSync(path.join(game, "config", "mcpfabric.config.json"), "utf8"));
const base = "http://" + (cfg.host || "127.0.0.1") + ":" + (cfg.port || 25599);
const headers = { "content-type": "application/json", authorization: "Bearer " + cfg.token };
async function call(m, p = {}) {
  const res = await fetch(base + "/rpc", { method: "POST", headers, body: JSON.stringify({ method: m, params: p }) });
  return await res.json().catch(() => ({ ok: false }));
}
const all = JSON.parse(fs.readFileSync(idsFile, "utf8"));
let ids = [];
for (const [ns, list] of Object.entries(all)) { if (nsFilter && !nsFilter.includes(ns)) continue; for (const raw of list) ids.push(raw.includes(":") ? raw : ns + ":" + raw); }
const badIds = ids.filter((id) => !id.includes(":"));
if (badIds.length) { console.error("BAD ids (no namespace):", badIds.slice(0, 5)); process.exit(2); }
console.log("items:", ids.length);
const result = { ok: [], unknown: [], rawkey: [], error: [] };
for (let i = 0; i < ids.length; i++) {
  const id = ids[i];
  const r = await call("command.run", { command: `give @p ${id} 1` });
  const out = (r?.result?.output || []).join(" | ");
  if (/Unknown item|unknown item|no such item|Expected/i.test(out)) result.unknown.push(id + " :: " + out.slice(0, 160));
  else if (r?.ok === false) result.error.push(id + " :: " + JSON.stringify(r.error || r).slice(0, 160));
  else {
    // name appears as "[Name]" in "Gave 1 [Name] to Tester"
    const m = out.match(/\[([^\]]+)\]/);
    const name = m ? m[1] : "";
    if (/^item\./.test(name.trim())) result.rawkey.push(id + " :: " + name);
    else result.ok.push(id);
  }
  await call("command.run", { command: "clear @p" });
  if ((i + 1) % 250 === 0) {
    console.log(`progress ${i + 1}/${ids.length} ok=${result.ok.length} unknown=${result.unknown.length} rawkey=${result.rawkey.length}`);
    fs.writeFileSync(outFile, JSON.stringify(result, null, 2));
  }
}
fs.writeFileSync(outFile, JSON.stringify(result, null, 2));
console.log(JSON.stringify({ ok: result.ok.length, unknown: result.unknown.length, rawkey: result.rawkey.length, error: result.error.length }, null, 2));
console.log("unknown:", result.unknown.slice(0, 15));
console.log("rawkey:", result.rawkey.slice(0, 15));