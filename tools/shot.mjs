#!/usr/bin/env node
// Capture a screenshot via mcpfabric and save as PNG.
// usage: node tools/shot.mjs --game <dir> --out <path.png>
import fs from "node:fs";
import path from "node:path";
const argv = process.argv.slice(2);
const arg = (n, d) => { const i = argv.indexOf("--" + n); return i >= 0 ? argv[i + 1] : d; };
const game = arg("game");
const out = arg("out", "work/run26/port/g33/lab-shots/shot.png");
const cfg = JSON.parse(fs.readFileSync(path.join(game, "config", "mcpfabric.config.json"), "utf8"));
const base = "http://" + cfg.host + ":" + cfg.port;
const headers = { "content-type": "application/json", authorization: "Bearer " + cfg.token };
const res = await fetch(base + "/rpc", { method: "POST", headers, body: JSON.stringify({ method: "vision.screenshot", params: {} }) });
const j = await res.json();
if (!j.ok) { console.error(JSON.stringify(j)); process.exit(1); }
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, Buffer.from(j.result.base64, "base64"));
console.log("saved " + out + " " + j.result.width + "x" + j.result.height);
