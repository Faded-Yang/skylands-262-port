#!/usr/bin/env node
// Physics assembler interaction test: place assembler + sample blocks around the player,
// hold right-click (control.startUsing), then read block changes + capture logs/screenshot.
import fs from "node:fs";
import path from "node:path";
const argv = process.argv.slice(2);
const arg = (n, d) => { const i = argv.indexOf("--" + n); return i >= 0 ? argv[i + 1] : d; };
const game = arg("game");
const outFile = arg("out", "work/run26/port/g29/lab_assembler.json");
const holdMs = parseInt(arg("hold", "4000"), 10);
const cfg = JSON.parse(fs.readFileSync(path.join(game, "config", "mcpfabric.config.json"), "utf8"));
const base = "http://" + cfg.host + ":" + cfg.port;
const headers = { "content-type": "application/json", authorization: "Bearer " + cfg.token };
const log = (s) => console.log("[asm] " + s);
async function call(m, p = {}) {
  const r = await fetch(base + "/rpc", { method: "POST", headers, body: JSON.stringify({ method: m, params: p }) });
  return await r.json();
}
await call("command.run", { command: "gamemode creative" });
const st = await call("player.getState", {});
const X = Math.floor(st.result.x) + 2, Y = Math.floor(st.result.y), Z = Math.floor(st.result.z) + 2;
log("anchor " + X + "," + Y + "," + Z);
await call("command.run", { command: "fill " + (X - 2) + " " + (Y - 1) + " " + (Z - 2) + " " + (X + 4) + " " + (Y - 1) + " " + (Z + 4) + " stone" });
const placements = [[0, 0, "simulated:physics_assembler"], [1, 0, "create:andesite_casing"], [2, 0, "create:shaft"], [0, 1, "create:cogwheel"], [1, 1, "create:gearbox"]];
for (const [dx, dz, id] of placements) {
  const r = await call("command.run", { command: "setblock " + (X + dx) + " " + Y + " " + (Z + dz) + " " + id });
  log("place " + id + " -> " + JSON.stringify((r.result && r.result.output) || r.error || r).slice(0, 120));
}
await call("command.run", { command: "tp @p " + (X + 0.5) + " " + (Y + 1) + " " + (Z + 3.5) + " 180 35" });
const readAll = async () => {
  const arr = [];
  for (const [dx, dz] of placements.map(p => [p[0], p[1]])) {
    const b = await call("world.getBlock", { x: X + dx, y: Y, z: Z + dz });
    arr.push(b.result ? b.result.id : (b.error ? b.error.code : "?"));
  }
  return arr;
};
await new Promise(r => setTimeout(r, 800));
const before = await readAll();
log("before " + JSON.stringify(before));
await call("control.startUsing", {});
await new Promise(r => setTimeout(r, holdMs));
await call("control.stopUsing", {});
await new Promise(r => setTimeout(r, 1500));
const after = await readAll();
log("after " + JSON.stringify(after));
const state = await call("player.getState", {});
fs.writeFileSync(outFile, JSON.stringify({ x: X, y: Y, z: Z, before, after, player: state.result, note: "grep latest.log for assembler/sublevel/Assemble lines" }, null, 2));
log("written " + outFile);