#!/usr/bin/env node
// Equipment test: give wearable items, equip them (right click / use), read player equipment.
// usage: node tools/test_equipment.mjs --game <dir>
import fs from "node:fs";
import path from "node:path";
const argv = process.argv.slice(2);
const arg = (n, d) => { const i = argv.indexOf("--" + n); return i >= 0 ? argv[i + 1] : d; };
const game = arg("game");
const outFile = arg("out", "work/run26/port/g29/lab_equipment.json");
const idsFile = arg("ids", "work/run26/port/g29/item_ids.json");
const cfg = JSON.parse(fs.readFileSync(path.join(game, "config", "mcpfabric.config.json"), "utf8"));
const base = "http://" + cfg.host + ":" + cfg.port;
const headers = { "content-type": "application/json", authorization: "Bearer " + cfg.token };
async function call(m, p = {}) { const r = await fetch(base + "/rpc", { method: "POST", headers, body: JSON.stringify({ method: m, params: p }) }); return await r.json(); }
const all = JSON.parse(fs.readFileSync(idsFile, "utf8"));
let ids = [];
for (const [ns, list] of Object.entries(all)) for (const raw of list) { const id = raw.includes(":") ? raw : ns + ":" + raw; if (/(helmet|chestplate|leggings|boots|elytra|jetpack|backpack|goggles|exoskeleton|armor|_cap|_hat)$/i.test(id)) ids.push(id); }
console.log("candidate wearables:", ids.length);
const res = { equipped: [], failed: [] };
for (const id of ids) {
  await call("command.run", { command: "clear @p" });
  const g = await call("command.run", { command: `give @p ${id} 1` });
  if (JSON.stringify(g?.result?.output || []).includes("Unknown item")) { res.failed.push({ id, why: "unknown-item" }); continue; }
  await call("command.run", { command: "gamemode survival" });
  await call("player.useItem", {});
  await new Promise(r => setTimeout(r, 200));
  const eq = await call("player.getEquipment", {});
  const s = JSON.stringify(eq?.result ?? eq?.error ?? {});
  const on = s.includes(id);
  if (on) res.equipped.push(id); else res.failed.push({ id, why: "not-equipped", equipment: s.slice(0, 300) });
}
fs.writeFileSync(outFile, JSON.stringify(res, null, 2));
console.log("equipped=" + res.equipped.length + " failed=" + res.failed.length);
